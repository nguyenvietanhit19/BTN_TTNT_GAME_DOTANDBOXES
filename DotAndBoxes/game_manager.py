# game_manager.py
"""
Quản lý vòng đời một ván game: khởi tạo, lượt chơi, lưu/tải.
"""
import json
import os

from board  import Board
from player import Player
from config import SAVE_FILE, DIFFICULTY_DEPTH, BOARD_CONFIGS


class GameManager:
    def __init__(self):
        self.board      = None
        self.players    = []          # [player1, player2]
        self.current_idx = 0          # 0 hoặc 1
        self.mode       = "PvAI"      # "PvAI" | "PvP"
        self.difficulty = "Hard"      # "Easy" | "Hard"
        self.board_size = "5x4"       # "5x4"  | "8x6"
        self.game_over  = False
        self.ai_depth   = 7

    # ──────────────────────────────────────────────────────────────────────────
    # Khởi tạo game mới
    # ──────────────────────────────────────────────────────────────────────────

    def new_game(self, mode: str, difficulty: str, board_size: str):
        self.mode       = mode
        self.difficulty = difficulty
        self.board_size = board_size
        self.game_over  = False
        self.current_idx = 0

        cfg = BOARD_CONFIGS[board_size]
        self.board = Board(cfg["cols"], cfg["rows"])

        if mode == "PvAI":
            self.players = [
                Player(1, "Bạn",   is_human=True),
                Player(2, "Máy",   is_human=False),
            ]
            self.ai_depth = DIFFICULTY_DEPTH[difficulty][board_size]
        else:
            self.players = [
                Player(1, "Người 1", is_human=True),
                Player(2, "Người 2", is_human=True),
            ]

    # ──────────────────────────────────────────────────────────────────────────
    # Lượt chơi
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def current_player(self) -> Player:
        return self.players[self.current_idx]

    def apply_move(self, move) -> int:
        """Áp dụng move cho người chơi hiện tại. Trả về số ô mới chiếm."""
        captured = self.board.apply_move(move, self.current_player.player_id)
        self.current_player.add_score(captured)

        if self.board.is_game_over():
            self.game_over = True
            self._delete_save()
        elif captured == 0:
            # Không chiếm ô → đổi lượt
            self.current_idx = 1 - self.current_idx

        return captured

    def get_winner(self):
        """Trả về Player thắng hoặc None nếu hòa."""
        p1, p2 = self.players
        if p1.score > p2.score:
            return p1
        elif p2.score > p1.score:
            return p2
        return None  # hòa

    # ──────────────────────────────────────────────────────────────────────────
    # Lưu / Tải
    # ──────────────────────────────────────────────────────────────────────────

    def save(self):
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
        data = {
            "mode":        self.mode,
            "difficulty":  self.difficulty,
            "board_size":  self.board_size,
            "current_idx": self.current_idx,
            "ai_depth":    self.ai_depth,
            "board":       self.board.to_dict(),
            "players":     [p.to_dict() for p in self.players],
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> bool:
        """Tải game đã lưu. Trả về True nếu thành công."""
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.mode        = data["mode"]
            self.difficulty  = data["difficulty"]
            self.board_size  = data["board_size"]
            self.current_idx = data["current_idx"]
            self.ai_depth    = data["ai_depth"]
            self.board       = Board.from_dict(data["board"])
            self.players     = [Player.from_dict(p) for p in data["players"]]
            self.game_over   = False
            return True
        except Exception:
            return False

    def has_save(self) -> bool:
        return os.path.exists(SAVE_FILE)

    def _delete_save(self):
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
