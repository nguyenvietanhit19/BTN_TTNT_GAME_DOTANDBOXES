# ui/screens.py
"""
Quản lý tất cả 5 màn hình giao diện.
Mỗi Screen có phương thức:
  handle_event(event) -> next_screen_name hoặc None
  update(dt)
  draw(surface)
"""
import copy
import math
import threading
import pygame

from config import *
from game_manager import GameManager
from ai.minimax   import choose_move


# ══════════════════════════════════════════════════════════════════════════════
# Tiện ích vẽ
# ══════════════════════════════════════════════════════════════════════════════

def _font(size):
    return pygame.font.SysFont("segoeui", size, bold=False)

def _font_bold(size):
    return pygame.font.SysFont("segoeui", size, bold=True)

def draw_text_center(surf, text, font, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))

def draw_rect_alpha(surf, color_rgba, rect, radius=12):
    """Vẽ hình chữ nhật có alpha."""
    tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(tmp, color_rgba, (0, 0, rect[2], rect[3]), border_radius=radius)
    surf.blit(tmp, (rect[0], rect[1]))


# ══════════════════════════════════════════════════════════════════════════════
# Lớp Button tái sử dụng
# ══════════════════════════════════════════════════════════════════════════════

class Button:
    def __init__(self, x, y, w, h, text,
                 color=None, hover_color=None,
                 text_color=None, font_size=None,
                 radius=12, border_color=None):
        self.rect         = pygame.Rect(x, y, w, h)
        self.text         = text
        self.color        = color        or C_SURFACE2
        self.hover_color  = hover_color  or C_ACCENT
        self.text_color   = text_color   or C_TEXT
        self.font_size    = font_size    or FONT_MEDIUM_SIZE
        self.radius       = radius
        self.border_color = border_color or C_BORDER
        self.hovered      = False
        self._font        = _font_bold(self.font_size)

    def handle_event(self, event) -> bool:
        """Trả về True nếu được click."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surf):
        bg = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surf, bg,              self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, self.border_color, self.rect, 2, border_radius=self.radius)
        text_col = C_BG if self.hovered else self.text_color
        draw_text_center(surf, self.text, self._font, text_col,
                         self.rect.centerx, self.rect.centery)


class ToggleButton(Button):
    """Nút bật/tắt (selected state)."""
    def __init__(self, *args, selected=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected = selected

    def draw(self, surf):
        bg = self.hover_color if (self.hovered or self.selected) else self.color
        pygame.draw.rect(surf, bg,              self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, self.border_color, self.rect, 2, border_radius=self.radius)
        text_col = C_BG if (self.hovered or self.selected) else self.text_color
        draw_text_center(surf, self.text, self._font, text_col,
                         self.rect.centerx, self.rect.centery)


# ══════════════════════════════════════════════════════════════════════════════
# Màn hình 1 — Splash (Tên game + nút Play)
# ══════════════════════════════════════════════════════════════════════════════

class SplashScreen:
    NAME = "splash"

    def __init__(self, gm: GameManager):
        self.gm   = gm
        self.tick = 0.0
        self._btn = Button(
            WINDOW_WIDTH//2 - 120, WINDOW_HEIGHT//2 + 60,
            240, 60, "PLAY",
            color=C_SURFACE2, hover_color=C_ACCENT,
            font_size=FONT_LARGE_SIZE, radius=30
        )
        # Particles
        self._particles = [
            {
                "x": __import__("random").randint(0, WINDOW_WIDTH),
                "y": __import__("random").uniform(0, WINDOW_HEIGHT),
                "vy": __import__("random").uniform(0.2, 0.8),
                "r":  __import__("random").randint(1, 3),
                "a":  __import__("random").randint(30, 120),
            }
            for _ in range(60)
        ]
        self._f_title  = _font_bold(FONT_TITLE_SIZE)
        self._f_sub    = _font(FONT_SMALL_SIZE)

    def handle_event(self, event):
        if self._btn.handle_event(event):
            return "continue_or_new" if self.gm.has_save() else "menu"
        return None

    def update(self, dt):
        self.tick += dt
        for p in self._particles:
            p["y"] -= p["vy"]
            if p["y"] < 0:
                p["y"] = WINDOW_HEIGHT
                p["x"] = __import__("random").randint(0, WINDOW_WIDTH)
        self._btn.handle_event(pygame.event.Event(pygame.MOUSEMOTION,
                               pos=pygame.mouse.get_pos()))

    def draw(self, surf):
        surf.fill(C_BG)
        # Particles
        for p in self._particles:
            s = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_ACCENT, p["a"]), (p["r"], p["r"]), p["r"])
            surf.blit(s, (int(p["x"]), int(p["y"])))

        # Glow circle phía sau title
        cx, cy = WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 60
        pulse  = 0.5 + 0.5 * math.sin(self.tick * 1.5)
        glow_r = int(180 + 20 * pulse)
        glow   = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 220, 255, int(18 * pulse)),
                           (glow_r, glow_r), glow_r)
        surf.blit(glow, (cx - glow_r, cy - glow_r))

        # Title
        draw_text_center(surf, "DOTS", self._f_title, C_ACCENT,
                         cx, cy - 38)
        draw_text_center(surf, "& BOXES", self._f_title, C_LINE_P2,
                         cx, cy + 42)

        # Subtitle
        draw_text_center(surf, "Trí Tuệ Nhân Tạo — Nhóm ...",
                         self._f_sub, C_TEXT_DIM, cx, cy + 105)

        self._btn.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Màn hình 2 — Continue or New
# ══════════════════════════════════════════════════════════════════════════════

class ContinueOrNewScreen:
    NAME = "continue_or_new"

    def __init__(self, gm: GameManager):
        self.gm  = gm
        cx       = WINDOW_WIDTH // 2
        self._btn_continue = Button(cx-140, 320, 280, 60, "Chơi tiếp",
                                    hover_color=C_ACCENT, font_size=FONT_MEDIUM_SIZE)
        self._btn_new      = Button(cx-140, 410, 280, 60, "Ván mới",
                                    hover_color=C_ACCENT2, font_size=FONT_MEDIUM_SIZE)
        self._f_title = _font_bold(FONT_LARGE_SIZE)
        self._f_info  = _font(FONT_SMALL_SIZE)

    def handle_event(self, event):
        if self._btn_continue.handle_event(event):
            self.gm.load()
            return "game"
        if self._btn_new.handle_event(event):
            return "menu"
        return None

    def update(self, dt):
        pos = pygame.mouse.get_pos()
        self._btn_continue.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos))
        self._btn_new.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pos))

    def draw(self, surf):
        surf.fill(C_BG)
        cx = WINDOW_WIDTH // 2

        # Panel
        panel = pygame.Rect(cx-220, 220, 440, 300)
        draw_rect_alpha(surf, (*C_SURFACE, 230), panel, radius=20)
        pygame.draw.rect(surf, C_BORDER, panel, 2, border_radius=20)

        draw_text_center(surf, "Bạn có ván chơi dở!", self._f_title, C_ACCENT,
                         cx, 280)
        draw_text_center(surf, "Muốn tiếp tục hay bắt đầu ván mới?",
                         self._f_info, C_TEXT_DIM, cx, 320)

        self._btn_continue.draw(surf)
        self._btn_new.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Màn hình 3 — Menu lựa chọn
# ══════════════════════════════════════════════════════════════════════════════

class MenuScreen:
    NAME = "menu"

    def __init__(self, gm: GameManager):
        self.gm   = gm
        cx        = WINDOW_WIDTH // 2

        # Mode
        self._mode_pvai = ToggleButton(cx-200, 230, 180, 50, "Người vs Máy",
                                       selected=True, hover_color=C_ACCENT)
        self._mode_pvp  = ToggleButton(cx+20,  230, 180, 50, "Người vs Người",
                                       hover_color=C_ACCENT)
        self._mode      = "PvAI"

        # Difficulty (chỉ hiện khi PvAI)
        self._diff_easy = ToggleButton(cx-200, 330, 180, 50, "Easy",
                                       selected=False, hover_color=C_SUCCESS)
        self._diff_hard = ToggleButton(cx+20,  330, 180, 50, "Hard",
                                       selected=True,  hover_color=C_ACCENT2)
        self._difficulty = "Hard"

        # Board size
        self._size_5x4 = ToggleButton(cx-200, 430, 180, 50, "5×4 (nhỏ)",
                                      selected=True, hover_color=C_ACCENT)
        self._size_8x6 = ToggleButton(cx+20,  430, 180, 50, "8×6 (lớn)",
                                      hover_color=C_ACCENT)
        self._board_size = "5x4"

        # Play
        self._btn_play = Button(cx-130, 530, 260, 62, "BẮT ĐẦU",
                                color=C_ACCENT, hover_color=C_WHITE,
                                text_color=C_BG, font_size=FONT_LARGE_SIZE, radius=31)

        self._f_title   = _font_bold(FONT_LARGE_SIZE)
        self._f_section = _font_bold(FONT_SMALL_SIZE)

    def _sync_toggles(self):
        self._mode_pvai.selected = (self._mode == "PvAI")
        self._mode_pvp.selected  = (self._mode == "PvP")
        self._diff_easy.selected = (self._difficulty == "Easy")
        self._diff_hard.selected = (self._difficulty == "Hard")
        self._size_5x4.selected  = (self._board_size == "5x4")
        self._size_8x6.selected  = (self._board_size == "8x6")

    def handle_event(self, event):
        if self._mode_pvai.handle_event(event):  self._mode = "PvAI"
        if self._mode_pvp.handle_event(event):   self._mode = "PvP"
        if self._diff_easy.handle_event(event):  self._difficulty = "Easy"
        if self._diff_hard.handle_event(event):  self._difficulty = "Hard"
        if self._size_5x4.handle_event(event):   self._board_size = "5x4"
        if self._size_8x6.handle_event(event):   self._board_size = "8x6"
        self._sync_toggles()

        if self._btn_play.handle_event(event):
            self.gm.new_game(self._mode, self._difficulty, self._board_size)
            return "game"
        return None

    def update(self, dt):
        pos = pygame.mouse.get_pos()
        ev  = pygame.event.Event(pygame.MOUSEMOTION, pos=pos)
        for btn in [self._mode_pvai, self._mode_pvp,
                    self._diff_easy, self._diff_hard,
                    self._size_5x4,  self._size_8x6,
                    self._btn_play]:
            btn.handle_event(ev)

    def draw(self, surf):
        surf.fill(C_BG)
        cx = WINDOW_WIDTH // 2
        draw_text_center(surf, "Thiết lập game", self._f_title, C_ACCENT, cx, 100)

        # Labels
        draw_text_center(surf, "Chế độ chơi",  self._f_section, C_TEXT_DIM, cx, 200)
        draw_text_center(surf, "Bàn cờ",        self._f_section, C_TEXT_DIM, cx, 400)

        self._mode_pvai.draw(surf)
        self._mode_pvp.draw(surf)
        self._size_5x4.draw(surf)
        self._size_8x6.draw(surf)
        self._btn_play.draw(surf)

        if self._mode == "PvAI":
            draw_text_center(surf, "Độ khó AI", self._f_section, C_TEXT_DIM, cx, 300)
            self._diff_easy.draw(surf)
            self._diff_hard.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Màn hình 4 — Gameplay
# ══════════════════════════════════════════════════════════════════════════════

class GameScreen:
    NAME = "game"

    def __init__(self, gm: GameManager):
        self.gm          = gm
        self._hover_move = None   # move đang hover
        self._ai_thinking = False
        self._ai_move    = None   # move AI vừa tính xong
        self._flash_cells = []    # [(r,c, timer)] ô vừa chiếm → flash
        self._msg        = ""
        self._msg_timer  = 0.0
        self._f_small = _font(FONT_SMALL_SIZE)
        self._f_med   = _font(FONT_MEDIUM_SIZE)
        self._f_bold  = _font_bold(FONT_MEDIUM_SIZE)
        self._btn_save = Button(WINDOW_WIDTH - 120, 20, 100, 36, "Lưu & Thoát",
                                font_size=14, radius=8)
        self._board_offset = (0, 0)  # tính trong draw

    # ── Tính offset bàn cờ để căn giữa ────────────────────────────────────
    def _calc_offset(self):
        b = self.gm.board
        board_w = (b.cols - 1) * CELL_SIZE
        board_h = (b.rows - 1) * CELL_SIZE
        ox = (WINDOW_WIDTH  - board_w) // 2
        oy = (WINDOW_HEIGHT - board_h) // 2 + 20
        return ox, oy

    # ── Chuyển tọa độ pixel → move ────────────────────────────────────────
    def _pixel_to_move(self, px, py):
        ox, oy = self._calc_offset()
        b      = self.gm.board
        best_move = None
        best_dist  = 14   # ngưỡng click (px)

        # Cạnh ngang
        for r in range(b.rows):
            for c in range(b.cols - 1):
                if b.h_lines[r][c] != 0:
                    continue
                mx = ox + c * CELL_SIZE + CELL_SIZE // 2
                my = oy + r * CELL_SIZE
                if abs(py - my) < best_dist and abs(px - mx) < CELL_SIZE // 2:
                    d = abs(py - my)
                    if d < best_dist:
                        best_dist  = d
                        best_move  = ('h', r, c)

        # Cạnh dọc
        for r in range(b.rows - 1):
            for c in range(b.cols):
                if b.v_lines[r][c] != 0:
                    continue
                mx = ox + c * CELL_SIZE
                my = oy + r * CELL_SIZE + CELL_SIZE // 2
                if abs(px - mx) < best_dist and abs(py - my) < CELL_SIZE // 2:
                    d = abs(px - mx)
                    if d < best_dist:
                        best_dist  = d
                        best_move  = ('v', r, c)

        return best_move

    # ── Xử lý sự kiện ─────────────────────────────────────────────────────
    def handle_event(self, event):
        if self._btn_save.handle_event(event):
            self.gm.save()
            return "splash"

        if event.type == pygame.MOUSEMOTION:
            self._hover_move = self._pixel_to_move(*event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.gm.game_over:
                return "result"
            if self.gm.current_player.is_human and not self._ai_thinking:
                move = self._pixel_to_move(*event.pos)
                if move:
                    self._do_move(move)
                    if self.gm.game_over:
                        return "result"

        return None

    def _do_move(self, move):
        captured = self.gm.apply_move(move)
        if captured:
            self._flash_cells = [
                (r, c, 0.5)
                for r in range(self.gm.board.box_rows)
                for c in range(self.gm.board.box_cols)
                if self.gm.board.boxes[r][c] != 0
                   and (r, c) not in [(x, y) for x, y, _ in self._flash_cells]
            ]
            self._msg       = f"+{captured} ô!"
            self._msg_timer = 1.2

    _AI_NO_MOVE = object()  # sentinel: thread xong nhưng không có nước

    def _start_ai(self):
        self._ai_thinking = True
        depth = self.gm.ai_depth
        board_copy = copy.deepcopy(self.gm.board)

        def run():
            try:
                move = choose_move(board_copy, depth)
            except Exception:
                move = None
            self._ai_move = move if move is not None else self._AI_NO_MOVE
        t = threading.Thread(target=run, daemon=True)
        t.start()

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt):
        # Flash cells
        self._flash_cells = [
            (r, c, t - dt) for r, c, t in self._flash_cells if t - dt > 0
        ]
        # Msg timer
        if self._msg_timer > 0:
            self._msg_timer -= dt

        # Lượt AI
        if (not self.gm.game_over
                and not self.gm.current_player.is_human
                and not self._ai_thinking
                and self._ai_move is None):
            self._start_ai()

        if self._ai_move is not None:
            move = self._ai_move
            self._ai_move     = None
            self._ai_thinking = False
            if move is not self._AI_NO_MOVE:
                self._do_move(move)

        self._btn_save.handle_event(
            pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos()))

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, surf):
        surf.fill(C_BG)
        b  = self.gm.board
        ox, oy = self._calc_offset()

        # ── HUD (điểm, lượt) ───────────────────────────────────────────
        p1, p2   = self.gm.players
        cur      = self.gm.current_player
        p1_bold  = (cur == p1)
        p2_bold  = (cur == p2)

        # P1 card
        p1_rect = pygame.Rect(20, 20, 200, 70)
        draw_rect_alpha(surf,
                        (*C_LINE_P1, 30) if p1_bold else (*C_SURFACE, 200),
                        p1_rect, radius=12)
        if p1_bold:
            pygame.draw.rect(surf, C_LINE_P1, p1_rect, 2, border_radius=12)
        surf.blit(self._f_bold.render(p1.name, True, C_LINE_P1), (32, 30))
        surf.blit(self._f_med.render(str(p1.score), True, C_TEXT), (32, 55))

        # P2 card
        p2_rect = pygame.Rect(WINDOW_WIDTH-220, 20, 200, 70)
        draw_rect_alpha(surf,
                        (*C_LINE_P2, 30) if p2_bold else (*C_SURFACE, 200),
                        p2_rect, radius=12)
        if p2_bold:
            pygame.draw.rect(surf, C_LINE_P2, p2_rect, 2, border_radius=12)
        surf.blit(self._f_bold.render(p2.name, True, C_LINE_P2),
                  (WINDOW_WIDTH-208, 30))
        surf.blit(self._f_med.render(str(p2.score), True, C_TEXT),
                  (WINDOW_WIDTH-208, 55))

        # Lượt / AI thinking
        if self._ai_thinking:
            status = "Máy đang suy nghĩ..."
        else:
            status = f"Lượt: {cur.name}"
        draw_text_center(surf, status, self._f_small, C_TEXT_DIM,
                         WINDOW_WIDTH//2, 45)

        # Thông báo +ô
        if self._msg_timer > 0:
            alpha = int(255 * min(1.0, self._msg_timer))
            ms    = self._f_bold.render(self._msg, True, C_SUCCESS)
            ms.set_alpha(alpha)
            surf.blit(ms, (WINDOW_WIDTH//2 - ms.get_width()//2, 65))

        # ── Ô (box fill) ───────────────────────────────────────────────
        for r in range(b.box_rows):
            for c in range(b.box_cols):
                owner = b.boxes[r][c]
                if owner == 0:
                    continue
                color = C_BOX_P1 if owner == 1 else C_BOX_P2
                # flash boost alpha
                flash = next((t for rr, cc, t in self._flash_cells
                              if rr == r and cc == c), 0)
                a = min(255, int(color[3] + 120 * (flash / 0.5)))
                rect = pygame.Rect(
                    ox + c * CELL_SIZE + DOT_RADIUS,
                    oy + r * CELL_SIZE + DOT_RADIUS,
                    CELL_SIZE - DOT_RADIUS*2,
                    CELL_SIZE - DOT_RADIUS*2,
                )
                draw_rect_alpha(surf, (color[0], color[1], color[2], a), rect, radius=6)

                # chữ cái chủ
                lbl = self._f_small.render(
                    p1.name[0] if owner == 1 else p2.name[0],
                    True,
                    C_LINE_P1 if owner == 1 else C_LINE_P2
                )
                surf.blit(lbl, (rect.centerx - lbl.get_width()//2,
                                rect.centery - lbl.get_height()//2))

        # ── Cạnh ngang ─────────────────────────────────────────────────
        for r in range(b.rows):
            for c in range(b.cols - 1):
                x1 = ox + c * CELL_SIZE
                x2 = ox + (c+1) * CELL_SIZE
                y  = oy + r * CELL_SIZE
                owner = b.h_lines[r][c]
                if owner:
                    col = C_LINE_P1 if owner == 1 else C_LINE_P2
                    pygame.draw.line(surf, col, (x1, y), (x2, y), LINE_WIDTH)
                else:
                    hov = self._hover_move == ('h', r, c)
                    col = C_LINE_HOVER if hov else C_LINE_DEFAULT
                    w   = LINE_HOVER_WIDTH if hov else 2
                    pygame.draw.line(surf, col, (x1, y), (x2, y), w)

        # ── Cạnh dọc ───────────────────────────────────────────────────
        for r in range(b.rows - 1):
            for c in range(b.cols):
                x  = ox + c * CELL_SIZE
                y1 = oy + r * CELL_SIZE
                y2 = oy + (r+1) * CELL_SIZE
                owner = b.v_lines[r][c]
                if owner:
                    col = C_LINE_P1 if owner == 1 else C_LINE_P2
                    pygame.draw.line(surf, col, (x, y1), (x, y2), LINE_WIDTH)
                else:
                    hov = self._hover_move == ('v', r, c)
                    col = C_LINE_HOVER if hov else C_LINE_DEFAULT
                    w   = LINE_HOVER_WIDTH if hov else 2
                    pygame.draw.line(surf, col, (x, y1), (x, y2), w)

        # ── Điểm ───────────────────────────────────────────────────────
        for r in range(b.rows):
            for c in range(b.cols):
                x = ox + c * CELL_SIZE
                y = oy + r * CELL_SIZE
                col = C_DOT_HOVER if self._hover_near_dot(x, y) else C_DOT
                pygame.draw.circle(surf, col, (x, y), DOT_RADIUS)

        self._btn_save.draw(surf)

    def _hover_near_dot(self, dx, dy) -> bool:
        if self._hover_move is None:
            return False
        mx, my = pygame.mouse.get_pos()
        return abs(mx - dx) < 20 and abs(my - dy) < 20


# ══════════════════════════════════════════════════════════════════════════════
# Màn hình 5 — Kết quả
# ══════════════════════════════════════════════════════════════════════════════

class ResultScreen:
    NAME = "result"

    def __init__(self, gm: GameManager):
        self.gm   = gm
        self.tick = 0.0
        cx        = WINDOW_WIDTH // 2
        self._btn_again = Button(cx-140, 440, 280, 60, "Chơi lại",
                                 hover_color=C_ACCENT, font_size=FONT_MEDIUM_SIZE)
        self._btn_menu  = Button(cx-140, 520, 280, 60, "Menu",
                                 hover_color=C_ACCENT2, font_size=FONT_MEDIUM_SIZE)
        self._f_big   = _font_bold(52)
        self._f_title = _font_bold(FONT_LARGE_SIZE)
        self._f_med   = _font(FONT_MEDIUM_SIZE)

    def handle_event(self, event):
        if self._btn_again.handle_event(event):
            self.gm.new_game(self.gm.mode, self.gm.difficulty, self.gm.board_size)
            return "game"
        if self._btn_menu.handle_event(event):
            return "menu"
        return None

    def update(self, dt):
        self.tick += dt
        pos = pygame.mouse.get_pos()
        ev  = pygame.event.Event(pygame.MOUSEMOTION, pos=pos)
        self._btn_again.handle_event(ev)
        self._btn_menu.handle_event(ev)

    def draw(self, surf):
        surf.fill(C_BG)
        cx = WINDOW_WIDTH // 2

        winner = self.gm.get_winner()
        p1, p2 = self.gm.players

        # Glow
        pulse = 0.5 + 0.5 * math.sin(self.tick * 2)
        col   = C_LINE_P1 if (winner and winner.player_id == 1) else C_LINE_P2
        glow  = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, int(30 * pulse)), (150, 150), 150)
        surf.blit(glow, (cx - 150, 130))

        # Kết quả
        if winner:
            draw_text_center(surf, "🎉 Chiến thắng!", self._f_big, col, cx, 220)
            draw_text_center(surf, winner.name, self._f_title, C_WHITE, cx, 285)
        else:
            draw_text_center(surf, "Hòa!", self._f_big, C_WARNING, cx, 240)

        # Điểm
        score_txt = f"{p1.name}  {p1.score}  —  {p2.score}  {p2.name}"
        draw_text_center(surf, score_txt, self._f_med, C_TEXT_DIM, cx, 350)

        self._btn_again.draw(surf)
        self._btn_menu.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# ScreenManager — điều phối các màn hình
# ══════════════════════════════════════════════════════════════════════════════

class ScreenManager:
    def __init__(self):
        self.gm = GameManager()
        self._screens = {}
        self._current = None
        self._build_screens()
        self._switch("splash")

    def _build_screens(self):
        self._screens = {
            "splash":           SplashScreen(self.gm),
            "continue_or_new":  ContinueOrNewScreen(self.gm),
            "menu":             MenuScreen(self.gm),
            "game":             GameScreen(self.gm),
            "result":           ResultScreen(self.gm),
        }

    def _switch(self, name: str):
        # Tạo lại màn hình mới để reset state
        cls_map = {
            "splash":           SplashScreen,
            "continue_or_new":  ContinueOrNewScreen,
            "menu":             MenuScreen,
            "game":             GameScreen,
            "result":           ResultScreen,
        }
        self._screens[name] = cls_map[name](self.gm)
        self._current        = self._screens[name]

    def handle_event(self, event):
        next_screen = self._current.handle_event(event)
        if next_screen:
            self._switch(next_screen)

    def update(self, dt):
        next_screen = None
        self._current.update(dt)
        # GameScreen có thể tự chuyển sang result
        if hasattr(self._current, '_auto_next'):
            next_screen = self._current._auto_next
        if next_screen:
            self._switch(next_screen)

    def draw(self, surf):
        self._current.draw(surf)
