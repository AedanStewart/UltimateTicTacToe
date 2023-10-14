import functools

WIN_PATTERNS = [
    0b111000000,
    0b000111000,
    0b000000111,
    0b100100100,
    0b010010010,
    0b001001001,
    0b100010001,
    0b001010100,
]
NEAR_WIN_PATTERNS = [
    (0b110000000, 2),
    (0b101000000, 1),
    (0b011000000, 0),
    (0b000110000, 5),
    (0b000101000, 4),
    (0b000011000, 3),
    (0b000000110, 8),
    (0b000000101, 7),
    (0b000000011, 6),
    (0b100100000, 6),
    (0b100000100, 3),
    (0b000100100, 0),
    (0b010010000, 7),
    (0b010000010, 4),
    (0b000010010, 1),
    (0b001001000, 8),
    (0b001000001, 5),
    (0b000001001, 2),
    (0b100010000, 8),
    (0b100000001, 4),
    (0b000010001, 0),
    (0b001010000, 6),
    (0b001000100, 4),
    (0b000010100, 2),
]
BIT_POSITION_LOOKUP = {1 << (80 - i): i for i in range(81)}
SUBBOARD_WIN_WEIGHT = 100
SUBBOARD_NEAR_WIN_WEIGHT = 5
OVERALL_NEAR_WIN_WEIGHT = 200
REALLY_BIG_NUMBER = 100_000_000_000


def place_index(board: int, index: int):
    return board | (1 << (80 - index))


def get_index(board: int, index: int):
    return (board & (1 << (80 - index))) != 0


def get_subboard(board: tuple[int, int, int, int], subboard: int):
    x_board, o_board, _, _ = board
    return (
        (x_board >> (81 - ((subboard + 1) * 9))) & ((1 << 9) - 1),
        (o_board >> (81 - ((subboard + 1) * 9))) & ((1 << 9) - 1),
    )


# superfluous function, but it makes main.py marginally easier
def place_token(board: tuple[int, int, int, int], index: int, token: int):
    return make_move(board, 1 << (80 - index), token)


def make_move(board: tuple[int, int, int, int], move: int, token: int):
    idx = BIT_POSITION_LOOKUP[move]
    subboard_idx = idx // 9

    if token == 1:
        xb, ob, xw, ow = board
        xb |= move
        subboard = get_subboard((xb, ob, xw, ow), subboard_idx)
        xw |= subboard_has_win(subboard[0]) << (8 - subboard_idx)
        return (xb, ob, xw, ow)
    else:
        xb, ob, xw, ow = board
        ob |= move
        subboard = get_subboard((xb, ob, xw, ow), subboard_idx)
        ow |= subboard_has_win(subboard[1]) << (8 - subboard_idx)
        return (xb, ob, xw, ow)


# this hurts to look at
def find_move_list(board: tuple[int, int, int, int], subboard: int):
    overall = board[0] | board[1]
    moves = []
    sb = get_subboard(board, subboard)
    if (
        subboard_has_win(sb[0])
        or subboard_has_win(sb[1])
        or (sb[0] | sb[1]) == ((1 << 9) - 1)
    ):
        for z in range(9):
            sbz = get_subboard(board, z)
            if subboard_has_win(sbz[0]) or subboard_has_win(sbz[1]):
                continue
            for i in range(9):
                if not get_index(overall, z * 9 + i):
                    moves.append(i + (z * 9))
    else:
        for i in range(9):
            if not get_index(overall, subboard * 9 + i):
                moves.append(i + (subboard * 9))
    return moves


def find_moves(board: tuple[int, int, int, int], subboard: int):
    bitmask = 0
    won_boards = board[2] | board[3]
    sb = get_subboard(board, subboard)
    if (1 << (8 - subboard)) & won_boards or (sb[0] | sb[1]) == ((1 << 9) - 1):
        for i in range(9):
            if won_boards & (1 << i):
                bitmask |= ((1 << 9) - 1) << (i * 9)
    else:
        for i in range(9):
            if i != (8 - subboard):
                bitmask |= ((1 << 9) - 1) << (i * 9)
    return ((1 << 81) - 1) ^ (board[0] | board[1] | bitmask)


@functools.lru_cache
def subboard_has_win(subboard: int):
    for pattern in WIN_PATTERNS:
        if (subboard & pattern) == pattern:
            return True
    return False


def check_win(board: tuple[int, int, int, int]):
    if subboard_has_win(board[2]):
        return 1
    elif subboard_has_win(board[3]):
        return -1
    return 0


def check_draw(board: tuple[int, int, int, int]):
    overallwins = board[2] | board[3]
    if overallwins == ((1 << 9) - 1):
        return True
    for i in range(9):
        if overallwins & (1 << (8 - i)):
            continue
        sb = get_subboard(board, i)
        if (sb[0] | sb[1]) != ((1 << 9) - 1):
            return False
    return True


@functools.lru_cache
def score_subboard(subboard: int, opponent_subboard: int):
    score = 0
    for pattern, missingindex in NEAR_WIN_PATTERNS:
        if (subboard & pattern) == pattern and opponent_subboard & (
            1 << 8 - missingindex
        ) == 0:
            score += 1
    return score


def evaluate_board(board: tuple[int, int, int, int], token: int):
    evaluation = 0

    cw = check_win(board)
    if cw:
        return token * 100_000_000 * cw

    for i in range(9):
        if board[2] & (1 << (8 - i)):
            evaluation += SUBBOARD_WIN_WEIGHT
            continue
        elif board[3] & (1 << (8 - i)):
            evaluation -= SUBBOARD_WIN_WEIGHT
            continue

        x_sb, o_sb = get_subboard(board, i)
        evaluation += score_subboard(x_sb, o_sb) * SUBBOARD_NEAR_WIN_WEIGHT
        evaluation -= score_subboard(o_sb, x_sb) * SUBBOARD_NEAR_WIN_WEIGHT

    evaluation += score_subboard(board[2], board[3]) * OVERALL_NEAR_WIN_WEIGHT
    evaluation -= score_subboard(board[3], board[2]) * OVERALL_NEAR_WIN_WEIGHT

    return evaluation * token


def negamax_alphabeta(
    board: tuple[int, int, int, int],
    subboard: int,
    token: int,
    depth: int,
    alpha: int = -REALLY_BIG_NUMBER,
    beta: int = REALLY_BIG_NUMBER,
):
    if depth == 0 or check_win(board) or check_draw(board):
        return (evaluate_board(board, token), -1)

    moves = find_moves(board, subboard)
    assert moves != 0, "This should have been unreachable, what have I done"

    value = -REALLY_BIG_NUMBER
    bestmove = -1
    while moves:
        move = ~(moves - 1) & moves
        moves ^= move

        recur_score, _ = negamax_alphabeta(
            make_move(board, move, token),
            BIT_POSITION_LOOKUP[move] % 9,
            -token,
            depth - 1,
            -beta,
            -alpha,
        )

        if -recur_score > value:
            value = -recur_score
            bestmove = BIT_POSITION_LOOKUP[move]

        alpha = max(alpha, value)
        if alpha >= beta:
            break

    return (value, bestmove)


def find_best_move(
    board: tuple[int, int, int, int], subboard: int, token: int, depth: int
):
    return negamax_alphabeta(board, subboard, token, depth)[1]
