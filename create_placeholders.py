#!/usr/bin/env python3
"""
Создает placeholder изображения для игры
"""
import pygame
import os

# Инициализируем pygame для создания изображений
pygame.init()

# Создаем фон (темно-синий градиент)
background = pygame.Surface((800, 600))
for y in range(600):
    color = (20, 20, 40 + int(y * 0.1))
    pygame.draw.line(background, color, (0, y), (800, y))
pygame.image.save(background, "assets/backgrounds/background.png")

# Создаем текстуру bedrock (темно-серый камень)
bedrock = pygame.Surface((64, 64))
bedrock.fill((40, 40, 40))
# Добавляем простую текстуру
for x in range(0, 64, 8):
    for y in range(0, 64, 8):
        if (x + y) % 16 == 0:
            pygame.draw.rect(bedrock, (60, 60, 60), (x, y, 8, 8))
pygame.image.save(bedrock, "assets/blocks/bedrock/bedrock.png")

# Цвета для иконок ресурсов
resource_colors = {
    "coal": (45, 45, 45),
    "iron": (210, 210, 210),
    "copper": (184, 115, 51),
    "gold": (255, 215, 0),
    "diamond": (0, 255, 255),
    "emerald": (0, 255, 0),
    "lapis": (0, 0, 255),
    "redstone": (255, 0, 0),
}

# Создаем иконки ресурсов
for resource, color in resource_colors.items():
    icon = pygame.Surface((32, 32))
    icon.fill(color)
    # Добавляем рамку
    pygame.draw.rect(icon, (255, 255, 255), (0, 0, 32, 32), 2)
    pygame.image.save(icon, f"assets/ui/{resource}.png")

print("Placeholder изображения созданы успешно!")
pygame.quit()
