from __future__ import annotations
# ↑ Permet d'utiliser les annotations de type de manière "paresseuse" (évaluées comme
#   des chaînes de caractères). Cela permet par exemple d'écrire "chess.Board" comme
#   type dans une fonction sans que Python n'ait besoin de résoudre ce type immédiatement.
 
import chess, chess.svg
# ↑ "chess" est la bibliothèque qui gère toute la logique du jeu d'échecs :
#   représentation du plateau, règles, coups légaux, détection d'échec/mat, etc.
#   "chess.svg" permet de générer une image du plateau au format SVG (image vectorielle).
 
from cairosvg import svg2png
# ↑ cairosvg est une bibliothèque qui convertit des images SVG en PNG.
#   On en a besoin car pygame ne sait pas afficher du SVG directement,
#   donc on convertit d'abord le plateau (SVG) en image PNG affichable.
 
import io
# ↑ Module standard pour manipuler des flux de données en mémoire (au lieu de fichiers
#   sur le disque). On l'utilise pour charger l'image PNG générée directement en mémoire.
 
import pygame
# ↑ Bibliothèque graphique qui permet de créer une fenêtre, dessiner des images,
#   et gérer les entrées utilisateur (clics de souris, clavier, etc.)
 
from pygame.locals import QUIT, MOUSEBUTTONUP
# ↑ Constantes d'événements pygame :
#   - QUIT : l'utilisateur a fermé la fenêtre (clic sur la croix)
#   - MOUSEBUTTONUP : l'utilisateur a relâché un bouton de la souris
 
import math
# ↑ Module mathématique standard : on l'utilise pour math.inf (infini), qui sert
#   de valeur de départ pour alpha (-inf) et beta (+inf).
 
import random
# ↑ Module pour générer des nombres aléatoires. On l'utilise encore un peu ici :
#   pour départager plusieurs coups qui ont exactement le même score, afin que
#   l'IA ne joue pas toujours le même coup dans une position donnée.
 
 
# ------------------------------------------------------------------
# Valeurs classiques des pièces (en "points de pion"), utilisées pour
# l'évaluation matérielle. Le roi n'a pas de valeur ici car il n'est
# jamais "gagné" : sa capture équivaut à une fin de partie, déjà gérée
# séparément par board.is_game_over().
# ------------------------------------------------------------------
PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.2,   # légèrement > cavalier, heuristique classique
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}
 
 
def evaluat(board: chess.Board) -> float:
    """
    Fonction d'évaluation d'une position d'échecs.
    Retourne un score numérique :
        - positif => avantage pour les BLANCS
        - négatif => avantage pour les NOIRS
        - 0       => position équilibrée (ou nulle)
    """
    # 1) Fin de partie : on retourne une valeur "extrême" (et non pas juste ±1)
    #    pour que le minimax préfère toujours un mat immédiat à un simple
    #    avantage matériel, quelle que soit la profondeur explorée.
    if board.is_game_over():
        outcome = board.outcome()
 
        if outcome.winner is None:
            # Partie nulle (pat, répétition, matériel insuffisant, 50 coups...)
            return 0.0
 
        # chess.WHITE == True, chess.BLACK == False
        return 1000.0 if outcome.winner == chess.WHITE else -1000.0
 
    score = 0.0
 
    # 2) Score matériel : on parcourt les 64 cases, et pour chaque pièce trouvée
    #    on ajoute sa valeur (si blanche) ou on la soustrait (si noire).
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        value = PIECE_VALUES[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value
        else:
            score -= value
 
    # 3) Petit bonus de mobilité : plus un camp a de coups légaux disponibles,
    #    plus sa position est jugée "active". On ne calcule la mobilité que
    #    pour le camp au trait (calculer les deux coûterait cher : il faudrait
    #    inverser board.turn artificiellement). C'est une approximation simple
    #    mais efficace pour un projet pédagogique.
    mobility = len(list(board.legal_moves)) * 0.01
    if board.turn == chess.WHITE:
        score += mobility
    else:
        score -= mobility
 
    return score
 
 
# Modifier à partir d'ici
# ########################################################
 
# Profondeur de recherche : nombre de "demi-coups" (plis) explorés.
# Plus c'est grand, plus l'IA est forte mais lente. 3 ou 4 est un bon
# compromis pour une fonction d'évaluation simple comme celle-ci.
SEARCH_DEPTH = 3
 
 
def alphabeta(board: chess.Board, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Cœur de l'algorithme : explore récursivement l'arbre des coups possibles
    et retourne le score de la position `board`, en supposant que chaque
    camp joue optimalement, avec élagage alpha-bêta.
 
    Paramètres :
        board       : la position à évaluer
        depth       : nombre de plis restant à explorer avant de s'arrêter
        alpha       : meilleur score déjà garanti pour le MAXIMISEUR (blancs)
        beta        : meilleur score déjà garanti pour le MINIMISEUR (noirs)
        maximizing  : True si c'est au tour du joueur qui maximise (Blancs)
 
    Retour :
        float : le score de la position, du point de vue "score absolu"
                (positif = bon pour les Blancs), comme evaluat().
    """
    # Cas de base : profondeur atteinte ou partie terminée => on évalue directement
    if depth == 0 or board.is_game_over():
        return evaluat(board)
 
    legal_moves = list(board.legal_moves)
 
    if maximizing:
        # Le joueur Blanc cherche à MAXIMISER le score
        best_value = -math.inf
        for move in legal_moves:
            board.push(move)                     # on joue le coup temporairement
            value = alphabeta(board, depth - 1, alpha, beta, False)
            board.pop()                          # on annule le coup (retour en arrière)
 
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
 
            if alpha >= beta:
                # Coupure bêta : le joueur MIN, plus haut dans l'arbre, a déjà
                # une meilleure alternative ailleurs. Il n'ira jamais choisir
                # cette branche, donc inutile de continuer à l'explorer.
                break
 
        return best_value
    else:
        # Le joueur Noir cherche à MINIMISER le score
        best_value = math.inf
        for move in legal_moves:
            board.push(move)
            value = alphabeta(board, depth - 1, alpha, beta, True)
            board.pop()
 
            best_value = min(best_value, value)
            beta = min(beta, best_value)
 
            if alpha >= beta:
                # Coupure alpha : symétrique du cas précédent.
                break
 
        return best_value
 
 
def searchBestMove(board: chess.Board) -> chess.Move:
    """ Cette fonction prend en paramêtre l'échiquier actuel.
        Elle retourne le meilleur coup à jouer, trouvé via alpha-bêta.
    """
    legal_moves = list(board.legal_moves)
 
    # On maximise si c'est aux Blancs de jouer, sinon on minimise.
    maximizing_root = board.turn == chess.WHITE
 
    best_moves = []
    best_value = -math.inf if maximizing_root else math.inf
 
    alpha = -math.inf
    beta = math.inf
 
    for move in legal_moves:
        board.push(move)
        # Depuis la racine, on appelle alphabeta pour le camp ADVERSE
        # (c'est lui qui répond après notre coup), profondeur - 1.
        value = alphabeta(board, SEARCH_DEPTH - 1, alpha, beta, not maximizing_root)
        board.pop()
 
        if maximizing_root:
            if value > best_value:
                best_value = value
                best_moves = [move]
                alpha = max(alpha, best_value)
            elif value == best_value:
                best_moves.append(move)
        else:
            if value < best_value:
                best_value = value
                best_moves = [move]
                beta = min(beta, best_value)
            elif value == best_value:
                best_moves.append(move)
 
    # S'il y a plusieurs coups ex-aequo (même score), on en choisit un au
    # hasard parmi eux, pour éviter que l'IA soit parfaitement prévisible.
    return best_moves[random.randrange(0, len(best_moves))]
 
 
# Jusqu'ici.
# Vous ne devez RIEN modifier dans la suite de ce code ...
# ########################################################
if __name__ == "__main__":
    # Ce bloc ne s'exécute que si on lance CE fichier directement
    # (et non si on l'importe depuis un autre fichier Python).
 
    SCREEN_SIZE = 768
    # ↑ Taille de la fenêtre en pixels (largeur = hauteur = 768, fenêtre carrée)
 
    SQUARE_SIZE = SCREEN_SIZE // 8
    # ↑ Taille d'une case de l'échiquier en pixels.
    #   Un échiquier fait 8x8 cases, donc on divise la taille totale par 8.
    #   L'opérateur // fait une division entière (sans virgule).
 
    # Initialiser le chess board
    board = chess.Board()
    # ↑ Crée un nouvel échiquier avec la position de départ standard des échecs.
 
    # Initialiser pygame et le jeu
    pygame.init()
    # ↑ Initialise tous les modules internes de pygame (obligatoire avant toute utilisation)
 
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    # ↑ Crée la fenêtre d'affichage de taille SCREEN_SIZE x SCREEN_SIZE.
    #   "screen" est la surface sur laquelle on va dessiner le plateau.
 
    pygame.display.set_caption('Jeu d\'echecs')
    # ↑ Définit le titre affiché dans la barre de la fenêtre.
 
    font = pygame.font.Font(None, 56)
    # ↑ Charge une police d'écriture par défaut (None = police système par défaut)
    #   avec une taille de 56 pixels, utilisée pour afficher le message de fin de partie.
 
    # Boucle principale du jeu
    player_turn = True
    # ↑ Booléen qui indique si c'est le tour du joueur humain (True) ou de la machine (False).
    #   On considère ici que le joueur humain joue les Blancs (qui commencent).
 
    lastMove = None
    # ↑ Mémorise le dernier coup joué (pour le surligner visuellement sur le plateau)
 
    selected_square = None
    # ↑ Mémorise la case actuellement sélectionnée par le joueur (None = aucune sélection)
 
    fill_squares = {}
    # ↑ Dictionnaire {case: couleur} utilisé pour surligner certaines cases
    #   (case sélectionnée, coups possibles depuis cette case, etc.)
 
    while True:
        # ============================================================
        # BOUCLE PRINCIPALE DU JEU (tourne indéfiniment jusqu'à fermeture)
        # ============================================================
 
        # --- Tour de la machine (IA) ---
        # Si ce n'est pas le tour du joueur humain ET que la partie n'est pas terminée,
        # alors on demande à l'IA de choisir et jouer un coup.
        if not player_turn and not board.is_game_over():
            lastMove = searchBestMove(board)
            # ↑ Appelle la fonction qui doit retourner le "meilleur" coup selon l'IA
            board.push(lastMove)
            # ↑ Joue ce coup sur le plateau (met à jour l'état du jeu)
            player_turn = not player_turn
            # ↑ Inverse le tour : redonne la main au joueur humain
 
        # --- Traitement des événements utilisateur (souris, fermeture fenêtre...) ---
        for event in pygame.event.get():
            # pygame.event.get() renvoie la liste de tous les événements survenus
            # depuis le dernier appel (clics, touches clavier, fermeture, etc.)
 
            if event.type == QUIT:
                # L'utilisateur a cliqué sur la croix pour fermer la fenêtre
                pygame.quit()   # Ferme proprement pygame
                exit(0)         # Termine le programme
 
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                # L'utilisateur a relâché le clic GAUCHE de la souris (button == 1)
 
                # On convertit la position en pixels (event.pos) en coordonnées de case
                # sur l'échiquier (colonne, rangée), chaque case faisant SQUARE_SIZE pixels.
                col = event.pos[0] // SQUARE_SIZE
                # ↑ Colonne = position horizontale du clic divisée par la taille d'une case
 
                row = 7 - event.pos[1] // SQUARE_SIZE
                # ↑ Rangée = on inverse l'axe vertical car dans pygame, y=0 est en HAUT
                #   de l'écran, alors que sur un échiquier, la rangée 0 (rang 1) est en BAS.
                #   D'où le "7 - ..." pour retourner l'axe.
 
                square = chess.square(col, row)
                # ↑ Convertit (colonne, rangée) en un identifiant de case "chess"
                #   (un entier de 0 à 63 représentant une case précise, ex: a1, e4, etc.)
 
                # --- Cas 1 : une case était déjà sélectionnée (2e clic = destination) ---
                if selected_square is not None:
                    # On construit le coup : de la case sélectionnée vers la case cliquée
                    move = chess.Move(selected_square, square)
 
                    if move in board.legal_moves:
                        # Le coup est légal : on le joue réellement sur le plateau
                        board.push(move)
                        lastMove = move
                        player_turn = not player_turn
                        # ↑ On passe la main à l'adversaire (l'IA, dans ce cas)
                        square = None
                        # ↑ On "consomme" la case cliquée pour ne pas la re-sélectionner
                        #   juste après (voir le "if square is not None" plus bas)
 
                    # Qu'on ait joué un coup valide ou non, on désélectionne tout
                    # et on efface les surlignages
                    selected_square = None
                    fill_squares = {}
 
                # --- Cas 2 : aucune case n'était sélectionnée (1er clic = origine) ---
                if square is not None and selected_square is None:
                    # On vérifie qu'il y a bien une pièce sur la case cliquée
                    # ET que cette pièce appartient au joueur dont c'est le tour
                    if board.piece_at(square) is not None and board.piece_at(square).color == board.turn:
 
                        # On calcule toutes les cases où cette pièce peut légalement aller,
                        # et on les met en surbrillance avec une couleur bleu clair semi-transparente.
                        fill_squares = dict.fromkeys(
                            (m.to_square for m in board.legal_moves if m.from_square == square),
                            '#0088ff55'  # couleur hexadécimale + canal alpha (transparence)
                        )
 
                        if fill_squares:
                            # S'il existe au moins un coup légal depuis cette case,
                            # on la retient comme "case sélectionnée"
                            selected_square = square
                            # Et on la surligne elle-même avec une couleur pleine (opaque)
                            fill_squares[int(square)] = '#0088ff'
 
        # ============================================================
        # AFFICHAGE DU PLATEAU
        # ============================================================
 
        # Génère une représentation SVG (image vectorielle) du plateau actuel,
        # avec le dernier coup surligné (lastmove) et les cases spéciales (fill)
        svg_data = chess.svg.board(board=board, size=SCREEN_SIZE, lastmove=lastMove, fill=fill_squares)
 
        # Convertit ce SVG en image PNG (bytes) car pygame ne lit pas le SVG nativement
        png_data = svg2png(bytestring=svg_data)
 
        # Charge cette image PNG (en mémoire, via io.BytesIO) comme une surface pygame,
        # et active le canal alpha (transparence) avec convert_alpha()
        chessboard_img = pygame.image.load(io.BytesIO(png_data)).convert_alpha()
 
        # Dessine cette image du plateau sur l'écran, à la position (0, 0) = coin haut-gauche
        screen.blit(chessboard_img, (0, 0))
 
        # ============================================================
        # AFFICHAGE DU MESSAGE DE FIN DE PARTIE (si applicable)
        # ============================================================
        if board.is_game_over():
            game_result = board.outcome()
            # ↑ Récupère les infos sur l'issue de la partie
 
            # Construit le texte à afficher selon le résultat
            text = "Partie nulle" if game_result.winner is None else (
                "Les blancs gagnent" if game_result.winner else "Les noirs gagnent"
            )
 
            # Transforme ce texte en une image (surface pygame) avec la police définie plus haut,
            # en couleur rouge (255, 0, 0), avec anti-aliasing activé (True)
            text = font.render(f"Fin de jeu: {text}", True, (255, 0, 0))
 
            # Calcule le rectangle englobant ce texte, centré au milieu de l'écran
            text_rect = text.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE // 2))
 
            # Crée un rectangle de fond blanc légèrement plus grand que le texte
            # (marge de 10 pixels de chaque côté) pour que le texte soit bien lisible
            background_rect = pygame.Rect(
                text_rect.left - 10, text_rect.top - 10,
                text_rect.width + 20, text_rect.height + 20
            )
 
            # Dessine ce rectangle blanc puis le texte par-dessus
            pygame.draw.rect(screen, (255, 255, 255), background_rect)
            screen.blit(text, text_rect)
 
        # Met à jour réellement l'affichage à l'écran
        # (jusqu'ici, tout était dessiné "en mémoire" sur la surface screen)
        pygame.display.flip()
 
        # Petite pause de 50 millisecondes pour ne pas surcharger le processeur
        # en boucle infinie, et limiter grossièrement la fréquence de rafraîchissement
        pygame.time.wait(50)
 