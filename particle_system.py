import random
import pygame
from settings import BLOCK_SIZE

class ParticleSystem:
    def __init__(self, particle_count=15, particle_life=30):
        self.particles = []
        self.particle_count = particle_count
        self.particle_life = particle_life

    def add_block_break_effect(self, x, y, color):
        for _ in range(self.particle_count):
            self.particles.append({
                'x': x + random.randint(0, BLOCK_SIZE),
                'y': y + random.randint(0, BLOCK_SIZE),
                'color': color,
                'speed_x': random.uniform(-3, 3),
                'speed_y': random.uniform(-5, -2),
                'life': self.particle_life
            })

    def update(self):
        self.particles = [p for p in self.particles if p['life'] > 0]
        for p in self.particles:
            p['x'] += p['speed_x']
            p['y'] += p['speed_y']
            p['life'] -= 1
