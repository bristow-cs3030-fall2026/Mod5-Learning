"""Tic-tac-toe client: connects to the server and lets you play.

Usage:  python ttt_client.py [host] [port]
Default: 127.0.0.1 5555
"""
import socket
import sys


def show_board(cells):
    """Draw the board. Empty squares show their number (1-9)."""
    shown = [c if c != "-" else str(i + 1) for i, c in enumerate(cells)]
    print()
    print(f" {shown[0]} | {shown[1]} | {shown[2]}")
    print("---+---+---")
    print(f" {shown[3]} | {shown[4]} | {shown[5]}")
    print("---+---+---")
    print(f" {shown[6]} | {shown[7]} | {shown[8]}")
    print()


def ask_move(f):
    move = input("Your move (1-9): ").strip()
    f.write(f"MOVE {move}\n")
    f.flush()


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5555

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except OSError as e:
        print(f"Could not connect to {host}:{port} - {e}")
        print("Is the server running?")
        return
    f = sock.makefile("rw", encoding="utf-8", newline="\n")

    me = None
    try:
        while True:
            line = f.readline()
            if not line:
                print("Lost connection to the server.")
                break
            line = line.rstrip("\n")
            command, _, rest = line.partition(" ")

            if command == "WELCOME":
                me = rest
                print(f"You are player {me}.")
            elif command == "INFO":
                print(rest)
            elif command == "BOARD":
                show_board(rest)
            elif command == "WAIT":
                print("Waiting for the other player...")
            elif command == "YOUR_TURN":
                ask_move(f)
            elif command == "INVALID":
                print(rest)
                ask_move(f)          # server is still waiting for a legal move
            elif command == "WIN":
                print("You win! 🎉" if rest == me else "You lose. Better luck next time!")
                break
            elif command == "DRAW":
                if rest == "locked":
                    print("No one can win any more, so it's a draw.")
                else:
                    print("It's a draw.")
                break
            elif command == "OPPONENT_LEFT":
                print("The other player left. Game over.")
                break
    except (KeyboardInterrupt, EOFError):
        print("\nLeaving the game.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
