import functools

SIZE = 81
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
SUBBOARD_WIN_WEIGHT = 100
SUBBOARD_NEAR_WIN_WEIGHT = 5
OVERALL_NEAR_WIN_WEIGHT = 200


def place_index(board: int, index: int):
    return board | (1 << (SIZE - index - 1))


def get_index(board: int, index: int):
    return (board & (1 << (SIZE - index - 1))) != 0


@functools.lru_cache
def get_subboard(board: tuple[int, int], subboard: int):
    x_board, o_board = board
    return (
        (x_board >> (SIZE - ((subboard + 1) * 9))) & 0b111111111,
        (o_board >> (SIZE - ((subboard + 1) * 9))) & 0b111111111,
    )


def place_token(board: tuple[int, int], index: int, token: int):
    if token == 1:
        return (place_index(board[0], index), board[1])
    else:
        return (board[0], place_index(board[1], index))


def find_moves(board: tuple[int, int], subboard: int):
    overall = board[0] | board[1]
    moves = []
    sb = get_subboard(board, subboard)
    if subboard_has_win(sb[0]) or subboard_has_win(sb[1]) or not ~(sb[0] | sb[1]):
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


@functools.lru_cache
def subboard_has_win(subboard: int):
    for pattern in WIN_PATTERNS:
        if (subboard & pattern) == pattern:
            return True
    return False


@functools.lru_cache
def check_win(board: tuple[int, int]):
    overall_wins_x = 0
    overall_wins_o = 0
    for i in range(9):
        x_sb, o_sb = get_subboard(board, i)
        if subboard_has_win(x_sb):
            overall_wins_x = overall_wins_x | (1 << (8 - i))
        elif subboard_has_win(o_sb):
            overall_wins_o = overall_wins_o | (1 << (8 - i))

    if subboard_has_win(overall_wins_x):
        return 1
    elif subboard_has_win(overall_wins_o):
        return -1
    return 0


@functools.lru_cache
def score_subboard(subboard: int, opponent_subboard: int):
    score = 0
    for pattern, missingindex in NEAR_WIN_PATTERNS:
        if (subboard & pattern) == pattern and opponent_subboard & (
            1 << 8 - missingindex
        ) == 0:
            score += 1
    return score


@functools.lru_cache
def evaluate_board(board: tuple[int, int], token: int):
    evaluation = 0
    overall_x = 0
    overall_o = 0

    cw = check_win(board)
    if cw:
        return token * 100_000_000 * cw

    for i in range(9):
        x_sb, o_sb = get_subboard(board, i)
        evaluation += score_subboard(x_sb, o_sb) * SUBBOARD_NEAR_WIN_WEIGHT
        evaluation -= score_subboard(o_sb, x_sb) * SUBBOARD_NEAR_WIN_WEIGHT

        if subboard_has_win(x_sb):
            evaluation += SUBBOARD_WIN_WEIGHT
            overall_x = overall_x | (1 << (8 - i))
        elif subboard_has_win(o_sb):
            evaluation -= SUBBOARD_WIN_WEIGHT
            overall_o = overall_o | (1 << (8 - i))

    evaluation += score_subboard(overall_x, overall_o) * OVERALL_NEAR_WIN_WEIGHT
    evaluation -= score_subboard(overall_o, overall_x) * OVERALL_NEAR_WIN_WEIGHT

    return evaluation * token


@functools.lru_cache
def negamax_alphabeta(
    board: tuple[int, int], subboard: int, token: int, alpha: int, beta: int, depth: int
):
    if depth == 0 or check_win(board) != 0:
        return (evaluate_board(board, token), -1)

    moves = find_moves(board, subboard)
    # if moves == []:
    #     print(board, subboard, token, alpha, beta, depth)
    assert moves != [], "This should have been unreachable, what have I done"

    value = -100_000_000_000
    bestmove = -1
    for move in moves:
        recur_score, _ = negamax_alphabeta(
            place_token(board, move, token),
            move % 9,
            -token,
            -beta,
            -alpha,
            depth - 1,
        )

        if -recur_score > value:
            value = -recur_score
            bestmove = move

        alpha = max(alpha, value)
        if alpha >= beta:
            break

    return (value, bestmove)


def find_best_move(board: tuple[int, int], subboard: int, token: int, depth: int):
    return negamax_alphabeta(board, subboard, token, -100000, 100000, depth)[1]
