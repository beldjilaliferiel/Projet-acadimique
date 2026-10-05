#matada mada mada
import pygame
import random
import math
from game.utilities import *
pygame.font.init()

# ── Palette ────────────────────────────────────────────────────────────────
CELL        = 80
BOARD_PX    = CELL * 8
PANEL_W     = 220
LABEL_W     = 24          # ← bande gauche pour les numéros de lignes
LABEL_H     = 24          # ← bande basse  pour les numéros de colonnes
WIN_W       = LABEL_W + BOARD_PX + PANEL_W
WIN_H       = BOARD_PX + LABEL_H

C_DARK      = (107, 63,  28)
C_LIGHT     = (232, 217, 180)
C_SELECT    = (181, 201,  90)
C_LEGAL     = (126, 200,  80)
C_CAPTURE   = (224,  80,  80)
C_BG        = ( 44,  44,  44)
C_PANEL     = ( 44,  44,  44)
C_BORDER    = ( 85,  85,  85)
C_TEXT      = (255, 255, 255)
C_SUBTEXT   = (170, 170, 170)
C_ACCENT    = (224, 160,  32)

C_RED_FILL  = (210,  60,  60)
C_RED_RIM   = (140,  20,  20)
C_BLK_FILL  = ( 34,  34,  34)
C_BLK_RIM   = ( 85,  85,  85)
C_SHADOW    = ( 17,  17,  17)

# Couleur des labels de coordonnées (blanc sur fond sombre)
C_LABEL_BG  = ( 30,  30,  30)
C_LABEL_TXT = (220, 220, 220)


class MCTSNode:
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
        return (self.wins / self.visits) + c * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self, c=1.41):
        return max(self.children, key=lambda ch: ch.uct_value(c))

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0


class Game:
    def __init__(self, width=WIN_W, height=WIN_H, mcts_player=BLACK_PIECE, mcts_iterations=800):
        self.n_squares   = 8
        self.board       = self.create_board()
        self.turn        = RED_PIECE
        self.winner      = None
        self.selected_piece  = None
        self.available_moves = []
        self.capture_moves   = []
        self.move_count      = 0
        self.width  = WIN_W
        self.height = WIN_H
        

        # FIX 1 : fenêtre redimensionnable
        self.window = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
        self.square_size = CELL
        pygame.display.set_caption("Checkers – MCTS")

        self.font_lg   = pygame.font.SysFont("Helvetica", 28, bold=True)
        self.font_md   = pygame.font.SysFont("Helvetica", 18)
        self.font_sm   = pygame.font.SysFont("Helvetica", 13)
        self.font_lbl  = pygame.font.SysFont("Helvetica", 13, bold=True)   # labels coords
        self.font_king = pygame.font.SysFont("Helvetica", int(CELL * 0.30), bold=True)

        self.history = []

        self.mcts_player     = mcts_player
        self.non_mcts_player = RED_PIECE if mcts_player == BLACK_PIECE else RED_PIECE
        self.mcts_iterations = mcts_iterations
        self._ai_disabled = False

        self.SLIDER_MIN      = 100
        self.SLIDER_MAX      = 4000
        self.slider_dragging = False
        self.slider_bar_rect  = pygame.Rect(0, 0, 0, 0)
        self.slider_knob_rect = pygame.Rect(0, 0, 0, 0)

    # ── helpers de positionnement ──────────────────────────────────────────
    @property
    def board_x(self):
        """Origine X du plateau (après la bande de labels de lignes)."""
        return LABEL_W

    @property
    def board_y(self):
        """Origine Y du plateau (en haut)."""
        return 0

    def _cell_rect(self, row, col):
        x = self.board_x + col * CELL
        y = self.board_y + row * CELL
        return x, y

    # ------------------------------------------------------------------ board
    def create_board(self):
        board = [[0] * self.n_squares for _ in range(self.n_squares)]
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                if (r + c) % 2 != 0:
                    if r < 3:
                        board[r][c] = BLACK_PIECE
                    elif r > 4:
                        board[r][c] = RED_PIECE
        return board

    # ------------------------------------------------------------------ draw
    def draw_board(self):
        self.window.fill(C_BG)
        self._draw_squares()
        self._draw_coord_labels()   # FIX 2 : labels visibles
        self._draw_pieces()
        self._draw_panel()
        if self.winner:
            self._draw_winner()
        pygame.display.update()

    def _draw_squares(self):
        legal_dests = set(self.available_moves)
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                x0, y0 = self._cell_rect(r, c)
                dark = (r + c) % 2 != 0
                if not dark:
                    fill = C_LIGHT
                elif self.selected_piece and (r, c) == self.selected_piece:
                    fill = C_SELECT
                else:
                    fill = C_DARK
                pygame.draw.rect(self.window, fill, (x0, y0, CELL, CELL))

                if dark and (r, c) in legal_dests:
                    is_cap = abs(r - self.selected_piece[0]) == 2 if self.selected_piece else False
                    dot_c  = C_CAPTURE if is_cap else C_LEGAL
                    mx, my = x0 + CELL // 2, y0 + CELL // 2
                    pygame.draw.circle(self.window, dot_c, (mx, my), 12)

    # FIX 2 : labels de coordonnées bien visibles ──────────────────────────
    def _draw_coord_labels(self):
        # ── bande gauche : numéros de lignes (0 à 7) ──────────────────────
        pygame.draw.rect(self.window, C_LABEL_BG, (0, 0, LABEL_W, BOARD_PX))
        for r in range(self.n_squares):
            lbl = self.font_lbl.render(str(r), True, C_LABEL_TXT)
            _, y0 = self._cell_rect(r, 0)
            lx = LABEL_W // 2 - lbl.get_width() // 2
            ly = y0 + CELL // 2 - lbl.get_height() // 2
            self.window.blit(lbl, (lx, ly))

        # ── bande basse : numéros de colonnes (0 à 7) ─────────────────────
        pygame.draw.rect(self.window, C_LABEL_BG,
                         (0, BOARD_PX, LABEL_W + BOARD_PX, LABEL_H))
        for c in range(self.n_squares):
            lbl = self.font_lbl.render(str(c), True, C_LABEL_TXT)
            x0, _ = self._cell_rect(0, c)
            lx = x0 + CELL // 2 - lbl.get_width() // 2
            ly = BOARD_PX + LABEL_H // 2 - lbl.get_height() // 2
            self.window.blit(lbl, (lx, ly))

        # coin en bas à gauche (petit carré neutre)
        pygame.draw.rect(self.window, C_LABEL_BG, (0, BOARD_PX, LABEL_W, LABEL_H))

    def _draw_pieces(self):
        for r in range(self.n_squares):
            for c in range(self.n_squares):
                piece = self.board[r][c]
                if piece == 0:
                    continue
                x0, y0 = self._cell_rect(r, c)
                x = x0 + CELL // 2
                y = y0 + CELL // 2
                rad = CELL // 2 - 8
                is_red  = piece in (RED_PIECE,  RED_KING)
                is_king = piece in (BLACK_KING, RED_KING)
                fill = C_RED_FILL if is_red else C_BLK_FILL
                rim  = C_RED_RIM  if is_red else C_BLK_RIM
                pygame.draw.circle(self.window, C_SHADOW, (x + 3, y + 3), rad)
                pygame.draw.circle(self.window, fill, (x, y), rad)
                pygame.draw.circle(self.window, rim,  (x, y), rad, 3)
                if is_king:
                    pygame.draw.circle(self.window, rim, (x, y), rad - 9, 2)
                    cc = (255, 220, 180) if is_red else (200, 200, 200)
                    lbl = self.font_king.render("K", True, cc)
                    self.window.blit(lbl, (x - lbl.get_width() // 2, y - lbl.get_height() // 2))

    def _draw_panel(self):
        px = LABEL_W + BOARD_PX
        pygame.draw.rect(self.window, C_PANEL, (px, 0, PANEL_W, WIN_H))
        pygame.draw.line(self.window, C_BORDER, (px, 0), (px, WIN_H), 1)

        y = 18
        title = self.font_lg.render("Checkers", True, C_TEXT)
        self.window.blit(title, (px + PANEL_W // 2 - title.get_width() // 2, y))
        y += 40

        pygame.draw.line(self.window, C_BORDER, (px + 10, y), (px + PANEL_W - 10, y), 1)
        y += 14

        red_cnt   = sum(1 for r in self.board for p in r if p in (RED_PIECE,   RED_KING))
        black_cnt = sum(1 for r in self.board for p in r if p in (BLACK_PIECE, BLACK_KING))

        pygame.draw.circle(self.window, C_RED_FILL, (px + 30, y + 10), 10)
        pygame.draw.circle(self.window, C_RED_RIM,  (px + 30, y + 10), 10, 2)
        rc = self.font_md.render(f"Rouge  {red_cnt}", True, C_TEXT)
        self.window.blit(rc, (px + 48, y))

        y += 30
        pygame.draw.circle(self.window, C_BLK_FILL, (px + 30, y + 10), 10)
        pygame.draw.circle(self.window, C_BLK_RIM,  (px + 30, y + 10), 10, 2)
        bc = self.font_md.render(f"Noir     {black_cnt}", True, C_TEXT)
        self.window.blit(bc, (px + 48, y))

        y += 32
        pygame.draw.line(self.window, C_BORDER, (px + 10, y), (px + PANEL_W - 10, y), 1)
        y += 12

        if not self.winner:
            if self.turn == RED_PIECE:
                turn_txt = "Rouge (vous)"
                turn_col = C_RED_FILL
            else:
                turn_txt = "Noir (IA)"
                turn_col = (180, 180, 180)
            lbl = self.font_md.render("Tour :", True, C_SUBTEXT)
            self.window.blit(lbl, (px + 10, y))
            val = self.font_md.render(turn_txt, True, turn_col)
            self.window.blit(val, (px + 10, y + 20))
            y += 52
        else:
            y += 10

        pygame.draw.line(self.window, C_BORDER, (px + 10, y), (px + PANEL_W - 10, y), 1)
        y += 14

        sim_lbl = self.font_sm.render("Simulations MCTS", True, C_SUBTEXT)
        self.window.blit(sim_lbl, (px + 10, y))
        y += 18

        val_txt = self.font_md.render(str(self.mcts_iterations), True, C_ACCENT)
        self.window.blit(val_txt, (px + PANEL_W - val_txt.get_width() - 10, y - 2))

        bar_x = px + 10
        bar_y = y + 16
        bar_w = PANEL_W - 20
        bar_h = 6
        pygame.draw.rect(self.window, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=3)

        ratio = (self.mcts_iterations - self.SLIDER_MIN) / (self.SLIDER_MAX - self.SLIDER_MIN)
        filled_w = int(bar_w * ratio)
        if filled_w > 0:
            pygame.draw.rect(self.window, C_ACCENT, (bar_x, bar_y, filled_w, bar_h), border_radius=3)

        knob_x = bar_x + filled_w
        knob_y = bar_y + bar_h // 2
        pygame.draw.circle(self.window, C_ACCENT, (knob_x, knob_y), 8)
        pygame.draw.circle(self.window, C_TEXT,   (knob_x, knob_y), 8, 2)

        self.slider_bar_rect  = pygame.Rect(bar_x - 8, bar_y - 8, bar_w + 16, bar_h + 16)
        self.slider_knob_rect = pygame.Rect(knob_x - 8, knob_y - 8, 16, 16)

        mn = self.font_sm.render(str(self.SLIDER_MIN), True, (100, 100, 100))
        mx = self.font_sm.render(str(self.SLIDER_MAX), True, (100, 100, 100))
        self.window.blit(mn, (bar_x, bar_y + 10))
        self.window.blit(mx, (bar_x + bar_w - mx.get_width(), bar_y + 10))

        y += 46
        pygame.draw.line(self.window, C_BORDER, (px + 10, y), (px + PANEL_W - 10, y), 1)
        y += 12

        h_lbl = self.font_sm.render("Historique", True, C_SUBTEXT)
        self.window.blit(h_lbl, (px + 10, y))
        y += 18
        for entry in self.history[:14]:
            line = self.font_sm.render(entry, True, (200, 200, 200))
            self.window.blit(line, (px + 10, y))
            y += 16
            if y > WIN_H - 10:
                break

    def _log(self, msg):
        self.history.insert(0, msg)

    def _draw_winner(self):
        if self.winner == "draw":
            msg = "Match nul !"
        elif self.winner == BLACK_PIECE:
            msg = "Noir gagne !"
        else:
            msg = "Rouge gagne !"
        surf_txt = self.font_lg.render(msg, True, C_ACCENT)
        w = surf_txt.get_width() + 40
        h = surf_txt.get_height() + 20
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 210))
        bx = LABEL_W + BOARD_PX // 2 - w // 2
        by = BOARD_PX // 2 - h // 2
        self.window.blit(overlay, (bx, by))
        pygame.draw.rect(self.window, C_ACCENT, (bx, by, w, h), 2, border_radius=6)
        self.window.blit(surf_txt, (bx + 20, by + 10))

    # ------------------------------------------------------------------ moves
    def _opponent(self, turn):
        return BLACK_PIECE if turn == RED_PIECE else RED_PIECE

    def get_available_moves(self, row, col, board, turn):
        piece = board[row][col]
        moves = []
        if piece == BLACK_PIECE:
            moves += self._diagonal_moves(row, col, +1, board, turn)
        elif piece == RED_PIECE:
            moves += self._diagonal_moves(row, col, -1, board, turn)
        elif piece in (BLACK_KING, RED_KING):
            moves += self._diagonal_moves(row, col, +1, board, turn)
            moves += self._diagonal_moves(row, col, -1, board, turn)
        return moves

    def _diagonal_moves(self, row, col, direction, board, turn):
        moves = []
        opp   = self._opponent(turn)
        for dc in (+1, -1):
            nr, nc = row + direction, col + dc
            if self._in_bounds(nr, nc) and board[nr][nc] == 0:
                moves.append((nr, nc))
            elif self._in_bounds(nr, nc) and board[nr][nc] in (opp, opp + 2):
                jr, jc = row + 2 * direction, col + 2 * dc
                if self._in_bounds(jr, jc) and board[jr][jc] == 0:
                    moves.append((jr, jc))
        return moves

    def _in_bounds(self, r, c):
        return 0 <= r < self.n_squares and 0 <= c < self.n_squares

    def has_capture_moves(self, row, available_moves):
        return [(r, c) for (r, c) in available_moves if abs(r - row) == 2]

    def get_all_possible_moves(self, board, turn):
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
        return capture_only if capture_only else all_moves

    # ------------------------------------------------------------------ UI
    def select(self, row, col):
        if self.winner:
            return
        piece = self.board[row][col]

    # Si une capture multiple est en cours (après un premier saut)
        if self.capture_moves:
            if (row, col) in self.capture_moves:
                self.move(row, col)
            return

    # Récupérer tous les coups légaux du joueur (avec capture obligatoire)
        legal_moves_dict = self.get_all_possible_moves(self.board, self.turn)

        if piece != 0 and (piece == self.turn or piece == self.turn + 2):
        # Vérifier si la pièce cliquée a des coups légaux
            if (row, col) in legal_moves_dict:
                self.selected_piece = (row, col)
                self.available_moves = legal_moves_dict[(row, col)]
            else:
            # La pièce ne peut pas bouger (aucun coup légal)
                self.selected_piece = None
                self.available_moves = []
        elif self.selected_piece:
            self.move(row, col)

    def move(self, row, col):
        if (row, col) not in self.available_moves:
            self.selected_piece  = None
            self.available_moves = []
            self.capture_moves   = []
            return

        self.capture_moves = []

        sr, sc = self.selected_piece
        self.board[row][col] = self.board[sr][sc]
        self.board[sr][sc]   = 0

        if self.board[row][col] == BLACK_PIECE and row == self.n_squares - 1:
            self.board[row][col] = BLACK_KING
        elif self.board[row][col] == RED_PIECE and row == 0:
            self.board[row][col] = RED_KING

        if abs(row - sr) == 2:
            mid_r = sr + (row - sr) // 2
            mid_c = sc + (col - sc) // 2
            self.board[mid_r][mid_c] = 0
            self.move_count = 0
            who = "Rouge" if self.turn == RED_PIECE else "Noir"
            self._log(f"{who}: ({sr},{sc})→({row},{col}) ×")

            self.draw_board()
            pygame.display.update()

            self.selected_piece = (row, col)
            next_moves = self.get_available_moves(row, col, self.board, self.turn)
            next_caps  = self.has_capture_moves(row, next_moves)
            if next_caps:
                self.available_moves = next_caps
                self.capture_moves   = next_caps
                if self.turn == self.mcts_player:
                    self.move(next_caps[0][0], next_caps[0][1])
                return
        else:
            who = "Rouge" if self.turn == RED_PIECE else "Noir"
            self._log(f"{who}: ({sr},{sc})→({row},{col})")

        self.change_turn()

    def change_turn(self):
        self.turn = self._opponent(self.turn)
        self.selected_piece  = None
        self.available_moves = []
        self.capture_moves   = []
        self.move_count += 1

        if self.move_count >= 100:
            self.winner = "draw"
            return
        if self.check_winner(self.board):
            self.winner = self._opponent(self.turn)
            return

    def check_winner(self, board):
        red_has_moves = black_has_moves = False
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
        if self.turn == RED_PIECE and not red_has_moves:
            return True
        if self.turn == BLACK_PIECE and not black_has_moves:
            return True
        return False

    # ------------------------------------------------------------------ MCTS
    def make_move(self, board, move, piece_row, piece_col):
        nb = [r[:] for r in board]
        pr, pc = piece_row, piece_col
        mr, mc = move

        nb[mr][mc] = nb[pr][pc]
        nb[pr][pc] = 0

        if nb[mr][mc] == BLACK_PIECE and mr == self.n_squares - 1:
            nb[mr][mc] = BLACK_KING
        elif nb[mr][mc] == RED_PIECE and mr == 0:
            nb[mr][mc] = RED_KING

        if abs(mr - pr) == 2:
            nb[pr + (mr - pr) // 2][pc + (mc - pc) // 2] = 0
            turn_of_piece = nb[mr][mc] if nb[mr][mc] <= 2 else nb[mr][mc] - 2
            next_mvs  = self.get_available_moves(mr, mc, nb, turn_of_piece)
            next_caps = self.has_capture_moves(mr, next_mvs)
            if next_caps:
                return self.make_move(nb, random.choice(next_caps), mr, mc)

        return nb

    def mcts_search(self, board, iterations, turn=None):
        if turn is None:
            turn = self.mcts_player
        root = MCTSNode(board, turn)
        all_moves = self.get_all_possible_moves(board, turn)
        root.untried_moves = [(p, m) for p, mvs in all_moves.items() for m in mvs]

        for _ in range(iterations):
            node       = root
            temp_board = [r[:] for r in board]
            temp_turn  = turn

            while node.untried_moves == [] and node.children:
                node = node.best_child()
                if node.move:
                    p, mv = node.move
                    temp_board = self.make_move(temp_board, mv, p[0], p[1])
                    temp_turn  = self._opponent(temp_turn)

            if node.untried_moves:
                chosen = random.choice(node.untried_moves)
                node.untried_moves.remove(chosen)
                p, mv = chosen
                temp_board = self.make_move(temp_board, mv, p[0], p[1])
                temp_turn  = self._opponent(temp_turn)

                child = MCTSNode(temp_board, temp_turn, parent=node, move=chosen)
                child_moves = self.get_all_possible_moves(temp_board, temp_turn)
                child.untried_moves = [(cp, cm) for cp, cms in child_moves.items() for cm in cms]
                node.children.append(child)
                node = child

            sim_board = [r[:] for r in temp_board]
            sim_turn  = temp_turn
            depth = 0

            while not self.check_winner(sim_board) and depth < 80:
                sim_moves = self.get_all_possible_moves(sim_board, sim_turn)
                if not sim_moves:
                    break
                p, mv = self._smart_random_move(sim_moves, sim_board, sim_turn)
                sim_board = self.make_move(sim_board, mv, p[0], p[1])
                sim_turn  = self._opponent(sim_turn)
                depth += 1

            result = self.evaluate_board(sim_board, turn)
            while node is not None:
                node.visits += 1
                node.wins   += result
                node = node.parent

        if not root.children:
            return None
        return max(root.children, key=lambda ch: ch.visits).move

    def _smart_random_move(self, moves, board, turn):
        captures = [(p, m) for p, ms in moves.items() for m in ms if abs(m[0] - p[0]) == 2]
        if captures:
            return random.choice(captures)

        scored = []
        center = 3.5
        for p, ms in moves.items():
            for m in ms:
                score = 0
                if turn == BLACK_PIECE:
                    score += m[0]
                elif turn == RED_PIECE:
                    score += (7 - m[0])
                score += 2 - abs(m[1] - center) * 0.5
                if board[p[0]][p[1]] in (BLACK_KING, RED_KING):
                    score += 1
                scored.append((score, p, m))

        scored.sort(reverse=True)
        top = scored[:max(1, len(scored) // 2)]
        _, p, m = random.choice(top)
        return p, m

    def evaluate_board(self, board, mcts_player=None):
        if mcts_player is None:
            mcts_player = self.mcts_player
        red_score = black_score = 0

        for r in range(self.n_squares):
            for c in range(self.n_squares):
                p = board[r][c]
                if p == 0:
                    continue
                center_bonus = 1.0 - abs(c - 3.5) / 7.0

                if p == RED_PIECE:
                    advance = (7 - r) / 7.0
                    red_score   += 10 + 3 * advance + center_bonus
                    if r == 7:
                        red_score += 1
                elif p == RED_KING:
                    red_score   += 20 + center_bonus * 2
                elif p == BLACK_PIECE:
                    advance = r / 7.0
                    black_score += 10 + 3 * advance + center_bonus
                    if r == 0:
                        black_score += 1
                elif p == BLACK_KING:
                    black_score += 20 + center_bonus * 2

        diff = red_score - black_score
        if mcts_player == BLACK_PIECE:
            diff = -diff

        return 1 / (1 + math.exp(-diff / 15))

    # ------------------------------------------------------------------ slider
    def _slider_x_to_iters(self, mouse_x):
        bar_x = LABEL_W + BOARD_PX + 10
        bar_w = PANEL_W - 20
        ratio = max(0.0, min(1.0, (mouse_x - bar_x) / bar_w))
        value = self.SLIDER_MIN + ratio * (self.SLIDER_MAX - self.SLIDER_MIN)
        step = 10
        return max(self.SLIDER_MIN, min(self.SLIDER_MAX, round(value / step) * step))

    # ------------------------------------------------------------------ main loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            self.draw_board()
            if not self._ai_disabled and not self.winner and self.turn == self.mcts_player:
                best = self.mcts_search(self.board, self.mcts_iterations)
                if best:
                    piece, mv = best
                    self.selected_piece  = piece
                    self.available_moves = self.get_available_moves(piece[0], piece[1], self.board, self.turn)
                    self.move(mv[0], mv[1])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # FIX 1 : gérer le redimensionnement
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE
                    )

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if self.slider_bar_rect.collidepoint(mx, my) or \
                       self.slider_knob_rect.collidepoint(mx, my):
                        self.slider_dragging = True
                        self.mcts_iterations = self._slider_x_to_iters(mx)
                    elif not self.winner and self.turn != self.mcts_player:
                        # Convertir coords souris → case (en tenant compte de LABEL_W)
                        col = (mx - LABEL_W) // CELL
                        row = my // CELL
                        if 0 <= col < self.n_squares and 0 <= row < self.n_squares:
                            self.select(row, col)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.slider_dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.slider_dragging:
                        self.mcts_iterations = self._slider_x_to_iters(event.pos[0])

            clock.tick(60)
        pygame.quit()
