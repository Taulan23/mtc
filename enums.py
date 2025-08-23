from enum import Enum

class PickaxeType(Enum):
    WOOD = {"color": (139, 69, 19), "speed": 1, "command": "!wood"}
    STONE = {"color": (100, 100, 100), "speed": 2, "command": "!stone"}
    IRON = {"color": (210, 210, 210), "speed": 3, "command": "!iron"}
    GOLD = {"color": (255, 215, 0), "speed": 6, "command": "!gold"}
    DIAMOND = {"color": (0, 255, 255), "speed": 5, "command": "!diamond"}
    NETHERITE = {"color": (70, 0, 50), "speed": 9, "command": "!netherite"}

class BlockType(Enum):
    IRON = {"color": (210, 210, 210), "hardness": 3, "spawn_chance": 0.08}
    COPPER = {"color": (184, 115, 51), "hardness": 2, "spawn_chance": 0.07}
    GOLD = {"color": (255, 215, 0), "hardness": 2, "spawn_chance": 0.03}
    COAL = {"color": (45, 45, 45), "hardness": 1, "spawn_chance": 0.1}
    REDSTONE = {"color": (255, 0, 0), "hardness": 2, "spawn_chance": 0.05}
    LAPIS = {"color": (0, 0, 255), "hardness": 3, "spawn_chance": 0.02}
    DIAMOND = {"color": (0, 255, 255), "hardness": 4, "spawn_chance": 0.008}
    EMERALD = {"color": (0, 255, 0), "hardness": 4, "spawn_chance": 0.003}
    OBSIDIAN = {"color": (25, 0, 45), "hardness": 18, "spawn_chance": 0.03}
    COBBLE = {"color": (130, 130, 130), "hardness": 2, "spawn_chance": 0.1}
    STONE = {"color": (100, 100, 100), "hardness": 2, "spawn_chance": 0.45}
    STONE2 = {"color": (110, 110, 110), "hardness": 2, "spawn_chance": 0.15}
    STONE3 = {"color": (90, 90, 90), "hardness": 2, "spawn_chance": 0.15}