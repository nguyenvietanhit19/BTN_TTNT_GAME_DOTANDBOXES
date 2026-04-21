# ai/minimax.py
"""
AI 3 tầng cho Dots and Boxes:
  Tầng 1 — Greedy      : chiếm ngay ô 3 cạnh nếu có
  Tầng 2 — Chain       : Double-cross khi đủ điều kiện
  Tầng 3 — Minimax+AB  : tìm kiếm theo độ sâu với heuristic
"""
import math
import random
from board import Board


AI_ID     = 2
HUMAN_ID  = 1


# ══════════════════════════════════════════════════════════════════════════════
# Hàm công khai: chọn nước đi cho AI
# ══════════════════════════════════════════════════════════════════════════════

def choose_move(board: Board, depth: int):
    """
    Trả về move tốt nhất cho AI (player_id = 2).
    depth: độ sâu Minimax (từ config).
    """
    moves = board.available_moves()
    if not moves:
        return None

    # Adaptive depth: giảm độ sâu khi còn nhiều nước để tránh timeout
    n = len(moves)
    if n > 20:
        depth = min(depth, 3)
    elif n > 12:
        depth = min(depth, 5)

    # ── Tầng 1: Greedy ─────────────────────────────────────────────────────
    greedy = _greedy_move(board)
    if greedy:
        return greedy

    # ── Tầng 2: Chain Analysis / Double-cross ──────────────────────────────
    chain_move = _chain_move(board)
    if chain_move:
        return chain_move

    # ── Tầng 3: Minimax + Alpha-Beta ───────────────────────────────────────
    best_move  = None
    best_score = -math.inf
    alpha, beta = -math.inf, math.inf

    # Sắp xếp ưu tiên: tránh đưa ô 2 cạnh → 3 cạnh trước
    ordered = _order_moves(board, moves)

    for move in ordered:
        prev_boxes = board.copy_boxes()
        captured   = board.apply_move(move, AI_ID)
        # Nếu AI vừa chiếm ô → vẫn là lượt AI
        next_is_max = captured > 0
        score = _minimax(board, depth - 1, alpha, beta, next_is_max)
        board.undo_move(move, prev_boxes)

        if score > best_score:
            best_score = score
            best_move  = move
        alpha = max(alpha, best_score)

    return best_move


# ══════════════════════════════════════════════════════════════════════════════
# Tầng 1 — Greedy
# ══════════════════════════════════════════════════════════════════════════════

def _greedy_move(board: Board):
    """Trả về move chiếm ô có 3 cạnh (nếu có), ngẫu nhiên trong số đó."""
    safe = []
    for move in board.available_moves():
        prev = board.copy_boxes()
        captured = board.apply_move(move, AI_ID)
        board.undo_move(move, prev)
        if captured > 0:
            safe.append(move)
    return random.choice(safe) if safe else None


# ══════════════════════════════════════════════════════════════════════════════
# Tầng 2 — Chain Analysis & Double-cross
# ══════════════════════════════════════════════════════════════════════════════

def _chain_move(board: Board):
    """
    Kích hoạt khi: chuỗi ≥ 3 ô, số chuỗi còn lại ≤ 2,
    và cả 2 nhánh (ăn hết / để lại 2) đều giúp AI thắng.
    Trả về move Double-cross hoặc None.
    """
    chains = board.get_chains()
    if not chains:
        return None

    long_chains = [c for c in chains if len(c) >= 3]
    if not long_chains:
        return None

    total_remaining_chains = len(chains)
    if total_remaining_chains > 2:
        return None

    ai_score    = board.score(AI_ID)
    human_score = board.score(HUMAN_ID)
    total       = board.total_boxes()

    chain = long_chains[0]  # xử lý chuỗi đầu tiên

    # Ước tính: nếu AI ăn hết chuỗi
    sim_eat_all   = ai_score + len(chain)
    # Nếu để lại 2 (Double-cross): đối thủ buộc lấy 2, AI lấy phần còn lại
    remaining_after = total - ai_score - human_score - len(chain)
    sim_double_cross = ai_score + (len(chain) - 2) + remaining_after

    ai_wins_eat       = sim_eat_all       > total / 2
    ai_wins_doublecross = sim_double_cross > total / 2

    if ai_wins_eat and ai_wins_doublecross:
        # Double-cross: kẻ cạnh mở đầu chuỗi (để lại 2 ô cuối cho đối thủ)
        opening_move = _find_chain_opening(board, chain)
        if opening_move:
            return opening_move

    # Fallback: an toàn, tránh kẻ cạnh thứ 3 vào ô
    return _safe_move(board)


def _find_chain_opening(board: Board, chain):
    """Tìm cạnh mở đầu chuỗi (cạnh chưa kẻ duy nhất của ô đầu chuỗi)."""
    r, c = chain[0]
    candidates = []
    if not board.is_h_line_set(r, c):     candidates.append(('h', r, c))
    if not board.is_h_line_set(r+1, c):   candidates.append(('h', r+1, c))
    if not board.is_v_line_set(r, c):     candidates.append(('v', r, c))
    if not board.is_v_line_set(r, c+1):   candidates.append(('v', r, c+1))
    return candidates[0] if candidates else None


def _safe_move(board: Board):
    """
    Trả về move 'an toàn' nhất: ưu tiên cạnh không tạo ô 3-sided cho đối thủ.
    """
    moves = board.available_moves()
    safe = []
    for move in moves:
        if not _gives_opponent_box(board, move):
            safe.append(move)
    if safe:
        return random.choice(safe)
    # Không có move an toàn → chọn move ít tệ nhất
    return min(moves, key=lambda m: _danger_score(board, m))


def _gives_opponent_box(board: Board, move) -> bool:
    """Move này có tạo ô 3-cạnh cho đối thủ không?"""
    prev = board.copy_boxes()
    board.apply_move(move, AI_ID)
    # Sau khi kẻ cạnh, kiểm tra có ô nào còn 3 cạnh không
    danger = any(
        board.boxes[r][c] == 0 and board.count_box_sides(r, c) == 3
        for r in range(board.box_rows)
        for c in range(board.box_cols)
    )
    board.undo_move(move, prev)
    return danger


def _danger_score(board: Board, move) -> int:
    """Đếm số ô 3-sided mới tạo ra sau move."""
    prev = board.copy_boxes()
    board.apply_move(move, AI_ID)
    count = sum(
        1 for r in range(board.box_rows)
        for c in range(board.box_cols)
        if board.boxes[r][c] == 0 and board.count_box_sides(r, c) == 3
    )
    board.undo_move(move, prev)
    return count


# ══════════════════════════════════════════════════════════════════════════════
# Tầng 3 — Minimax + Alpha-Beta
# ══════════════════════════════════════════════════════════════════════════════

def _minimax(board: Board, depth: int, alpha: float, beta: float,
             is_maximizing: bool) -> float:
    if depth == 0 or board.is_game_over():
        return _evaluate(board)

    moves = board.available_moves()
    if not moves:
        return _evaluate(board)

    ordered = _order_moves(board, moves)
    player_id = AI_ID if is_maximizing else HUMAN_ID

    if is_maximizing:
        value = -math.inf
        for move in ordered:
            prev = board.copy_boxes()
            captured = board.apply_move(move, player_id)
            # Chiếm được ô → vẫn là lượt MAX
            next_max = captured > 0
            value = max(value, _minimax(board, depth - 1, alpha, beta, next_max))
            board.undo_move(move, prev)
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # pruning
        return value
    else:
        value = math.inf
        for move in ordered:
            prev = board.copy_boxes()
            captured = board.apply_move(move, player_id)
            next_max = not (captured > 0)  # nếu MIN chiếm được ô → MIN tiếp tục
            if captured > 0:
                next_max = False  # MIN tiếp tục
            else:
                next_max = True   # chuyển sang MAX
            value = min(value, _minimax(board, depth - 1, alpha, beta, next_max))
            board.undo_move(move, prev)
            beta = min(beta, value)
            if alpha >= beta:
                break  # pruning
        return value


def _evaluate(board: Board) -> float:
    """
    Hàm đánh giá heuristic:
      - Điểm cơ bản: hiệu số điểm AI - người
      - Bonus: số ô 3-sided của AI (sắp chiếm được)
      - Penalty: số ô 3-sided của đối thủ (AI sắp để lộ)
      - Chain heuristic: chuỗi dài có lợi cho AI
    """
    ai_score    = board.score(AI_ID)
    human_score = board.score(HUMAN_ID)
    base = (ai_score - human_score) * 10

    # Ô sắp chiếm được
    three_sided = [
        (r, c)
        for r in range(board.box_rows)
        for c in range(board.box_cols)
        if board.boxes[r][c] == 0 and board.count_box_sides(r, c) == 3
    ]
    # Nếu đang lượt AI → 3-sided là lợi thế
    chain_bonus = len(three_sided) * 2

    # Chain heuristic: ưu tiên chuỗi dài
    chains = board.get_chains()
    chain_value = 0
    for ch in chains:
        if len(ch) >= 3:
            chain_value += len(ch)  # AI có thể khai thác chuỗi dài
        elif len(ch) == 1:
            chain_value -= 1  # chuỗi ngắn ít lợi thế hơn

    return base + chain_bonus + chain_value


# ══════════════════════════════════════════════════════════════════════════════
# Tiện ích
# ══════════════════════════════════════════════════════════════════════════════

def _order_moves(board: Board, moves):
    """
    Sắp xếp move: ưu tiên move chiếm ô ngay, sau đó move an toàn,
    cuối cùng move tạo ô 3-sided cho đối thủ.
    """
    def priority(move):
        prev = board.copy_boxes()
        captured = board.apply_move(move, AI_ID)
        board.undo_move(move, prev)
        if captured > 0:
            return 0   # tốt nhất: chiếm ngay
        if not _gives_opponent_box(board, move):
            return 1   # an toàn
        return 2       # nguy hiểm
    return sorted(moves, key=priority)
