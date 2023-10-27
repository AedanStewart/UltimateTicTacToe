import rust_engine
import sys

DEPTH = 10
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


def subboard_has_win(subboard: int):
    for pattern in WIN_PATTERNS:
        if (subboard & pattern) == pattern:
            return True
    return False


def get_subboard(board: tuple[int, int, int, int], subboard: int):
    x_board, o_board, _, _ = board
    return (
        (x_board >> (81 - ((subboard + 1) * 9))) & ((1 << 9) - 1),
        (o_board >> (81 - ((subboard + 1) * 9))) & ((1 << 9) - 1),
    )


def str_to_bitboard(board: str):
    x_board, o_board, x_wins, o_wins = 0, 0, 0, 0
    for i, token in enumerate(board):
        if token == "X":
            x_board |= 1 << (80 - i)
        elif token == "O":
            o_board |= 1 << (80 - i)
    for i in range(9):
        subboard = get_subboard((x_board, o_board, 0, 0), i)
        x_wins |= subboard_has_win(subboard[0]) << (8 - i)
        o_wins |= subboard_has_win(subboard[1]) << (8 - i)
    return (x_board, o_board, x_wins, o_wins)


def main():
    args = sys.argv[1:]
    board = str_to_bitboard(args[0])
    previous_move = int(args[1])
    token = 1 if args[0].count("X") == args[0].count("O") else -1
    print(rust_engine.find_best_move(board, previous_move % 9, token, DEPTH))


if __name__ == "__main__":
    main()
