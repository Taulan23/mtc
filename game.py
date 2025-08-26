import pygame
from block_system import BlockSystem
from pickaxe import Pickaxe
from particle_system import ParticleSystem
from settings import *
from enums import PickaxeType, BlockType
import random
import pymunk
import pymunk.pygame_util


class Game:
    def __init__(self, screen):
        self.space = pymunk.Space()
        self.space.gravity = (0, 400)  # еще больше уменьшаем гравитацию для лучшего контакта с блоками
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
        self.background = pygame.image.load("assets/backgrounds/background.png").convert()
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.border_texture = pygame.image.load("assets/blocks/bedrock/bedrock.png").convert_alpha()
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

        # хэндлер столкновений для новой версии Pymunk
        self.space.on_collision(1, 2,
                               begin=self._collision_begin,
                               pre_solve=self._pickaxe_block_collision,
                               separate=self._collision_separate)

        self.draw_options = pymunk.pygame_util.DrawOptions(screen)

    # == управление ==
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.pickaxe.move_left()
            elif event.key == pygame.K_RIGHT:
                self.pickaxe.move_right()
            # Убираем ручное управление движением вниз
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

        # Убираем обработку KEYUP для упрощения

    # == столкновения ==
    def _pickaxe_block_collision(self, arbiter, space, data):
        pick_shape, block_shape = arbiter.shapes
        block = getattr(block_shape, "block_ref", None)
        if not block or not block.pm_body or block.health <= 0:
            return False

        # Убираем принудительную остановку скорости - позволяем физике работать естественно
        # Добавляем небольшой импульс при любом контакте для предотвращения "прилипания"

        # Добавляем небольшой импульс при любом контакте для предотвращения "прилипания"
        contact_impulse_x = random.uniform(-3, 3)
        contact_impulse_y = random.uniform(-2, 5)  # немного вниз
        self.pickaxe.body.apply_impulse_at_local_point((contact_impulse_x, contact_impulse_y), (0, 0))

        # --- урон ---
        if self.pickaxe.can_hit_now():
            destroyed = block.take_damage(self.pickaxe.type.value["speed"])
            if destroyed:
                # При разрушении блока добавляем дополнительный импульс для продолжения движения
                destroy_impulse_x = random.uniform(-15, 15)  # более сильный импульс для движения в стороны
                destroy_impulse_y = random.uniform(10, 40)  # сильный импульс вниз для продолжения падения
                self.pickaxe.body.apply_impulse_at_local_point((destroy_impulse_x, destroy_impulse_y), (0, 0))

                # Обработка ресурсов только при разрушении блока
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

                # Используем позицию физического тела для эффекта частиц
                if block.pm_body is not None:
                    effect_x = block.pm_body.position.x - BLOCK_SIZE // 2
                    effect_y = block.pm_body.position.y - BLOCK_SIZE // 2
                else:
                    effect_x = block.world_x
                    effect_y = block.world_y
                self.particles.add_block_break_effect(
                    effect_x, effect_y, block.type.value["color"]
                )
            else:
                # При простом ударе по блоку - вообще без импульса, чтобы кирка оставалась на месте
                pass

        return True

    def _collision_begin(self, arbiter, space, data):
        """Обработчик начала коллизии"""
        pick_shape, block_shape = arbiter.shapes
        block = getattr(block_shape, "block_ref", None)
        if block:
            print(f"НАЧАЛО КОНТАКТА с блоком {block.id}")  # отладка
            self.pickaxe.begin_contact(block.id)  # исправляем - передаем ID, а не health
        return True

    def _collision_separate(self, arbiter, space, data):
        """Обработчик конца коллизии"""
        pick_shape, block_shape = arbiter.shapes
        block = getattr(block_shape, "block_ref", None)
        if block:
            print(f"КОНЕЦ КОНТАКТА с блоком {block.id}")  # отладка
            self.pickaxe.end_contact()
        return True

    # == обновление ==
    def update(self):
        # шаг физики
        self.space.step(self._physics_dt)

        # обновляем кирку и частицы
        self.particles.update()

        # Плавный скролл камеры - следует за киркой, но с ограничениями
        if self.pickaxe.body is not None:
            pickaxe_y = self.pickaxe.body.position.y

            # Рассчитываем желаемую позицию камеры (кирка в центре экрана)
            target_scroll = pickaxe_y - SCREEN_HEIGHT * 0.5

            # Плавное следование за целью с ограничением скорости
            scroll_speed = 8.0  # скорость следования камеры
            scroll_diff = target_scroll - self.scroll_y
            if abs(scroll_diff) > scroll_speed:
                self.scroll_y += scroll_speed * (1 if scroll_diff > 0 else -1)
            else:
                self.scroll_y = target_scroll

            # Ограничиваем минимальную позицию камеры
            self.scroll_y = max(-100, self.scroll_y)

            # Проверяем, не ушла ли кирка слишком далеко от центра экрана
            screen_pickaxe_y = pickaxe_y - self.scroll_y
            center_offset = abs(screen_pickaxe_y - SCREEN_HEIGHT * 0.5)

            # Если кирка ушла слишком далеко от центра (больше чем на 200 пикселей)
            if center_offset > 200:
                # Плавно возвращаем кирку ближе к центру
                if screen_pickaxe_y < SCREEN_HEIGHT * 0.5 - 100:
                    # Кирка слишком высоко на экране - добавляем импульс вниз
                    self.pickaxe.body.velocity = (self.pickaxe.body.velocity.x, min(self.pickaxe.body.velocity.y + 5, 50))
                elif screen_pickaxe_y > SCREEN_HEIGHT * 0.5 + 100:
                    # Кирка слишком низко на экране - добавляем импульс вверх
                    self.pickaxe.body.velocity = (self.pickaxe.body.velocity.x, max(self.pickaxe.body.velocity.y - 5, -30))

            # Расширенная отладка для анализа проблемы формы
            vx, vy = self.pickaxe.body.velocity
            print(f"Камера: кирка Y={pickaxe_y:.1f}, экран Y={screen_pickaxe_y:.1f}, скорость=({vx:.1f}, {vy:.1f}), скролл={self.scroll_y}, контакт={self.pickaxe.in_contact}")  # отладка

        # дополнительный скролл при необходимости (для совместимости)
        if self.scroll_frames_left > 0:
            remaining = (self.scroll_target - self.scroll_y)
            delta = remaining / self.scroll_frames_left
            self.scroll_y += delta
            self.scroll_frames_left -= 1

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
        # rect.y -= int(self.scroll_y)  # Убираем двойное вычитание scroll_y
        screen.blit(self.pickaxe.image, rect)

        # Индикатор контакта - красный когда касается, зеленый когда нет
        contact_color = (255, 0, 0) if self.pickaxe.in_contact else (0, 255, 0)
        pygame.draw.circle(screen, contact_color, rect.center, 4)

        # Дополнительная линия для лучшей видимости контакта
        if self.pickaxe.in_contact:
            pygame.draw.line(screen, (255, 255, 0), rect.center, (rect.centerx, rect.centery - 10), 2)

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

        # Информация о контакте
        y += 30
        contact_status = "Контакт: ДА" if self.pickaxe.in_contact else "Контакт: НЕТ"
        contact_color = (0, 255, 0) if self.pickaxe.in_contact else (255, 0, 0)
        contact_txt = font.render(contact_status, True, contact_color)
        screen.blit(contact_txt, (10, y))

        # Упрощенная информация об управлении
        y += 30
        control_hint = "← → движение, ПРОБЕЛ активировать"
        hint_color = (200, 200, 200)  # серый
        hint_txt = font.render(control_hint, True, hint_color)
        screen.blit(hint_txt, (10, y))

        # Упрощенная отладочная информация
        y += 30
        if self.pickaxe.body:
            pos_info = f"Позиция: ({int(self.pickaxe.body.position.x)}, {int(self.pickaxe.body.position.y)})"
            pos_txt = font.render(pos_info, True, (255, 255, 0))
            screen.blit(pos_txt, (10, y))

    def _draw_hitboxes(self, screen):
        """Отладочная отрисовка хитбоксов"""
        # Рисуем хитбокс кирки
        if self.pickaxe.body and self.pickaxe.active:
            for shape in self.pickaxe.shapes:
                if isinstance(shape, pymunk.Poly):
                    # Получаем вершины полигона
                    vertices = shape.get_vertices()
                    if len(vertices) >= 3:  # треугольник или больше
                        # Преобразуем мировые координаты в экранные
                        screen_vertices = []
                        for vertex in vertices:
                            world_x, world_y = vertex
                            screen_x = int(world_x)
                            screen_y = int(world_y - self.scroll_y)
                            screen_vertices.append((screen_x, screen_y))

                        # Рисуем красный контур хитбокса
                        if len(screen_vertices) >= 3:
                            pygame.draw.polygon(screen, (255, 0, 0), screen_vertices, 2)
            
            # Рисуем центр физического тела кирки
            center_x = int(self.pickaxe.body.position.x)
            center_y = int(self.pickaxe.body.position.y - self.scroll_y)
            pygame.draw.circle(screen, (0, 255, 0), (center_x, center_y), 3)  # зеленый центр
            
            # Рисуем контур спрайта кирки для сравнения
            pygame.draw.rect(screen, (0, 0, 255), self.pickaxe.rect, 2)  # синий контур спрайта

        # Рисуем хитбоксы блоков
        for block in self.block_system.block_sprites:
            if block.pm_shape and isinstance(block.pm_shape, pymunk.Poly):
                vertices = block.pm_shape.get_vertices()
                if len(vertices) >= 3:
                    screen_vertices = []
                    for vertex in vertices:
                        world_x, world_y = vertex
                        screen_x = int(world_x)
                        screen_y = int(world_y - self.scroll_y)
                        screen_vertices.append((screen_x, screen_y))

                    # Рисуем синий контур для блоков
                    if len(screen_vertices) >= 3:
                        pygame.draw.polygon(screen, (0, 0, 255), screen_vertices, 1)

    def draw(self, screen):
        self._draw_background(screen)
        self._draw_borders(screen, self.border_texture)
        self._draw_blocks(screen)
        self._draw_particles(screen)
        self._draw_pickaxe(screen)
        self._draw_hud(screen)

        # Включаем отладку хитбоксов для диагностики проблемы
        self._draw_hitboxes(screen)  # включи при отладке
        # self.space.debug_draw(self.draw_options)  # pymunk отладка
        
