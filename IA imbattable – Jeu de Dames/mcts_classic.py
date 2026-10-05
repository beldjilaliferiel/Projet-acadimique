import math
import random
from game.utilities import BLACK_PIECE, RED_PIECE, BLACK_KING, RED_KING

# ============================================================
# MCTS CLASSIQUE (100% aléatoire, sans heuristique)
# ============================================================

class MCTSNodeClassic:
    def __init__(self, board, turn, parent=None, move=None):
        self.board = board
        self.turn = turn
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = None

    def uct_value(self, c=1.41):
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + c * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

    def best_child(self, c=1.41):
        return max(self.children, key=lambda ch: ch.uct_value(c))

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0


class MCTSClassic:
    """
    MCTS Classique = 100% aléatoire
    Pas d'heuristique
    Pas de smart move
    Juste random
    """
    def __init__(self, game):
        self.game = game  # référence au jeu pour utiliser ses fonctions

    def _opponent(self, turn):
        return BLACK_PIECE if turn == RED_PIECE else RED_PIECE

    def simulate_random(self, board, turn):
        """
        Simulation 100% aléatoire jusqu'à la fin de la partie
        Aucune heuristique — just random moves
        """
        sim_board = [r[:] for r in board]
        sim_turn = turn
        depth = 0

        while not self.game.check_winner(sim_board) and depth < 80:
            # Récupérer tous les coups possibles
            sim_moves = self.game.get_all_possible_moves(sim_board, sim_turn)
            
            if not sim_moves:
                break

            # Choisir UN coup complètement au hasard (pas d'heuristique)
            all_options = [
                (p, m) 
                for p, ms in sim_moves.items() 
                for m in ms
            ]
            p, mv = random.choice(all_options)  # 100% ALÉATOIRE

            sim_board = self.game.make_move(sim_board, mv, p[0], p[1])
            sim_turn = self._opponent(sim_turn)
            depth += 1

        return self.evaluate_classic(sim_board)

    def evaluate_classic(self, board):
        """
        Évaluation simple : juste compter les pièces
        Pas de bonus position, pas de centre, pas d'avancement
        Juste : qui a plus de pièces ?
        """
        red_count = 0
        black_count = 0

        for r in range(self.game.n_squares):
            for c in range(self.game.n_squares):
                p = board[r][c]
                if p == RED_PIECE:
                    red_count += 1
                elif p == RED_KING:
                    red_count += 2   # dame vaut 2
                elif p == BLACK_PIECE:
                    black_count += 1
                elif p == BLACK_KING:
                    black_count += 2  # dame vaut 2

        diff = red_count - black_count
        # score entre 0 et 1 du point de vue de RED
        return 1 / (1 + math.exp(-diff / 5))

    def mcts_search_classic(self, board, iterations):
        """
        MCTS classique pour RED
        Même structure que ton MCTS mais simulation 100% aléatoire
        """
        root = MCTSNodeClassic(board, RED_PIECE)
        all_moves = self.game.get_all_possible_moves(board, RED_PIECE)
        root.untried_moves = [
            (p, m) 
            for p, mvs in all_moves.items() 
            for m in mvs
        ]

        for _ in range(iterations):
            node = root
            temp_board = [r[:] for r in board]
            temp_turn = RED_PIECE

            # ---- SELECTION ----
            while node.untried_moves == [] and node.children:
                node = node.best_child()
                if node.move:
                    p, mv = node.move
                    temp_board = self.game.make_move(
                        temp_board, mv, p[0], p[1]
                    )
                    temp_turn = self._opponent(temp_turn)

            # ---- EXPANSION ----
            if node.untried_moves:
                chosen = random.choice(node.untried_moves)
                node.untried_moves.remove(chosen)
                p, mv = chosen
                temp_board = self.game.make_move(
                    temp_board, mv, p[0], p[1]
                )
                temp_turn = self._opponent(temp_turn)

                child = MCTSNodeClassic(
                    temp_board, temp_turn, 
                    parent=node, move=chosen
                )
                child_moves = self.game.get_all_possible_moves(
                    temp_board, temp_turn
                )
                child.untried_moves = [
                    (cp, cm) 
                    for cp, cms in child_moves.items() 
                    for cm in cms
                ]
                node.children.append(child)
                node = child

            # ---- SIMULATION (100% aléatoire) ----
            result = self.simulate_random(temp_board, temp_turn)

            # ---- BACKPROPAGATION ----
            while node is not None:
                node.visits += 1
                node.wins += result
                node = node.parent

        if not root.children:
            return None
        return max(root.children, key=lambda ch: ch.visits).move