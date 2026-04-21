"""
AI 3 tầng cho Dots and Boxes:
  Tầng 1 — Greedy      : chiếm ngay ô 3 cạnh nếu có
  Tầng 2 — Chain       : Double-cross khi đủ điều kiện
  Tầng 3 — Minimax+AB  : tìm kiếm theo độ sâu với heuristic
"""
import math
import random

from board import Board


AI_ID = 2
HUMAN_ID = 1


def choose_move(board: Board, depth: int, difficulty: str = "Hard"):
    """
    Trả về move tốt nhất cho AI (player_id = 2).
    depth: độ sâu Minimax (từ config).
    """
    moves = board.available_moves()
    if not moves:
        return None

    n = len(moves)
    if n > 20:
        depth = min(depth, 3)
    elif n > 12:
        depth = min(depth, 5)

    greedy = _greedy_move(board)
    if greedy:
        return greedy

    if difficulty == "Easy":
        return _easy_move(board)

    chain_move = _chain_move(board)
    if chain_move:
        return chain_move

    ordered = _order_moves(board, moves)
    scored_moves = []
    alpha, beta = -math.inf, math.inf

    for move in ordered:
        prev_boxes = board.copy_boxes()
        captured = board.apply_move(move, AI_ID)
        next_is_max = captured > 0
        score = _minimax(board, depth - 1, alpha, beta, next_is_max)
        board.undo_move(move, prev_boxes)
        scored_moves.append((move, score))
        alpha = max(alpha, score)

    if not scored_moves:
        return random.choice(moves)

    best_score = max(score for _, score in scored_moves)
    best_moves = [move for move, score in scored_moves if score == best_score]

    if difficulty == "Hard":
        return random.choice(best_moves)

    return _medium_like_random_choice(scored_moves)


def _greedy_move(board: Board):
    """Trả về move chiếm ô có 3 cạnh (nếu có), ngẫu nhiên trong số đó."""
    greedy_moves = []
    for move in board.available_moves():
        prev = board.copy_boxes()
        captured = board.apply_move(move, AI_ID)
        board.undo_move(move, prev)
        if captured > 0:
            greedy_moves.append(move)
    return random.choice(greedy_moves) if greedy_moves else None


def _easy_move(board: Board):
    """
    Easy: đánh ngẫu nhiên nhiều hơn.
    Ưu tiên giữ được nước ăn ô, còn lại chọn ngẫu nhiên trong nhóm an toàn nếu có.
    """
    moves = board.available_moves()
    safe_moves = [move for move in moves if not _gives_opponent_box(board, move)]
    if safe_moves:
        return random.choice(safe_moves)
    return random.choice(moves)


def _medium_like_random_choice(scored_moves):
    """
    Chọn ngẫu nhiên trong nhóm nước đi gần tốt nhất để AI không bị quá cứng.
    """
    scored_moves.sort(key=lambda item: item[1], reverse=True)
    top_count = min(3, len(scored_moves))
    candidate_pool = [move for move, _ in scored_moves[:top_count]]
    return random.choice(candidate_pool)


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

    if len(chains) > 2:
        return None

    ai_score = board.score(AI_ID)
    human_score = board.score(HUMAN_ID)
    total = board.total_boxes()
    chain = long_chains[0]

    sim_eat_all = ai_score + len(chain)
    remaining_after = total - ai_score - human_score - len(chain)
    sim_double_cross = ai_score + (len(chain) - 2) + remaining_after

    ai_wins_eat = sim_eat_all > total / 2
    ai_wins_doublecross = sim_double_cross > total / 2

    if ai_wins_eat and ai_wins_doublecross:
        opening_move = _find_chain_opening(board, chain)
        if opening_move:
            return opening_move

    return _safe_move(board)


def _find_chain_opening(board: Board, chain):
    """Tìm cạnh mở ở đầu chuỗi."""
    r, c = chain[0]
    candidates = []
    if not board.is_h_line_set(r, c):
        candidates.append(("h", r, c))
    if not board.is_h_line_set(r + 1, c):
        candidates.append(("h", r + 1, c))
    if not board.is_v_line_set(r, c):
        candidates.append(("v", r, c))
    if not board.is_v_line_set(r, c + 1):
        candidates.append(("v", r, c + 1))
    return candidates[0] if candidates else None


def _safe_move(board: Board):
    """
    Trả về move an toàn nhất: ưu tiên cạnh không tạo ô 3-sided mới cho đối thủ.
    """
    moves = board.available_moves()
    safe = []
    for move in moves:
        if not _gives_opponent_box(board, move):
            safe.append(move)
    if safe:
        return random.choice(safe)
    return min(moves, key=lambda m: _danger_score(board, m))


def _three_sided_boxes(board: Board):
    return {
        (r, c)
        for r in range(board.box_rows)
        for c in range(board.box_cols)
        if board.boxes[r][c] == 0 and board.count_box_sides(r, c) == 3
    }


def _gives_opponent_box(board: Board, move) -> bool:
    """Move này có tạo thêm ô 3-cạnh mới cho đối thủ không?"""
    before = _three_sided_boxes(board)
    prev = board.copy_boxes()
    board.apply_move(move, AI_ID)
    after = _three_sided_boxes(board)
    board.undo_move(move, prev)
    return len(after - before) > 0


def _danger_score(board: Board, move) -> int:
    """Đếm số ô 3-sided mới tạo ra sau move."""
    before = _three_sided_boxes(board)
    prev = board.copy_boxes()
    board.apply_move(move, AI_ID)
    after = _three_sided_boxes(board)
    board.undo_move(move, prev)
    return len(after - before)


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
            next_max = captured > 0
            value = max(value, _minimax(board, depth - 1, alpha, beta, next_max))
            board.undo_move(move, prev)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    value = math.inf
    for move in ordered:
        prev = board.copy_boxes()
        captured = board.apply_move(move, player_id)
        next_max = captured == 0
        value = min(value, _minimax(board, depth - 1, alpha, beta, next_max))
        board.undo_move(move, prev)
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value


def _evaluate(board: Board) -> float:
    """
    Hàm đánh giá heuristic:
      - Điểm cơ bản: hiệu số điểm AI - người
      - Bonus: số ô 3-sided
      - Chain heuristic: ưu tiên chuỗi dài
    """
    ai_score = board.score(AI_ID)
    human_score = board.score(HUMAN_ID)
    base = (ai_score - human_score) * 10

    three_sided = _three_sided_boxes(board)
    chain_bonus = len(three_sided) * 2

    chains = board.get_chains()
    chain_value = 0
    for ch in chains:
        if len(ch) >= 3:
            chain_value += len(ch)
        elif len(ch) == 1:
            chain_value -= 1

    return base + chain_bonus + chain_value


def _order_moves(board: Board, moves):
    """
    Sắp xếp move: ưu tiên move chiếm ô ngay, sau đó move an toàn,
    cuối cùng move tạo ô 3-sided mới cho đối thủ.
    """
    def priority(move):
        prev = board.copy_boxes()
        captured = board.apply_move(move, AI_ID)
        board.undo_move(move, prev)
        if captured > 0:
            return 0
        if not _gives_opponent_box(board, move):
            return 1
        return 2

    return sorted(moves, key=priority)
