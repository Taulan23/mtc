# pickaxe.py
import os
import math
import random
import pygame
import pymunk
from enums import PickaxeType
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLOCK_SIZE, BORDER_WIDTH,
    BOUNCE_GRAVITY
)


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
PICKAXES_DIR = os.path.join(ASSETS_DIR, "pickaxes")

class ThrowPickaxe(Exception):
    pass

class Pickaxe(pygame.sprite.Sprite):
    """
    Кирка с физикой Pymunk:
    - тело и вращение считаются физикой
    - коллизии/ломание блоков по прежнему через маску (в game.handle_collisions)
    - форма тела собрана из множества маленьких кругов по маске (точная/устойчивая)
    """
    def __init__(self, space: pymunk.Space):
        super().__init__()
        self.space = space

        self.type = PickaxeType.WOOD
        self.size = "small"
        self.active = False

        # "экранные" координаты
        self.x = float(SCREEN_WIDTH // 2)
        self.y = float(SCREEN_HEIGHT // 4)

        # визуальная часть (картинки)
        self.base_image = self._load_image_for_type(self.type)
        self.original_image = self._make_image_for_size()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()

        # маска для коллизий
        self.mask = pygame.mask.from_surface(self.image)

        # параметры «ощущения»
        self.rotation_damping = 0.985
        self._rot_speed_limit = 10.0
        self.rotation_kick = 6.0
        self.friction_factor = 0.992
        self.bounce_stop = 25.0

        # анти-спам-ударов
        self.in_contact = False
        self.contact_block_id = None
        self.last_hit_ts = 0
        self.last_hit_y = self.y
        self.hit_cooldown_ms = 200  # Увеличено с 160 до 200 для предотвращения частых ударов
        self.min_hit_speed = 2.5
        self.min_travel_px_between_hits = 3

        # ---- Pymunk: тело + формы по маске ----
        self.body: pymunk.Body = None
        self.shapes = []
        self._build_physics_body(self.type)   # теперь есть self.original_image → можно строить hitbox

        # синхронизируем rect с physics body
        self._sync_rect_from_state()
        self.active = True

    # ---- загрузка/создание спрайта ----
    def _load_image_for_type(self, pick_type: PickaxeType):
        name = pick_type.name.lower()
        path = os.path.join(PICKAXES_DIR, f"pickaxe_{name}.png")
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception:
                return None
        return None

    def _make_image_for_size(self) -> pygame.Surface:
        w = BLOCK_SIZE if self.size == "small" else int(BLOCK_SIZE * 1.5)
        h = BLOCK_SIZE if self.size == "small" else int(BLOCK_SIZE * 1.5)
        if self.base_image is not None:
            return pygame.transform.smoothscale(self.base_image, (w, h))
        # fallback — прямоугольник
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = self.type.value["color"]
        pygame.draw.rect(surf, color, (0, 0, w, h // 2), border_radius=4)
        pygame.draw.rect(surf, (0, 0, 0, 60), (0, 0, w, h), 1)
        return surf

    # ---- физика Pymunk ----
    def _clear_physics(self):
        if self.body is not None:
            for sh in self.shapes:
                if sh in self.space.shapes:
                    self.space.remove(sh)
            if self.body in self.space.bodies:
                self.space.remove(self.body)
        self.body = None
        self.shapes = []

    def _build_physics_body(self, pick_type: PickaxeType):
        self._clear_physics()
        mass = 2
        w, h = self.image.get_size()
        moment = pymunk.moment_for_box(mass, (w, h))
        self.body = pymunk.Body(mass, moment)
        self.body.position = self.x, self.y
        self.space.add(self.body)

        # Создаем простую прямоугольную форму для кирки
        w, h = self.image.get_size()
        shape = pymunk.Poly.create_box(self.body, (w, h))
        shape.friction = 0.8  # увеличено трение для лучшего контакта
        shape.elasticity = 0.1  # немного увеличено для более естественного отскока
        shape.collision_type = 1
        self.space.add(shape)
        self.shapes.append(shape)

    # ---- публичное API (совместимость) ----
    def activate(self, pick_type: PickaxeType, size: str):
        self.type = pick_type
        self.size = size
        self.base_image = self._load_image_for_type(self.type)
        self.original_image = self._make_image_for_size()
        self.image = self.original_image.copy()
        self._clear_physics()
        self._build_physics_body(self.type)
        self.reset_position()
        self.active = True

    def reset_position(self):
        # Начальная позиция в мировых координатах
        self.x = float(SCREEN_WIDTH // 2)
        self.y = float(SCREEN_HEIGHT // 4)
        if self.body is not None:
            self.body.position = (self.x, self.y)
            self.body.velocity = (0, 0)
            self.body.angular_velocity = 0
        self.image = self.original_image.copy()
        self._sync_rect_from_state()

    def can_hit_now(self):
        now = pygame.time.get_ticks()
        if now - self.last_hit_ts >= self.hit_cooldown_ms:
            self.last_hit_ts = now
            return True
        return False

    def move_left(self):
        if not self.body: return
        vx, vy = self.body.velocity
        self.body.velocity = (vx - 200, vy)

    def move_right(self):
        if not self.body: return
        vx, vy = self.body.velocity
        self.body.velocity = (vx + 200, vy)

    def apply_command(self, command: str):
        cmd = command.lower()
        for pickaxe_type in PickaxeType:
            if cmd == pickaxe_type.value["command"]:
                self.activate(pickaxe_type, self.size)
                return
        if cmd == "!large":
            self.activate(self.type, "large")
        elif cmd == "!small":
            self.activate(self.type, "small")

    def bounce(self, from_side: bool = False):
        if not self.body: return
        vx, vy = self.body.velocity
        if from_side:
            vx = -0.15 * vx
        else:
            vy = -0.15 * vy
        if abs(vx) < self.bounce_stop: vx = 0.0
        if abs(vy) < self.bounce_stop: vy = 0.0
        self.body.velocity = (vx, vy)

    def apply_friction(self):
        if not self.body: return
        vx, vy = self.body.velocity
        vx *= self.friction_factor
        if abs(vx) < self.bounce_stop:
            vx = 0.0
        self.body.velocity = (vx, vy)

    def apply_spin_from_hit(self, dx: float, dy: float):
        if not self.body: return
        if abs(dx) > abs(dy):
            deg = self.rotation_kick * (-1 if dx > 0 else 1)
        else:
            deg = (self.rotation_kick * 0.6) * (-1 if dy > 0 else 1)
        add = math.radians(deg)
        self.body.angular_velocity = max(-2.0, min(2.0, self.body.angular_velocity + add))

    def nudge(self, nx: float, ny: float):
        if not self.body: return
        px, py = self.body.position
        self.body.position = (px + nx, py + ny)

    def update(self, scroll_y: float = 0.0):
        if not self.active or not self.body:
            return

        # Отладка
        # print(f"Pickaxe world pos: {self.body.position}, velocity: {self.body.velocity}")

        self.apply_friction()
        w = self.rect.width
        min_x = BORDER_WIDTH + w // 2
        max_x = SCREEN_WIDTH - BORDER_WIDTH - w // 2
        px, py = self.body.position
        if px < min_x:
            self.body.position = (min_x, py)
            self.bounce(from_side=True)
        elif px > max_x:
            self.body.position = (max_x, py)
            self.bounce(from_side=True)

        # если слишком глубоко вниз – ресет
        # if py > self.scroll_limit_y():
        #     self.reset_position()

        self.body.angular_velocity *= self.rotation_damping
        self.x, self.y = self.body.position
        angle_deg = -math.degrees(self.body.angle)
        self.image = pygame.transform.rotate(self.original_image, angle_deg)
        self._sync_rect_from_state(scroll_y)
        self.mask = pygame.mask.from_surface(self.image)

    def _sync_rect_from_state(self, scroll_y: float = 0.0):
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        bx, by = self.body.position
        # экранная позиция = мировая - смещение камеры
        self.rect.left = int(bx - self.rect.width // 2)
        self.rect.top = int(by - self.rect.height // 2 - scroll_y)

    def scroll_limit_y(self):
        """Нижний предел, при выходе за который кирка ресетится"""
        return SCREEN_HEIGHT + 500  # можно подстроить

    def begin_contact(self, block_id: int):
        self.in_contact = True
        self.contact_block_id = block_id

    def end_contact(self):
        self.in_contact = False
        self.contact_block_id = None

    def get_rect(self) -> pygame.Rect:
        return self.rect