"""Tic-tac-toe server: waits for two players, then referees the game.

Usage:  python ttt_server.py [host] [port]
Default: 127.0.0.1 5555
"""
import socket
import sys
from functools import lru_cache

WIN_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
             (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
             (0, 4, 8), (2, 4, 6)]              # diagonals


def send(f, message):
    """Send one line of text to a player."""
    f.write(message + "\n")
    f.flush()


def winner_of(board):
    for a, b, c in WIN_LINES:
        if board[a] != "-" and board[a] == board[b] == board[c]:
            return board[a]
    return None


@lru_cache(maxsize=None)
def can_anyone_win(board, turn):
    """True if SOME sequence of legal moves from this position ends in a win
    (however badly or cooperatively the players play). `board` is a 9-char
    string and `turn` is whose move it is. If this is False, the game is
    already a guaranteed draw."""
    if winner_of(board):
        return True
    if "-" not in board:
        return False
    next_turn = "O" if turn == "X" else "X"
    for i, cell in enumerate(board):
        if cell == "-":
            if can_anyone_win(board[:i] + turn + board[i + 1:], next_turn):
                return True
    return False


def play(players):
    """players is a dict: {'X': file, 'O': file}"""
    board = ["-"] * 9
    turn = "X"

    for symbol, f in players.items():
        send(f, f"WELCOME {symbol}")
    for f in players.values():
        send(f, "BOARD " + "".join(board))

    while True:
        other = "O" if turn == "X" else "X"
        send(players[turn], "YOUR_TURN")
        send(players[other], "WAIT")

        # Keep asking until the current player sends a legal move.
        while True:
            line = players[turn].readline()
            if not line:
                raise ConnectionError(f"Player {turn} disconnected")
            parts = line.split()
            if len(parts) != 2 or parts[0] != "MOVE":
                send(players[turn], "INVALID Send a number from 1 to 9.")
                continue
            if not parts[1].isdigit() or not 1 <= int(parts[1]) <= 9:
                send(players[turn], "INVALID Pick a number from 1 to 9.")
                continue
            index = int(parts[1]) - 1
            if board[index] != "-":
                send(players[turn], "INVALID That square is taken.")
                continue
            break

        board[index] = turn
        for f in players.values():
            send(f, "BOARD " + "".join(board))

        win = winner_of(board)
        if win:
            for f in players.values():
                send(f, f"WIN {win}")
            return
        if "-" not in board:
            for f in players.values():
                send(f, "DRAW full")
            return
        if not can_anyone_win("".join(board), other):
            # Every possible continuation ends in a draw, so stop now.
            for f in players.values():
                send(f, "DRAW locked")
            return
        turn = other


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(2)
    print(f"Server listening on {host}:{port}. Waiting for 2 players...")

    conns, files = [], []
    for symbol in ("X", "O"):
        conn, addr = server.accept()
        print(f"Player {symbol} connected from {addr}")
        conns.append(conn)
        # makefile lets us read/write whole lines instead of raw bytes
        files.append(conn.makefile("rw", encoding="utf-8", newline="\n"))
        if symbol == "X":
            send(files[0], "INFO Connected. Waiting for an opponent...")

    players = {"X": files[0], "O": files[1]}
    try:
        play(players)
        print("Game finished.")
    except (ConnectionError, OSError, ValueError) as e:
        print("Game ended early:", e)
        for f in files:
            try:
                send(f, "OPPONENT_LEFT")
            except (OSError, ValueError):
                pass
    finally:
        for c in conns:
            c.close()
        server.close()


if __name__ == "__main__":
    main()
