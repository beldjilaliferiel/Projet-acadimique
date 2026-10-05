import pygame
import random
import math
from game.utilities import *
pygame.font.init()
 
 
class MCTSNode:#Cette classe représente un nœud dans l’arbre du MCTS
    #Chaque node = position du jeu et chaque enfant = coup possible 
    def __init__(self, board, turn, parent=None, move=None):
        #constructeur    
        self.board = board#board:etat plateau
        self.turn = turn#turn:red or black
        self.parent = parent#parent:node parent dou on vient
        self.move = move#move:coup qui a mene a ce node
        self.children = []#liste des coups possibles explorés
        self.wins = 0#combien de fois il a mené à une bonne position
        self.visits = 0#combien de fois ce nœud a été exploré
        self.untried_moves = None#coups pas encore testés
 
    def uct_value(self, c=1.41):#formule du MCTS C pour equilibrer entre l exploration et exploitation
        if self.visits == 0:#si jamais exploré priorité maximale et forcer l’exploration
            return float('inf')
        return (self.wins / self.visits) + c * math.sqrt(math.log(self.parent.visits) / self.visits)
        #(self.wins / self.visits) Exploitation 
        #c * sqrt(log(parent.visits) / self.visits) Exploration : favorise les nœuds peu visités pour tester de nouvelles idées

    def best_child(self, c=1.41):#choisir le meilleur enfant selon UCT
        return max(self.children, key=lambda ch: ch.uct_value(c))
        #pour chaque enfant ch calcule uct_value et prendre le max
         
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0#vérifier si tous les coups sont testés
 
    #Créer des nœuds(positions du jeu)
    #Stocker stats (wins / visits)
    #Calculer UCT
    #Choisir le meilleur coup
 
class Game:
    def __init__(self, width=720, height=720, mcts_player=BLACK_PIECE, mcts_iterations=800):
        #Initialise tout le jeu taille fenetre plateau joueur ia parametre mcts
        #Paramètres du jeu
        self.n_squares   = 8#plateau 8×8
        self.board       = self.create_board()#crée le plateau initial (pions placés)
        self.turn        = RED_PIECE#joueur qui commence (rouge)
        self.winner      = None#pas encore de gagnant
        #Interaction joueur
        self.selected_piece  = None#pièce sélectionnée avec la souris
        self.available_moves = []#mouvements possibles
        self.capture_moves   = []#mouvements de capture uniquement
        self.move_count      = 0#compteur pour éviter parties infinies (draw)
        #Fenêtre graphique (Pygame)
        #dimensions de la fenêtre
        self.width  = width
        self.height = height
        self.window = pygame.display.set_mode((width, height))#crée la fenêtre du jeu
        self.square_size = width // self.n_squares #taille d’une case
        pygame.display.set_caption("Checkers – MCTS")#nom de la fenêtre
        #Texte affichage des rois
        self.font = pygame.font.Font(None, 36)#police
        self.text_black_king = self.font.render("K", True, WHITE)
        #crée le texte "K" pour roi noir(k texte true anti-aliasing joli hhh white couleur)
        self.text_red_king   = self.font.render("K", True, BLACK)
        #crée le texte "K" pour roi rouge
        
        #IA (MCTS)
        self.mcts_player     = mcts_player#quel joueur est contrôlé par l’IA
        self.non_mcts_player = RED_PIECE if mcts_player == BLACK_PIECE else BLACK_PIECE#autre joueur
        self.mcts_iterations = mcts_iterations#nombre de simulations MCTS
        
        #fct initialise 
        #jeu : plateau tour gagnant
        #interaction : selection mouvements
        #interface : fenetre taille cases textes 
        #ia : joueur ia nombre d iterations

    #board
    def create_board(self):#construit le plateau initial
        #crée une grille 8×8 remplie de 0 cases vides underscore : i vrab inutile
        board = [[0] * self.n_squares for _ in range(self.n_squares)]
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                if (r + c) % 2 != 0:#Cases jouables noires
                    #cases noires (r + c) impair
                    if r < 3:#lignes 0,1,2  pions noirs en haut
                        board[r][c] = BLACK_PIECE# acceder a une case r ligne c colonne
                    elif r > 4:#lignes 5,6,7 → pions rouges en bas
                        board[r][c] = RED_PIECE
        return board
    
        #crée une grille vide
        #sélectionne cases noires
        #place les pions : noirs en haut / rouges en bas
 
    #draw 
    def draw_board(self):#affiche tout le jeu a l ecran 
        self.window.fill(WHITE)#efface l’écran et met un fond blanc
        #Dessiner les cases noires
        for r in range(self.n_squares):
            for c in range(self.n_squares):#parcourir la grille
                if (r + c) % 2 != 0:#cases noires
                    #Dessine un carré noir à une position précise dans la fenêtre
                    pygame.draw.rect(self.window, BLACK,
                                     (c * self.square_size, r * self.square_size,
                                      self.square_size, self.square_size))
                    #(où dessiner,couleur du rectangle,(x, y, width, height))
                    #c = colonne (0,1,2...)
                    #square_size = taille d’une case (ex: 90 px) x = 3 * 90 = 270 la case est à 270 pixels à droite
        
        #dessiner les pieces
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                piece = self.board[r][c]
                if piece == 0:#Ignorer les cases vides
                    continue
                #Si une case contient une pièce il dessine un cercle pion au centre de la case
                x = c * self.square_size + self.square_size // 2
                y = r * self.square_size + self.square_size // 2
                rad = self.square_size // 2 - 10
                color = BROWN if piece in (BLACK_PIECE, BLACK_KING) else RED
                pygame.draw.circle(self.window, color, (x, y), rad)
                #Si une case contient une pièce qui est KING il dessine un cercle pion au centre de la case
                if piece == BLACK_KING:
                    self.window.blit(self.text_black_king,
                                     (x - self.text_black_king.get_width() // 2,
                                      y - self.text_black_king.get_height() // 2))
                elif piece == RED_KING:
                    self.window.blit(self.text_red_king,
                                     (x - self.text_red_king.get_width() // 2,
                                      y - self.text_red_king.get_height() // 2))
        #Coups possibles
        for (mr, mc) in self.available_moves:
            #(ligne,colonne)ou le joueur peut jouer
            pygame.draw.circle(self.window, BLUE,
                               #fenere , couleur cercle blue
                               (mc * self.square_size + self.square_size // 2,
                                mr * self.square_size + self.square_size // 2), 15)
                                    #position convertion en pixels 
                                                                    #rayon du cercle
        #Fin de partie                                                            
        if self.winner:#si quelqu un a gagne le jeu affiche “Black wins” “Red wins” ou “Draw”
            self._draw_winner()
        pygame.display.update()
 
    def _draw_winner(self):#afficher le message de fin de partie au centre de l’écran.
        if self.winner == "draw":
            msg = "Draw!"
        elif self.winner == BLACK_PIECE:
            msg = "Black wins!"
        else:
            msg = "Red wins!"

        surf = self.font.render(msg, True, YELLOW)#Créer le texte à afficher
        bg   = pygame.Surface((surf.get_width() + 20, surf.get_height() + 10))
        bg.fill(BLACK)#crée un rectangle noir un peu plus grand que le texte
        self.window.blit(bg, (self.width // 2 - bg.get_width() // 2,
                               self.height // 2 - bg.get_height() // 2))
        #place le rectangle noir exactement au centre de l’écran
        self.window.blit(surf, (self.width // 2 - surf.get_width() // 2,
                                 self.height // 2 - surf.get_height() // 2))
        #Afficher le texte au centre
 
    #moves
    def _opponent(self, turn):#switch de joueur
        return BLACK_PIECE if turn == RED_PIECE else RED_PIECE
 
    def get_available_moves(self, row, col, board, turn):#EVALUATE ajout du paramètre turn vant → utilisait self.turn automatiquement Après → on peut passer le joueur depuis l'extérieur
        #donne seulement toutes les cases où cette pièce peut bouger
        #Depuis cette case, quelles sont les cases où je peux jouer
        #row col position de la piece 
        #board etat du plateau 
        #turn joueur actuel 
        """BUG FIX: turn is now an explicit parameter, not self.turn."""
        piece = board[row][col]#lire la piece actuelle
        moves = []#preparer une liste vide 
        if piece == BLACK_PIECE:#le pion noir peut avancer dans une seule direction vers le bas direction + 1
            moves += self._diagonal_moves(row, col, +1, board, turn)
        elif piece == RED_PIECE:#vers le haut (direction -1)
            moves += self._diagonal_moves(row, col, -1, board, turn)
        elif piece in (BLACK_KING, RED_KING):#dame (king)
            moves += self._diagonal_moves(row, col, +1, board, turn)#vers le haut vers le bas dans les deux sens
            moves += self._diagonal_moves(row, col, -1, board, turn)#vers le haut vers le bas dans les deux sens
        return moves#retourner tous les coups possibles
 
    def _diagonal_moves(self, row, col, direction, board, turn):
        moves = []#liste des coups possibles
        opp   = self._opponent(turn)#le joueur ennemi
        #Tester les 2 diagonales
        for dc in (+1, -1):#diagonale droite ou gauche 
            nr, nc = row + direction, col + dc #on regarde la case juste à côté en diagonale
            #Cas 1 case vide (déplacement simple)
            if self._in_bounds(nr, nc) and board[nr][nc] == 0:
                moves.append((nr, nc))#je peux juste avancer dessus
            #Cas 2 il y a une pièce ennemie (capture)    
            elif self._in_bounds(nr, nc) and board[nr][nc] in (opp, opp + 2):#la case contient un ennemi possible capture
                jr, jc = row + 2 * direction, col + 2 * dc #regarde la case après l’ennemi
                if self._in_bounds(jr, jc) and board[jr][jc] == 0:# Vérifier si on peut sauter pour capturer :la case derrière doit être vide
                    moves.append((jr, jc))
        return moves#renvoie tous les coups possibles
        
        #fct determine si cest un deplacement normal avancer vers une case vide 
        #ou une capture selon la diagonale si ennemi devant + case vide derrière je peux sauter et manger
 
    def _in_bounds(self, r, c):#case existe dans le plateau
        #verifier si une position est valide dans le jeu
        return 0 <= r < self.n_squares and 0 <= c < self.n_squares
 
    def has_capture_moves(self, row, available_moves):#Parmi les coups possibles, lesquels sont des captures
        return [(r, c) for (r, c) in available_moves if abs(r - row) == 2]
        #Elle regarde la liste des mouvements possibles
        #garde uniquement ceux où la pièce saute par-dessus un adversaire
        #déplacement normal = 1 case
        #capture = 2 cases (on saute une pièce)
    def get_all_possible_moves(self, board, turn):
        """Returns dict {piece_pos: [moves]}. Enforces mandatory capture."""
        all_moves = {}
        capture_only = {}
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                if board[r][c] == turn or board[r][c] == turn + 2:
                    mvs = self.get_available_moves(r, c, board, turn)
                    if mvs:
                        all_moves[(r, c)] = mvs
                    caps = self.has_capture_moves(r, mvs)
                    if caps:
                        capture_only[(r, c)] = caps
        # Mandatory capture rule
        return capture_only if capture_only else all_moves
 
    # ------------------------------------------------------------------ UI interaction
    def select(self, row, col):
        if self.winner:
            return
        piece = self.board[row][col]
 
        if self.capture_moves:
            if (row, col) in self.capture_moves:
                self.move(row, col)
            return
 
        if piece != 0 and (piece == self.turn or piece == self.turn + 2):
            self.selected_piece   = (row, col)
            self.available_moves  = self.get_available_moves(row, col, self.board, self.turn)
        elif self.selected_piece:
            self.move(row, col)
 #*******
    def move(self, row, col):
        if (row, col) not in self.available_moves:
            self.selected_piece  = None
            self.available_moves = []
            self.capture_moves   = []
            return
 
        # Clear stale capture state before applying the move
        self.capture_moves = []
 
        sr, sc = self.selected_piece
        self.board[row][col] = self.board[sr][sc]
        self.board[sr][sc]   = 0
 
        # Promotion
        if self.board[row][col] == BLACK_PIECE and row == self.n_squares - 1:
            self.board[row][col] = BLACK_KING
        elif self.board[row][col] == RED_PIECE and row == 0:
            self.board[row][col] = RED_KING
 
        # Capture
        if abs(row - sr) == 2:
            mid_r = sr + (row - sr) // 2
            mid_c = sc + (col - sc) // 2
            self.board[mid_r][mid_c] = 0   # remove captured piece immediately
            self.move_count = 0
 
            # Redraw so captured piece disappears before next input
            self.draw_board()
            pygame.display.update()
 
            # Check multi-jump
            self.selected_piece = (row, col)
            next_moves = self.get_available_moves(row, col, self.board, self.turn)
            next_caps  = self.has_capture_moves(row, next_moves)
            if next_caps:
                self.available_moves = next_caps
                self.capture_moves   = next_caps
                if self.turn == self.mcts_player:
                    self.move(next_caps[0][0], next_caps[0][1])
                return
 
        self.change_turn()
 
    # ------------------------------------------------------------------ turn
    def change_turn(self):
        self.turn            = self._opponent(self.turn)
        self.selected_piece  = None
        self.available_moves = []
        self.capture_moves   = []
        self.move_count     += 1
 
        if self.move_count >= 100:
            self.winner = "draw"
            return
        if self.check_winner(self.board):
            self.winner = self._opponent(self.turn)  # last player to move won
            return
 
        if self.turn == self.mcts_player and not getattr(self, '_ai_disabled', False):
# getattr cherche '_ai_disabled' dans l'objet game
# si la variable n'existe pas (jeu normal) → retourne False par défaut → l'IA joue
# si on l'a mise à True (evaluation.py) → l'IA ne joue pas
# permet de garder le contrôle total des tours dans la boucle d'évaluation
         best = self.mcts_search(self.board, self.mcts_iterations)
         if best:
            piece, mv = best
            self.selected_piece  = piece
            self.available_moves = self.get_available_moves(piece[0], piece[1], self.board, self.turn)
            self.move(mv[0], mv[1])
 
    def check_winner(self, board, current_turn=None):
     # current_turn ajouté pour evaluation.py
    # sans ce paramètre, la fonction utilisait self.turn (tour interne du jeu)
    # avec ce paramètre, on peut vérifier qui perd après chaque coup
    # depuis l'extérieur sans dépendre de l'état interne du jeu
     turn = current_turn if current_turn is not None else self.turn
     red_has_moves   = False
     black_has_moves = False
     has_red = has_black = False

     for r in range(self.n_squares):
        for c in range(self.n_squares):
            p = board[r][c]
            if p in (RED_PIECE, RED_KING):
                has_red = True
                if self.get_available_moves(r, c, board, RED_PIECE):
                    red_has_moves = True
            elif p in (BLACK_PIECE, BLACK_KING):
                has_black = True
                if self.get_available_moves(r, c, board, BLACK_PIECE):
                    black_has_moves = True

     if not has_red or not has_black:
        return True
     if turn == RED_PIECE and not red_has_moves:
        return True
     if turn == BLACK_PIECE and not black_has_moves:
        return True
     return False
 
    # ------------------------------------------------------------------ MCTS
    def make_move(self, board, move, piece_row, piece_col, smart=False):#EVALAUTE Avant → modifiait directement le plateau
#Après → retourne un nouveau plateau sans toucher l'original
     nb = [r[:] for r in board]
     pr, pc = piece_row, piece_col
     mr, mc = move

     nb[mr][mc] = nb[pr][pc]
     nb[pr][pc] = 0

    # Promotion
     if nb[mr][mc] == BLACK_PIECE and mr == self.n_squares - 1:
        nb[mr][mc] = BLACK_KING
     elif nb[mr][mc] == RED_PIECE and mr == 0:
        nb[mr][mc] = RED_KING

    # Capture + multi-jump
     if abs(mr - pr) == 2:
        nb[pr + (mr - pr) // 2][pc + (mc - pc) // 2] = 0
        turn_of_piece = nb[mr][mc] if nb[mr][mc] <= 2 else nb[mr][mc] - 2
        next_mvs  = self.get_available_moves(mr, mc, nb, turn_of_piece)
        next_caps = self.has_capture_moves(mr, next_mvs)
        if next_caps:
            if smart:
                # BUG 3 CORRIGE : choisir intelligemment
                next_caps_dict = {(mr, mc): next_caps}
                _, best_cap = self._smart_random_move(next_caps_dict, nb, turn_of_piece)
                return self.make_move(nb, best_cap, mr, mc, smart=True)
            else:
                return self.make_move(nb, random.choice(next_caps), mr, mc, smart=False)

     return nb#plateau mise ajour
       #déplacer une pièce
       #gérer la promotion en dame
       #supprimer les pièces capturées
       #enchaîner automatiquement les captures (multi-jump)
 
    def mcts_search(self, board, iterations):
     root = MCTSNode(board, self.mcts_player)
     all_moves = self.get_all_possible_moves(board, self.mcts_player)
     root.untried_moves = [(p, m) for p, mvs in all_moves.items() for m in mvs]

     for _ in range(iterations):
        node      = root
        temp_board = [r[:] for r in board]
        temp_turn  = self.mcts_player

        # Selection
        while node.untried_moves == [] and node.children:
            node = node.best_child()
            if node.move:
                p, mv = node.move
                temp_board = self.make_move(temp_board, mv, p[0], p[1])
                temp_turn  = self._opponent(temp_turn)

        # Expansion
        if node.untried_moves:
            chosen = random.choice(node.untried_moves)
            node.untried_moves.remove(chosen)
            p, mv = chosen

            # temp_turn = joueur QUI JOUE ce coup
            # on crée le child avec le tour du joueur qui VIENT DE JOUER
            child = MCTSNode(temp_board, temp_turn, parent=node, move=chosen)

            temp_board = self.make_move(temp_board, mv, p[0], p[1])
            temp_turn  = self._opponent(temp_turn)

            child_moves = self.get_all_possible_moves(temp_board, temp_turn)
            child.untried_moves = [(cp, cm) for cp, cms in child_moves.items() for cm in cms]
            node.children.append(child)
            node = child

        # Simulation
        sim_board = [r[:] for r in temp_board]
        sim_turn  = temp_turn
        depth = 0

        while not self.check_winner(sim_board, sim_turn) and depth < 80:
            sim_moves = self.get_all_possible_moves(sim_board, sim_turn)
            if not sim_moves:
                break
            p, mv = self._smart_random_move(sim_moves, sim_board, sim_turn)
            sim_board = self.make_move(sim_board, mv, p[0], p[1], smart=True)
            sim_turn  = self._opponent(sim_turn)
            depth += 1

        # Backpropagation
        result = self.evaluate_board(sim_board)
        while node is not None:
            node.visits += 1
            if node.turn == self.mcts_player:
                node.wins += result
            else:
                node.wins += (1 - result)
            node = node.parent

     if not root.children:
        return None
     return max(root.children, key=lambda ch: ch.visits).move
 
    def _smart_random_move(self, moves, board, turn):
       # Priority: capture > advance toward promotion > center control
       
        captures = [(p, m) for p, ms in moves.items() for m in ms if abs(m[0] - p[0]) == 2]
        if captures:
            return random.choice(captures)
 
        # Score non-capture moves heuristically
        scored = []
        center = 3.5
        for p, ms in moves.items():
            for m in ms:
                score = 0
                # Advance toward promotion
                if turn == BLACK_PIECE:
                    score += m[0]          # black advances downward
                elif turn == RED_PIECE:
                    score += (7 - m[0])    # red advances upward
                # Center control
                score += 2 - abs(m[1] - center) * 0.5
                # King safety: kings prefer center
                if board[p[0]][p[1]] in (BLACK_KING, RED_KING):
                    score += 1
                scored.append((score, p, m))
 
        # Weighted random from top half
        scored.sort(reverse=True)
        top = scored[:max(1, len(scored) // 2)]
        _, p, m = random.choice(top)
        return p, m
 
    def evaluate_board(self, board):
       #calcule un score pour chaque joueur
        red_score   = 0
        black_score = 0
 
        for r in range(self.n_squares):#all the boxes
            for c in range(self.n_squares):
                p = board[r][c]#recuperer une piece
                if p == 0:
                    continue
                center_bonus = 1.0 - abs(c - 3.5) / 7.0#3.5 = centre exact
                #plus une pièce est proche du centre → c’est mieux 
                #loin du centre → petit score
                #proche du centre → grand score
                #/7 on veut normaliser entre 0 et 1
                if p == RED_PIECE:
                    advance = (7 - r) / 7.0#plus avance best score 
                    red_score   += 10 + 3 * advance + center_bonus#10 valeur pion advance progression centre position 
                    if r == 7:  # back row protection
                        red_score += 1 # defense derniere ligne
                elif p == RED_KING:
                    red_score   += 20 + center_bonus * 2 # king 20 
                elif p == BLACK_PIECE:
                    advance = r / 7.0
                    black_score += 10 + 3 * advance + center_bonus
                    if r == 0:
                        black_score += 1
                elif p == BLACK_KING:
                    black_score += 20 + center_bonus * 2
 
        diff = red_score - black_score
        #diff sup 0 red  inf 0 black equal 0 egalite 
        if self.mcts_player == BLACK_PIECE:
            diff = -diff #score en poinyt de vue de l ia 
 
        # Soft sigmoid mapping to [0, 1]
        return 1 / (1 + math.exp(-diff / 15))#reglage d echelle pour que les score ne soit pas extreme 
        # 0 mauvais etat 0.5 equilibre 1 tres bon etat
    # main loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            self.draw_board()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.winner:
                    if self.turn != self.mcts_player:
                        x, y = pygame.mouse.get_pos()
                        self.select(y // self.square_size, x // self.square_size)
            clock.tick(60)
        pygame.quit()     