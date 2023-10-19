import argparse
import engine
import rust_engine
import random
import time
from tqdm import tqdm

PRINT_STUFF = True
USE_RUST = True
DEPTH = 7


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
        print_w("-" * 25)
        for row in range(0, 9, 3):
            print_w("| ", end="")
            for board in board_group:
                print_w(" ".join(list(board[row : row + 3])), end=" | ")
            print_w()
    print_w("-" * 25)


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
    parser.add_argument(
        "-t", "--time", help="Print the total time", action="store_true"
    )
    parser.add_argument(
        "-q", "--disable-print", help="Disable most printing", action="store_true"
    )
    parser.add_argument(
        "-c", "--test", help="Run a certain number of random games and print stats"
    )
    parser.add_argument(
        "-y",
        "--pure-python",
        help="Use the pure Python version of the engine",
        action="store_true",
    )

    return parser.parse_args()


def print_w(*args, **kwargs):
    if PRINT_STUFF:
        print(*args, **kwargs)


def run_tests(num_games: int):
    starttime = time.time()
    wins = [0, 0, 0]
    for _ in tqdm(range(num_games)):
        board = 0, 0, 0, 0
        lastmove = 40
        token = 1
        AI_up = True

        while True:
            if AI_up:
                if USE_RUST:
                    nextmove = rust_engine.find_best_move(  # type: ignore
                        board, lastmove % 9, token, DEPTH
                    )
                else:
                    nextmove = engine.find_best_move(board, lastmove % 9, token, DEPTH)
            else:
                nextmove = random.choice(engine.find_move_list(board, lastmove % 9))

            board = engine.place_token(board, nextmove, token)
            lastmove = nextmove
            token = -token
            AI_up = not AI_up

            cw = engine.check_win(board)
            if cw:
                wins[cw] += 1
                break

            if engine.check_draw(board):
                wins[0] += 1
                break
    print(f"AI wins: {wins[1]}\nRandom wins: {wins[-1]}\nDraws: {wins[0]}")
    print(f"Time: {time.time() - starttime:.4g}s")


# TODO: make main much less hideous
def main():
    global PRINT_STUFF, DEPTH, USE_RUST
    starttime = time.time()
    args = parse_args()
    board = str_to_bitboard(args.board)
    premove = int(args.premove)
    subboard = premove % 9
    depth = int(args.depth)
    token = 1 if args.board.count("X") == args.board.count("O") else -1
    current_move = premove
    PRINT_STUFF = not args.disable_print
    DEPTH = depth
    USE_RUST = not args.pure_python

    if not (args.play_game or args.random_game or args.play_self or args.test):
        if USE_RUST:
            bestmove = rust_engine.find_best_move(board, subboard, token, depth)  # type: ignore
        else:
            bestmove = engine.find_best_move(board, subboard, token, depth)
        board = engine.place_token(board, bestmove, token)
        subboard = bestmove % 9

        pretty_print(annotate_board(board, bestmove, subboard))
        print_w(f"\nNext Moves: {engine.find_move_list(board, subboard)}")
        print(f"AI Plays: {bestmove}")

        if args.output:
            with open(args.output, "w") as f:
                f.write(f"{bitboard_to_str(board)} {current_move} \n")
        if args.time:
            print(f"Time: {time.time() - starttime:.4g}s")
        return

    if args.test:
        run_tests(int(args.test))
        return

    if args.output:
        open(args.output, "w").close()

    AI_up = True
    while True:
        pretty_print(annotate_board(board, current_move, subboard))
        if args.output:
            with open(args.output, "a") as f:
                f.write(f"{bitboard_to_str(board)} {current_move} \n")

        cw = engine.check_win(board)
        if cw:
            print(f"{['X', 'O'][cw==-1]} wins!")
            break

        if engine.check_draw(board):
            print("Draw!")
            break

        if AI_up or args.play_self:
            if USE_RUST:
                nextmove = rust_engine.find_best_move(board, subboard, token, depth)  # type: ignore
            else:
                nextmove = engine.find_best_move(board, subboard, token, depth)
            print_w(f"\nAI {['X', 'O'][token==-1]} Plays: {nextmove}")
            AI_up = False

        elif args.random_game:
            nextmove = random.choice(engine.find_move_list(board, subboard))
            print_w(f"\nRandom {['X', 'O'][token==-1]} plays {nextmove}")
            AI_up = True

        else:
            while True:
                print_w(f"\nMoves: {engine.find_move_list(board, subboard)}")
                nextmove = int(input(f"Player {['X', 'O'][token==-1]}: "))
                if nextmove not in engine.find_move_list(board, subboard):
                    print_w("Invalid move, try again")
                else:
                    break
            AI_up = True

        board = engine.place_token(board, nextmove, token)
        current_move = nextmove
        token = -token
        subboard = nextmove % 9

    if args.time:
        print(f"Time: {time.time() - starttime:.4g}s")


if __name__ == "__main__":
    main()
