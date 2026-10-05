from game.game import Game

def main():
    # Paramètres MCTS:
    # mcts_player: Le joueur contrôlé par MCTS (BLACK_PIECE ou RED_PIECE)
    # mcts_iterations: Nombre de simulations MCTS par coup (plus = meilleur mais plus lent)
    #   - 500-1000: rapide, niveau débutant
    #   - 1000-2000: moyen, bon compromis
    #   - 2000-5000: lent, niveau avancé
    
    game = Game(mcts_iterations=(800)) # Vous pouvez ajuster ce nombre
    game.run()

if __name__ == "__main__":
    main()