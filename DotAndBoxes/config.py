# config.py
import pygame

# ─── CỬA SỔ ───────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 900
WINDOW_HEIGHT = 700
FPS           = 60
TITLE         = "Dots & Boxes"

# ─── BÀN CỜ ───────────────────────────────────────────────────────────────────
BOARD_CONFIGS = {
    "5x4": {"cols": 5, "rows": 4},   # 5 cột dot, 4 hàng dot → 4×3 ô
    "8x6": {"cols": 8, "rows": 6},   # 8 cột dot, 6 hàng dot → 7×5 ô
}

CELL_SIZE   = 90   # khoảng cách giữa 2 dot (px)
DOT_RADIUS  = 7
LINE_WIDTH  = 5
LINE_HOVER_WIDTH = 6

# ─── ĐỘ KHÓ ───────────────────────────────────────────────────────────────────
DIFFICULTY_DEPTH = {
    "Easy": {"5x4": 3, "8x6": 2},
    "Hard": {"5x4": 7, "8x6": 5},
}

# ─── MÀU SẮC ──────────────────────────────────────────────────────────────────
# Palette: nền tối đậm, accent neon cyan & coral
C_BG          = (13,  17,  23)    # nền chính
C_SURFACE     = (22,  30,  41)    # card / panel
C_SURFACE2    = (30,  42,  58)    # hover nhẹ
C_BORDER      = (45,  65,  90)    # viền
C_DOT         = (200, 220, 240)   # chấm bình thường
C_DOT_HOVER   = (100, 220, 255)   # chấm hover
C_LINE_DEFAULT= (45,  65,  90)    # đường chưa kẻ
C_LINE_HOVER  = (100, 220, 255)   # đường đang hover
C_LINE_P1     = (80,  200, 255)   # đường của người chơi 1 (cyan)
C_LINE_P2     = (255, 100, 120)   # đường của người chơi 2 / AI (coral)
C_BOX_P1      = (80,  200, 255, 60)   # tô ô P1
C_BOX_P2      = (255, 100, 120, 60)   # tô ô P2
C_TEXT        = (210, 225, 240)   # text thường
C_TEXT_DIM    = (90,  115, 145)   # text mờ
C_ACCENT      = (100, 220, 255)   # neon cyan
C_ACCENT2     = (255, 100, 120)   # coral
C_WHITE       = (255, 255, 255)
C_BLACK       = (0,   0,   0)
C_SUCCESS     = (80,  220, 150)   # xanh lá
C_WARNING     = (255, 200,  60)   # vàng

# ─── FILE LƯU GAME ────────────────────────────────────────────────────────────
SAVE_FILE = "saves/savegame.json"

# ─── FONT (pygame sẽ dùng font hệ thống) ─────────────────────────────────────
FONT_TITLE_SIZE  = 72
FONT_LARGE_SIZE  = 38
FONT_MEDIUM_SIZE = 26
FONT_SMALL_SIZE  = 18
