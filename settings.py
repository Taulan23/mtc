# settings.py
import os

# --- Экран и поле ---
BLOCK_SIZE = 64
BORDER_WIDTH = 32
GRID_COLS = 7
GRID_VISIBLE_ROWS = 13

SCREEN_WIDTH = GRID_COLS * BLOCK_SIZE + 2 * BORDER_WIDTH
SCREEN_HEIGHT = GRID_VISIBLE_ROWS * BLOCK_SIZE

# --- Генерация/скролл ---
INITIAL_SPAWN_ROWS = 40
INITIAL_OFFSET = 5 * BLOCK_SIZE
SCROLL_THRESHOLD_HEIGHT = INITIAL_OFFSET + BLOCK_SIZE
SCROLL_SMOOTH_FRAMES = 10

# --- Физика кирки ---
BOUNCE_STRENGTH = -3
BOUNCE_GRAVITY = 0.5
BOUNCE_MAX_COUNT = 1
BOUNCE_REDUCE_FACTOR = 0.3
BOUNCE_SIDE_IMPULSE = 10

# Визуал кирки: ротация
PICKAXE_ROTATE_FROM_VY = 8.0   # чем больше — тем сильнее влияет вертикальная скорость на угол
PICKAXE_TILT_FROM_VX = 2.2     # влияет горизонтальная скорость
PICKAXE_MAX_ANGLE = 35         # ограничение на итоговый угол в градусах
MAX_PICKAXE_SPEED = 1000
# --- HP блоков ---
BLOCK_HP_PER_HARDNESS = 5
BLOCK_HP_THRESHOLDS = [100, 80, 60, 40, 20, 0]

# --- Пути к ассетам (необязательны) ---
# Папки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # где лежит settings.py
ASSETS_ROOT = os.path.join(BASE_DIR, "assets")
PICKAXES_DIR = os.path.join(ASSETS_ROOT, "pickaxes")
BLOCKS_DIR = os.path.join(ASSETS_ROOT, "blocks")

# Имена файлов для кирок — можно не создавать, будет фоллбэк
PICKAXE_IMAGE_FILES = {
    "WOOD":      "pickaxe_wood.png",
    "STONE":     "pickaxe_stone.png",
    "IRON":      "pickaxe_iron.png",
    "GOLD":      "pickaxe_gold.png",
    "DIAMOND":   "pickaxe_diamond.png",
    "NETHERITE": "pickaxe_netherite.png",
}


RESOURCE_ICONS = {
    "coal": "assets/ui/coal.png",
    "iron": "assets/ui/iron.png",
    "copper": "assets/ui/copper.png",
    "gold": "assets/ui/gold.png",
    "diamond": "assets/ui/diamond.png",
    "emerald": "assets/ui/emerald.png",
    "lapis": "assets/ui/lapis.png",
    "redstone": "assets/ui/redstone.png",
}