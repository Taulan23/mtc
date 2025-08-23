import pygame
from mitc.block_system import BlockSystem
from mitc.pickaxe import Pickaxe
from mitc.particle_system import ParticleSystem
from mitc.settings import *
from mitc.enums import PickaxeType, BlockType
import random
import pymunk
import pymunk.pygame_util


class Game:
    def __init__(self, screen):
        self.space = pymunk.Space()
        self.space.gravity = (0, 1500)
        self._physics_dt = 1.0 / 60.0

        # системы
        self.block_system = BlockSystem(pm_space=self.space)
        self.pickaxe = Pickaxe(self.space)
        self.particles = ParticleSystem()

        # скролл (камера)
        self.scroll_y = 0.0
        self.scroll_target = 0.0
        self.scroll_frames_left = 0

        # фон
        self.background = pygame.image.load("evn/mitc/assets/backgrounds/background.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.border_texture = pygame.image.load("evn/mitc/assets/blocks/bedrock/bedrock.png").convert_alpha()
        self.border_texture = pygame.transform.scale(self.border_texture, (BLOCK_SIZE, BLOCK_SIZE))

        # ресурсы
        self.resources = {
            "coal": 0,
            "iron": 0,
            "copper": 0,
            "gold": 0,
            "diamond": 0,
            "emerald": 0,
            "lapis": 0,
            "redstone": 0,
        }
        self.resource_icons = {}
        for name, path in RESOURCE_ICONS.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                self.resource_icons[name] = pygame.transform.smoothscale(img, (32, 32))
            except Exception:
                self.resource_icons[name] = None

        # хэндлер столкновений
        handler = self.space.add_collision_handler(1, 2)  # 1 = кирка, 2 = блок
        handler.pre_solve = self._pickaxe_block_collision

        self.draw_options = pymunk.pygame_util.DrawOptions(screen)

    # == управление ==
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.pickaxe.move_left()
            elif event.key == pygame.K_RIGHT:
                self.pickaxe.move_right()
            elif event.key == pygame.K_SPACE:
                if not self.pickaxe.active:
                    self.pickaxe.activate(self.pickaxe.type, self.pickaxe.size)
            elif event.key == pygame.K_1:
                self.pickaxe.apply_command("!wood")
            elif event.key == pygame.K_2:
                self.pickaxe.apply_command("!stone")
            elif event.key == pygame.K_3:
                self.pickaxe.apply_command("!iron")
            elif event.key == pygame.K_4:
                self.pickaxe.apply_command("!gold")
            elif event.key == pygame.K_5:
                self.pickaxe.apply_command("!diamond")
            elif event.key == pygame.K_6:
                self.pickaxe.apply_command("!netherite")
            elif event.key == pygame.K_l:
                self.pickaxe.apply_command("!large")
            elif event.key == pygame.K_s:
                self.pickaxe.apply_command("!small")
            elif event.key == pygame.K_d:
                self.block_system.apply_chat_command("!spawn diamond")

    # == столкновения ==
    def _pickaxe_block_collision(self, arbiter, space, data):
        pick_shape, block_shape = arbiter.shapes
        block = getattr(block_shape, "block_ref", None)
        if not block or not block.pm_body or block.health <= 0:
            return False

        # отражение импульса
        dx = self.pickaxe.body.position.x - block.pm_body.position.x
        dy = self.pickaxe.body.position.y - block.pm_body.position.y
        n = pymunk.Vec2d(dx, dy).normalized()

        v = self.pickaxe.body.velocity
        vn = v.dot(n) * n
        vt = v - vn
        restitution = 0.2
        new_v = vt - vn * restitution
        self.pickaxe.body.velocity = new_v

        torque = n.cross(v) * 0.001
        self.pickaxe.body.angular_velocity += torque

        # --- урон ---
        if self.pickaxe.can_hit_now():
            destroyed = block.take_damage(self.pickaxe.type.value["speed"])
            if destroyed:
                resmap = {
                    BlockType.COAL: "coal",
                    BlockType.IRON: "iron",
                    BlockType.COPPER: "copper",
                    BlockType.GOLD: "gold",
                    BlockType.DIAMOND: "diamond",
                    BlockType.EMERALD: "emerald",
                }
                if block.type in resmap:
                    self.resources[resmap[block.type]] += 1
                elif block.type == BlockType.LAPIS:
                    self.resources["lapis"] += random.randint(1, 5)
                elif block.type == BlockType.REDSTONE:
                    self.resources["redstone"] += random.randint(1, 5)

                self.particles.add_block_break_effect(
                    block.world_x, block.world_y, block.type.value["color"]
                )

        return True

    # == обновление ==
    def update(self):
        # шаг физики
        self.space.step(self._physics_dt)

        # обновляем кирку и частицы
        
        self.particles.update()
        target_scroll = max(0, self.pickaxe.body.position.y - SCREEN_HEIGHT // 4)
        if target_scroll > self.scroll_y:
            self.scroll_y += (target_scroll - self.scroll_y) * 0.15  # плавное догоняние
        self.scroll_y = max(0, self.scroll_y)
        # плавный скролл камеры
        if self.scroll_frames_left > 0:
            remaining = (self.scroll_target - self.scroll_y)
            delta = remaining / self.scroll_frames_left
            self.scroll_y += delta
            self.scroll_frames_left -= 1

        # если кирка ушла ниже экрана → скроллим камеру
        if self.pickaxe.active and self.pickaxe.body.position.y > (INITIAL_OFFSET + BLOCK_SIZE):
            self.scroll_target = self.scroll_y + BLOCK_SIZE
            self.scroll_frames_left = SCROLL_SMOOTH_FRAMES
        
        self.pickaxe.update(self.scroll_y)
        # обновляем блоки (только экранные позиции!)
        self.block_system.update(self.scroll_y)

    # == отрисовка ==
    def _draw_background(self, screen):
        screen.blit(self.background, (0, 0))
        pygame.draw.rect(screen, (50, 50, 60), (0, 0, BORDER_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(screen, (50, 50, 60), (SCREEN_WIDTH - BORDER_WIDTH, 0, BORDER_WIDTH, SCREEN_HEIGHT))

    def _draw_blocks(self, screen):
        self.block_system.draw(screen)

        # HP над блоками
        font = pygame.font.SysFont(None, 18)
        for b in self.block_system.block_sprites:
            if b.health <= 0:
                continue
            hp_text = font.render(str(b.health), True, (255, 255, 255))
            shadow = font.render(str(b.health), True, (0, 0, 0))
            tx = b.rect.centerx - hp_text.get_width() // 2
            ty = b.rect.centery
            screen.blit(shadow, (tx + 1, ty + 1))
            screen.blit(hp_text, (tx, ty))

    def _draw_borders(self, surface: pygame.Surface, texture: pygame.Surface):
        # Левый бордер
        for y in range(0, SCREEN_HEIGHT, texture.get_height()):
            surface.blit(texture, (0, y), area=pygame.Rect(0, 0, BORDER_WIDTH, texture.get_height()))

        # Правый бордер
        x_right = SCREEN_WIDTH - BORDER_WIDTH
        for y in range(0, SCREEN_HEIGHT, texture.get_height()):
            surface.blit(texture, (x_right, y),
                         area=pygame.Rect(texture.get_width() - BORDER_WIDTH, 0, BORDER_WIDTH, texture.get_height()))

    def _draw_particles(self, screen):
        for p in self.particles.particles:
            alpha = min(255, p['life'] * 8)
            color = (*p['color'], alpha)
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (2, 2), 2)
            screen.blit(surf, (p['x'], p['y'] - self.scroll_y))

    def _draw_pickaxe(self, screen):
        rect = self.pickaxe.get_rect()
        rect.y -= int(self.scroll_y)
        screen.blit(self.pickaxe.image, rect)
        pygame.draw.circle(screen, (255, 0, 0), rect.center, 4)

    def _draw_hud(self, screen):
        font = pygame.font.SysFont("Arial", 24)
        y = 10
        for name, value in self.resources.items():
            icon = self.resource_icons.get(name)
            if icon:
                screen.blit(icon, (10, y))
            txt = font.render(str(value), True, (255, 255, 255))
            screen.blit(txt, (50, y + 4))
            y += 36

        depth = -(int(self.pickaxe.body.position.y // BLOCK_SIZE))
        depth_txt = font.render(f"Y: {depth}", True, (255, 255, 0))
        screen.blit(depth_txt, (10, y))

    def draw(self, screen):
        self._draw_background(screen)
        self._draw_borders(screen, self.border_texture)
        self._draw_blocks(screen)
        self._draw_particles(screen)
        self._draw_pickaxe(screen)
        self._draw_hud(screen)

        #self._draw_hitboxes(screen)  # включи при отладке
        #self.space.debug_draw(self.draw_options)  # pymunk отладка
        
