import os
import random
import pygame
import pymunk
import logging
from typing import Dict, Optional
from mitc.enums import BlockType
from mitc.settings import (
    BLOCK_SIZE, BORDER_WIDTH, SCREEN_HEIGHT, GRID_COLS,
    INITIAL_SPAWN_ROWS, INITIAL_OFFSET, BLOCK_HP_PER_HARDNESS,
    BLOCK_HP_THRESHOLDS, BLOCKS_DIR
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _safe_load(path: str, size=(BLOCK_SIZE, BLOCK_SIZE)) -> Optional[pygame.Surface]:
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        logger.warning(f"Failed to load image at {path}")
        return None


def _try_load_block_images_for_type(bt: BlockType) -> Dict[str, Optional[pygame.Surface]]:
    """
    Загружает базовую текстуру (<typename>.png) и текстуры повреждений (block_<thr>.png).
    Возвращает словарь с ключами 'base' и числовыми порогами здоровья (100, 80, ...).
    Если текстура не найдена, возвращается None для соответствующего ключа.
    """
    images: Dict[str, Optional[pygame.Surface]] = {"base": None}
    folder_type = os.path.join(BLOCKS_DIR, bt.name.lower())

    # Загружаем базовую текстуру (<typename>.png)
    base_path = os.path.join(folder_type, f"{bt.name.lower()}.png")
    images["base"] = _safe_load(base_path)

    # Загружаем текстуры повреждений
    have_any_damage = False
    for thr in BLOCK_HP_THRESHOLDS:
        type_path = os.path.join(folder_type, f"block_{thr}.png")
        surf = _safe_load(type_path)
        if not surf:
            # Пробуем общую текстуру
            common_path = os.path.join(BLOCKS_DIR, f"block_{thr}.png")
            surf = _safe_load(common_path)
        if surf:
            images[thr] = surf
            have_any_damage = True

    # Если есть базовая текстура или текстуры повреждений, возвращаем словарь
    if images["base"] or have_any_damage:
        return images
    return {"base": None}


class Block(pygame.sprite.Sprite):
    """Спрайт блока с HP и сменой спрайта по порогам HP."""
    def __init__(self, world_x: int, world_y: int, btype: BlockType,
                 images_by_thr: Dict[str, Optional[pygame.Surface]],
                 pm_space: Optional[pymunk.Space] = None):
        super().__init__()
        self.type = btype
        self.color = btype.value["color"]
        self.max_health = max(1, btype.value["hardness"] * BLOCK_HP_PER_HARDNESS)
        self.health = self.max_health
        self.world_x = world_x
        self.world_y = world_y
        self.images_by_thr = images_by_thr

        self.image = self._surface_for_health()
        self.rect = self.image.get_rect(topleft=(world_x, world_y))
        self.mask = pygame.mask.from_surface(self.image)

        self.pm_space = pm_space
        self.pm_body: Optional[pymunk.Body] = None
        self.pm_shape: Optional[pymunk.Shape] = None

        if self.pm_space is not None:
            self.pm_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            self.pm_body.position = (self.rect.centerx, self.rect.centery)

            self.pm_shape = pymunk.Poly.create_box(self.pm_body, (BLOCK_SIZE, BLOCK_SIZE))
            self.pm_shape.elasticity = 0.0
            self.pm_shape.friction = 0.95
            self.pm_shape.filter = pymunk.ShapeFilter(group=2)  # блоки не сталкиваются между собой
            self.pm_shape.block_ref = self
            self.pm_shape.collision_type = 2
            self.pm_space.add(self.pm_body, self.pm_shape)

    # ======= Вспомогательные =======

    def _percent(self) -> float:
        return (self.health / self.max_health) * 100.0

    def _pick_thr(self) -> int:
        p = self._percent()
        for thr in sorted(BLOCK_HP_THRESHOLDS, reverse=True):
            if p >= thr:
                return thr
        return min(BLOCK_HP_THRESHOLDS)

    def _surface_for_health(self) -> pygame.Surface:
        thr = self._pick_thr()
        s = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)

        # База
        if self.images_by_thr.get("base"):
            s.blit(self.images_by_thr["base"], (0, 0))
        else:
            pygame.draw.rect(s, self.color, (0, 0, BLOCK_SIZE, BLOCK_SIZE))

        # Повреждения
        if thr < 100:
            if self.images_by_thr.get(thr):
                s.blit(self.images_by_thr[thr], (0, 0))
            else:
                # fallback — трещины
                dmg = int((100 - self._percent()) // 20)
                crack = (0, 0, 0, 60)
                for i in range(dmg):
                    pygame.draw.line(s, crack, (8, 10 + i*10), (BLOCK_SIZE-8, 16 + i*12), 2)

        return s

    # ======= Жизненный цикл =======

    def take_damage(self, amount: int) -> bool:
        self.health -= max(1, amount)

        if self.health <= 0:
            self.kill()
            return True

        self.image = self._surface_for_health()
        self.mask = pygame.mask.from_surface(self.image)
        return False

    def kill(self) -> None:
        if self.pm_space and self.pm_body and self.pm_shape:
            self.pm_space.remove(self.pm_body, self.pm_shape)
            self.pm_body = None
            self.pm_shape = None
        super().kill()

    def sync_screen_pos(self, scroll_y: float):
        """
        Пересчитывает экранные координаты на основе world_y и текущего смещения камеры.
        """
        self.rect.x = self.world_x
        self.rect.y = int(self.world_y - scroll_y)
        if self.pm_body is not None:
            self.pm_body.position = (self.rect.centerx, self.rect.centery)


class BlockSystem:
    """Генерация и скролл блоков на базе спрайтов."""
    def __init__(self, pm_space: Optional[pymunk.Space] = None):
        self.pm_space = pm_space
        self.scroll_y = 0.0
        self.block_sprites = pygame.sprite.Group()

        # Картинки по типам
        self.type_to_images: Dict[BlockType, Dict[str, Optional[pygame.Surface]]] = {
            bt: _try_load_block_images_for_type(bt) for bt in BlockType
        }

        self._generate_initial_rows()
        logger.info("BlockSystem: initialized")

    # ======= Генерация =======

    def _random_block_type(self) -> BlockType:
        types = [bt for bt in BlockType]
        weights = [bt.value["spawn_chance"] for bt in BlockType]
        total = sum(weights) or 1.0
        return random.choices(types, weights=weights, k=1)[0]

    def _generate_row(self, world_y: int):
        for col in range(GRID_COLS):
            world_x = col * BLOCK_SIZE + BORDER_WIDTH
            bt = self._random_block_type()
            images = self.type_to_images.get(bt)
            b = Block(world_x, world_y, bt, images, pm_space=self.pm_space)
            b.sync_screen_pos(self.scroll_y)
            self.block_sprites.add(b)

    def _generate_initial_rows(self):
        for i in range(INITIAL_SPAWN_ROWS):
            self._generate_row(INITIAL_OFFSET + i * BLOCK_SIZE)

    # ======= Обновление =======

    def _remove_offscreen(self):
        for b in list(self.block_sprites):
            if b.rect.top > SCREEN_HEIGHT + BLOCK_SIZE:
                b.kill()

    def _generate_new_if_needed(self):
        if not self.block_sprites:
            self._generate_row(self.scroll_y + INITIAL_OFFSET)
            return
        last_y = max((b.world_y for b in self.block_sprites), default=self.scroll_y + INITIAL_OFFSET)
        if (last_y - self.scroll_y) < SCREEN_HEIGHT:
            self._generate_row(last_y + BLOCK_SIZE)

    def scroll(self, amount: float):
        self.scroll_y += amount
        for b in self.block_sprites:
            b.sync_screen_pos(self.scroll_y)

    def update(self, scroll_y):
        self.scroll_y = scroll_y
        
        # синхронизация экранных координат всех блоков
        for b in self.block_sprites:
            b.sync_screen_pos(scroll_y)
        
        # проверяем, нужно ли добавить новые строки
        self._generate_new_if_needed()
    
    def draw(self, surface: pygame.Surface):
        self.block_sprites.draw(surface)
    # ======= Чат-команды =======

    def apply_chat_command(self, command: str):
        if command.lower() == "!spawn diamond":
            for b in self.block_sprites:
                if random.random() < 0.1:
                    b.type = BlockType.DIAMOND
                    b.color = b.type.value["color"]
                    b.max_health = max(1, b.type.value["hardness"] * BLOCK_HP_PER_HARDNESS)
                    b.health = b.max_health
                    b.images_by_thr = self.type_to_images.get(BlockType.DIAMOND)
                    b.image = b._surface_for_health()
