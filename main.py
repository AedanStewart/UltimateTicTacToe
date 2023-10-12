import argparse
import engine
import random


def str_to_bitboard(board: str):
    x_board, o_board, x_wins, o_wins = 0, 0, 0, 0
    for i, token in enumerate(board):
        if token == "X":
            x_board = engine.place_index(x_board, i)
        elif token == "O":
            o_board = engine.place_index(o_board, i)
    for i in range(9):
        subboard = engine.get_subboard((x_board, o_board, 0, 0), i)
        x_wins |= engine.subboard_has_win(subboard[0]) << (8 - i)
        o_wins |= engine.subboard_has_win(subboard[1]) << (8 - i)
    return (x_board, o_board, x_wins, o_wins)


def bitboard_to_str(board: tuple[int, int, int, int]):
    x_board, o_board, _, _ = board
    board_str = ""
    for i in range(81):
        if engine.get_index(x_board, i):
            board_str += "X"
        elif engine.get_index(o_board, i):
            board_str += "O"
        else:
            board_str += "."
    return board_str


def pretty_print(board: str):
    sub_boards = [board[i : i + 9] for i in range(0, 81, 9)]
    for start in range(0, 9, 3):
        board_group = sub_boards[start : start + 3]
        print("-" * 25)
        for row in range(0, 9, 3):
            print("| ", end="")
            for board in board_group:
                print(" ".join(list(board[row : row + 3])), end=" | ")
            print()
    print("-" * 25)


def annotate_board(board: tuple[int, int, int, int], move: int, subboard: int):
    lst_board = list(bitboard_to_str(board).lower().replace(".", "-"))
    moves = engine.find_move_list(board, subboard)
    for i in moves:
        lst_board[i] = "."
    lst_board[move] = lst_board[move].upper()
    return "".join(lst_board)


def parse_args():
    parser = argparse.ArgumentParser(description="Ultimate Tic Tac Toe AI")
    parser.add_argument(
        "board",
        help="The board to parse, empty board if omitted",
        default="-" * 81,
        nargs="?",
    )
    parser.add_argument(
        "premove",
        help="The previous move, needed if board is provided",
        default=40,
        nargs="?",
    )
    parser.add_argument(
        "-d", "--depth", help="The depth to search to, defaults to 7", default=7
    )
    parser.add_argument(
        "-p", "--play-game", help="Play a game against the AI", action="store_true"
    )
    parser.add_argument(
        "-r", "--random-game", help="Play the AI against random", action="store_true"
    )
    parser.add_argument(
        "-s", "--play-self", help="Play the AI against itself", action="store_true"
    )
    parser.add_argument(
        "-o", "--output", help="Write printed boards to a file", default=""
    )

    return parser.parse_args()


def main():
    args = parse_args()
    board = str_to_bitboard(args.board)
    premove = int(args.premove)
    subboard = premove % 9
    depth = int(args.depth)
    token = 1 if args.board[int(args.premove)] == "O" else -1
    current_move = premove

    if not (args.play_game or args.random_game or args.play_self):
        bestmove = engine.find_best_move(board, subboard, token, depth)
        board = engine.place_token(board, bestmove, token)
        subboard = bestmove % 9

        pretty_print(annotate_board(board, bestmove, subboard))
        print(f"\nNext Moves: {engine.find_move_list(board, subboard)}")
        print(f"AI Plays: {bestmove}")

        if args.output:
            with open(args.output, "w") as f:
                f.write(bitboard_to_str(board))
        return

    if args.output:
        open(args.output, "w").close()

    AI_up = True
    while True:
        pretty_print(annotate_board(board, current_move, subboard))
        if args.output:
            with open(args.output, "a") as f:
                f.write(bitboard_to_str(board) + "\n")

        cw = engine.check_win(board)
        if cw:
            print(f"{['X', 'O'][cw==-1]} wins!")
            return

        if AI_up or args.play_self:
            nextmove = engine.find_best_move(board, subboard, token, depth)
            print(f"\nAI {['X', 'O'][token==-1]} Plays: {nextmove}")
            AI_up = False

        elif args.random_game:
            nextmove = random.choice(engine.find_move_list(board, subboard))
            print(f"\nRandom {['X', 'O'][token==-1]} plays {nextmove}")
            AI_up = True

        else:
            while True:
                print(f"\nMoves: {engine.find_move_list(board, subboard)}")
                nextmove = int(input(f"Player {['X', 'O'][token==-1]}: "))
                if nextmove not in engine.find_move_list(board, subboard):
                    print("Invalid move, try again")
                else:
                    break
            AI_up = True

        board = engine.place_token(board, nextmove, token)
        current_move = nextmove
        token = -token
        subboard = nextmove % 9


if __name__ == "__main__":
    main()
