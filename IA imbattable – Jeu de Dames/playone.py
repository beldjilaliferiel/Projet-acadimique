import pygame
from game.game import Game
from game.utilities import BLACK_PIECE, RED_PIECE
from mcts_classic import MCTSClassic

def run_single_game(iterations):
    pygame.init()

    game = Game(
        width=720,
        height=720,
        mcts_player=BLACK_PIECE,
        mcts_iterations=iterations
    )

    # Désactiver l'IA intégrée SANS changer mcts_player
    game._ai_disabled = True

    classic_ai = MCTSClassic(game)

    move_count = 0
    max_moves = 200

    while not game.winner and move_count < max_moves:

        if game.turn == BLACK_PIECE:
            best = game.mcts_search(game.board, iterations)
        else:
            best = classic_ai.mcts_search_classic(game.board, iterations)

        if best is None:
            break

        piece, mv = best
        game.board = game.make_move(game.board, mv, piece[0], piece[1])
        game.move_count += 1

        next_turn = game._opponent(game.turn)
        if game.check_winner(game.board, next_turn):
            game.winner = game.turn
            break

        if game.move_count >= 100:
            game.winner = "draw"
            break

        game.turn = game._opponent(game.turn)
        move_count += 1

    if game.winner == "draw" or move_count >= max_moves:
        return "draw"
    elif game.winner == BLACK_PIECE:
        return "black"
    else:
        return "red"


if __name__ == "__main__":
    iterations = int(input("Nombre de simulations : "))
    print(f"\nPartie avec {iterations} simulations...")
    result = run_single_game(iterations)
    print(f"Résultat : {result} wins")