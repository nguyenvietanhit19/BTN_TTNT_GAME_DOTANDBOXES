"""
Quản lý trạng thái bàn cờ Dots and Boxes.

Quy ước:
  - dots: lưới (rows × cols) điểm
  - h_lines[r][c]: cạnh ngang giữa dot(r,c) và dot(r, c+1)  → (rows) × (cols-1)
  - v_lines[r][c]: cạnh dọc  giữa dot(r,c) và dot(r+1, c)  → (rows-1) × (cols)
  - boxes[r][c]:   ô vuông (rows-1) × (cols-1), giá trị = player_id hoặc 0
"""


class Board:
    def __init__(self, cols: int, rows: int):
        """
        cols, rows: số cột và hàng của LƯỚI DOT.
        Số ô vuông = (rows-1) × (cols-1).
        """
        self.cols = cols
        self.rows = rows
        self.box_cols = cols - 1
        self.box_rows = rows - 1

        self.h_lines = [[0] * (cols - 1) for _ in range(rows)]
        self.v_lines = [[0] * cols for _ in range(rows - 1)]
        self.boxes = [[0] * (cols - 1) for _ in range(rows - 1)]

    def is_h_line_set(self, r: int, c: int) -> bool:
        return self.h_lines[r][c] != 0

    def is_v_line_set(self, r: int, c: int) -> bool:
        return self.v_lines[r][c] != 0

    def set_h_line(self, r: int, c: int, player_id: int) -> int:
        """Đặt cạnh ngang, trả về số ô mới chiếm được."""
        if self.h_lines[r][c] != 0:
            return 0
        self.h_lines[r][c] = player_id
        return self._check_boxes(player_id)

    def set_v_line(self, r: int, c: int, player_id: int) -> int:
        """Đặt cạnh dọc, trả về số ô mới chiếm được."""
        if self.v_lines[r][c] != 0:
            return 0
        self.v_lines[r][c] = player_id
        return self._check_boxes(player_id)

    def _check_boxes(self, player_id: int) -> int:
        """Sau khi đặt cạnh, kiểm tra toàn bàn tìm ô mới hoàn thành."""
        count = 0
        for r in range(self.box_rows):
            for c in range(self.box_cols):
                if self.boxes[r][c] == 0 and self._box_complete(r, c):
                    self.boxes[r][c] = player_id
                    count += 1
        return count

    def _box_complete(self, r: int, c: int) -> bool:
        """Ô (r,c) có đủ 4 cạnh không?"""
        top = self.h_lines[r][c] != 0
        bottom = self.h_lines[r + 1][c] != 0
        left = self.v_lines[r][c] != 0
        right = self.v_lines[r][c + 1] != 0
        return top and bottom and left and right

    def count_box_sides(self, r: int, c: int) -> int:
        """Đếm số cạnh đã kẻ của ô (r,c)."""
        top = int(self.h_lines[r][c] != 0)
        bottom = int(self.h_lines[r + 1][c] != 0)
        left = int(self.v_lines[r][c] != 0)
        right = int(self.v_lines[r][c + 1] != 0)
        return top + bottom + left + right

    def score(self, player_id: int) -> int:
        return sum(
            self.boxes[r][c] == player_id
            for r in range(self.box_rows)
            for c in range(self.box_cols)
        )

    def total_boxes(self) -> int:
        return self.box_rows * self.box_cols

    def is_game_over(self) -> bool:
        return all(
            self.boxes[r][c] != 0
            for r in range(self.box_rows)
            for c in range(self.box_cols)
        )

    def available_moves(self):
        """Trả về list các move dạng ('h', r, c) hoặc ('v', r, c)."""
        moves = []
        for r in range(self.rows):
            for c in range(self.cols - 1):
                if self.h_lines[r][c] == 0:
                    moves.append(("h", r, c))
        for r in range(self.rows - 1):
            for c in range(self.cols):
                if self.v_lines[r][c] == 0:
                    moves.append(("v", r, c))
        return moves

    def apply_move(self, move, player_id: int) -> int:
        """Áp dụng move, trả về số ô mới chiếm."""
        kind, r, c = move
        if kind == "h":
            return self.set_h_line(r, c, player_id)
        return self.set_v_line(r, c, player_id)

    def undo_move(self, move, prev_boxes):
        """Hoàn tác move (dùng trong Minimax)."""
        kind, r, c = move
        if kind == "h":
            self.h_lines[r][c] = 0
        else:
            self.v_lines[r][c] = 0
        for r2 in range(self.box_rows):
            for c2 in range(self.box_cols):
                self.boxes[r2][c2] = prev_boxes[r2][c2]

    def copy_boxes(self):
        return [row[:] for row in self.boxes]

    def get_chains(self):
        """
        Tìm tất cả các chuỗi ô liên thông qua cạnh chung còn mở.
        Trả về list các chain, mỗi chain là list [(r,c), ...] của các ô có đúng 3 cạnh.
        """
        three_sided = set()
        for r in range(self.box_rows):
            for c in range(self.box_cols):
                if self.boxes[r][c] == 0 and self.count_box_sides(r, c) == 3:
                    three_sided.add((r, c))

        visited = set()
        chains = []
        for start in three_sided:
            if start in visited:
                continue
            chain = []
            stack = [start]
            while stack:
                cell = stack.pop()
                if cell in visited:
                    continue
                visited.add(cell)
                chain.append(cell)
                r, c = cell
                for nr, nc in self._neighbors(r, c):
                    if (
                        (nr, nc) in three_sided
                        and (nr, nc) not in visited
                        and self._connected_by_open_edge(r, c, nr, nc)
                    ):
                        stack.append((nr, nc))
            chains.append(chain)
        return chains

    def _neighbors(self, r: int, c: int):
        """Các ô láng giềng kề cạnh của ô (r,c)."""
        result = []
        if r > 0:
            result.append((r - 1, c))
        if r < self.box_rows - 1:
            result.append((r + 1, c))
        if c > 0:
            result.append((r, c - 1))
        if c < self.box_cols - 1:
            result.append((r, c + 1))
        return result

    def _connected_by_open_edge(self, r1: int, c1: int, r2: int, c2: int) -> bool:
        """Hai ô liền kề chỉ thuộc cùng chain nếu cạnh chung giữa chúng còn mở."""
        if r1 == r2:
            if c2 == c1 + 1:
                return self.v_lines[r1][c1 + 1] == 0
            if c2 == c1 - 1:
                return self.v_lines[r1][c1] == 0
        elif c1 == c2:
            if r2 == r1 + 1:
                return self.h_lines[r1 + 1][c1] == 0
            if r2 == r1 - 1:
                return self.h_lines[r1][c1] == 0
        return False

    def to_dict(self):
        return {
            "cols": self.cols,
            "rows": self.rows,
            "h_lines": self.h_lines,
            "v_lines": self.v_lines,
            "boxes": self.boxes,
        }

    @classmethod
    def from_dict(cls, data):
        board = cls(data["cols"], data["rows"])
        board.h_lines = data["h_lines"]
        board.v_lines = data["v_lines"]
        board.boxes = data["boxes"]
        return board
