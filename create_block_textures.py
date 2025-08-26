#!/usr/bin/env python3
"""
Создает базовые текстуры для блоков
"""
import pygame
import os
from enums import BlockType

# Инициализируем pygame
pygame.init()

# Цвета для разных типов блоков
block_colors = {
    BlockType.IRON: (210, 210, 210),
    BlockType.COPPER: (184, 115, 51),
    BlockType.GOLD: (255, 215, 0),
    BlockType.COAL: (45, 45, 45),
    BlockType.REDSTONE: (255, 0, 0),
    BlockType.LAPIS: (0, 0, 255),
    BlockType.DIAMOND: (0, 255, 255),
    BlockType.EMERALD: (0, 255, 0),
    BlockType.OBSIDIAN: (25, 0, 45),
    BlockType.COBBLE: (130, 130, 130),
    BlockType.STONE: (100, 100, 100),
    BlockType.STONE2: (110, 110, 110),
    BlockType.STONE3: (90, 90, 90),
}

# Создаем директории для каждого типа блока
for block_type in BlockType:
    block_dir = f"assets/blocks/{block_type.name.lower()}"
    os.makedirs(block_dir, exist_ok=True)

    # Создаем базовую текстуру
    block_surface = pygame.Surface((64, 64))
    color = block_colors.get(block_type, (100, 100, 100))
    block_surface.fill(color)

    # Добавляем простую текстуру (клетки)
    for x in range(0, 64, 8):
        for y in range(0, 64, 8):
            if (x + y) % 16 == 0:
                darker_color = tuple(max(0, c - 20) for c in color)
                pygame.draw.rect(block_surface, darker_color, (x, y, 8, 8))

    pygame.image.save(block_surface, f"{block_dir}/{block_type.name.lower()}.png")

    # Создаем текстуры повреждений (block_100.png, block_80.png, etc.)
    damage_levels = [100, 80, 60, 40, 20, 0]
    for damage in damage_levels:
        damage_surface = block_surface.copy()

        # Добавляем эффекты повреждений
        if damage < 100:
            # Добавляем трещины
            crack_color = (0, 0, 0, 60)
            crack_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
            num_cracks = (100 - damage) // 20 + 1

            for i in range(num_cracks):
                start_x = 8 + i * 10
                start_y = 10 + i * 8
                end_x = 64 - 8 - i * 10
                end_y = 16 + i * 12
                pygame.draw.line(crack_surface, crack_color, (start_x, start_y), (end_x, end_y), 2)

            damage_surface.blit(crack_surface, (0, 0))

        pygame.image.save(damage_surface, f"{block_dir}/block_{damage}.png")

# Создаем общие текстуры повреждений
os.makedirs("assets/blocks", exist_ok=True)
for damage in [100, 80, 60, 40, 20, 0]:
    damage_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    if damage < 100:
        crack_color = (0, 0, 0, 60)
        num_cracks = (100 - damage) // 20 + 1
        for i in range(num_cracks):
            start_x = 8 + i * 10
            start_y = 10 + i * 8
            end_x = 64 - 8 - i * 10
            end_y = 16 + i * 12
            pygame.draw.line(damage_surface, crack_color, (start_x, start_y), (end_x, end_y), 2)

    pygame.image.save(damage_surface, f"assets/blocks/block_{damage}.png")

print("Все текстуры блоков созданы успешно!")
pygame.quit()
