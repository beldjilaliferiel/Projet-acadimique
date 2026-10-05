import pygame
import matplotlib.pyplot as plt
import numpy as np

from game.game import Game
from game.utilities import BLACK_PIECE, RED_PIECE
from mcts_classic import MCTSClassic



# UNE PARTIE : MCTS amélioré vs MCTS classique
#prépare la partie On crée le plateau de jeu, on désactive l'IA intégrée, on crée les deux IA et on initialise les compteurs
#Chaque IA joue à son tour À chaque tour de boucle, on demande à la bonne IA de chercher le meilleur coup possible sur le plateau actuel
#On joue le coup On applique le coup trouvé sur le plateau. On compte les pièces avant et après pour savoir si une pièce a été mangée
#On met à jour le compteur de coups sans capture Si une pièce a été mangée → compteur repart à 0. Sinon → on ajoute 1. C'est pour appliquer la règle des 100 coups
#On vérifie si quelqu'un a gagné On regarde si l'adversaire peut encore jouer. S'il ne peut plus → le joueur actuel a gagné, on arrête
#On vérifie le match nul Si 100 coups sans capture ou 200 coups au total → match nul, on arrête
#On retourne le résultat Une fois la partie terminée, la fonction dit qui a gagné : "black", "red" ou "draw"
def run_single_game(iter_black, iter_red):
    pygame.init()

    game = Game(
        width=720,
        height=720,
        mcts_player=BLACK_PIECE,
        mcts_iterations=iter_black
    )#CRER UNE PARTIE DE DAMES HEURISTIQUE IA 

    game._ai_disabled = True#DESACTIVER L IA intégrée du jeu NOUS QUI GERE QUI JOUE ET QUAND
    classic_ai = MCTSClassic(game)#crée l'IA classique (le joueur rouge)

    move_count = 0#compte le nombre de coups joués depuis le début
    max_moves = 200#si on dépasse 200 coups au total, on force l'arrêt pour éviter une partie infinie

    while not game.winner and move_count < max_moves:
          #On continue à jouer tant que personne n'a gagné ET qu'on n'a pas dépassé 200 coups.
        if game.turn == BLACK_PIECE:
            best = game.mcts_search(game.board, iter_black)
        else:
            best = classic_ai.mcts_search_classic(game.board, iter_red)
        #Selon qui doit jouer, on appelle la bonne IA
        if best is None:
            break#Si l'IA ne trouve aucun coup possible IA est bloqué, on arrête la partie.
        #récupère le coup
        piece, mv = best
        #la pièce à bouger et le mouvement à faire
        # Compter les pièces avant le coup
        pieces_before = sum(
            1 for r in range(game.n_squares)
            for c in range(game.n_squares)
            if game.board[r][c] != 0#pas vide
        )
        #On joue le coup plateau board maj
        game.board = game.make_move(game.board, mv, piece[0], piece[1])

        # reCompter les pièces après le coup
        pieces_after = sum(
            1 for r in range(game.n_squares)
            for c in range(game.n_squares)
            if game.board[r][c] != 0
        )

        # Reset move_count si capture, sinon incrémenter
        if pieces_after < pieces_before:
            game.move_count = 0#il y a eu une capture → on remet à 0
        else:
            game.move_count += 1# pas de capture → on incrémente
        #si 100 coups se passent sans aucune capture, c'est match nul.
        #Dès qu'une pièce est mangée, le compteur repart de zéro.
        # Vérifier gagnant
        next_turn = game._opponent(game.turn)#récupère qui est l'adversaire 
        if game.check_winner(game.board, next_turn):#vérifie si l'adversaire est bloqué ou n'a plus de pièces
            #true adversaire perdue 
            game.winner = game.turn#joueur actuel gagne
            break# on s arrete

        if game.move_count >= 100:
            game.winner = "draw"
            break#Si 100 coups se sont passés sans aucune capture on déclare match nul et on sort de la boucle

        game.turn = game._opponent(game.turn)#passe au joueur adv
        move_count += 1# incrémente le compteur global de coups joués dans la partie

    if game.winner == "draw" or move_count >= max_moves:
        return "draw"
    #game.winner == "draw" → la règle des 100 coups a été déclenchée
    #move_count >= max_moves → on a atteint 200 coups, sécurité anti-boucle infinie
    elif game.winner == BLACK_PIECE:
        return "black"
    else:
        return "red"



# ÉVALUATION
def run_evaluation(iter_black, iter_red, n_games=10):

    wins_black = 0
    wins_red = 0
    draws = 0

    print("\n" + "=" * 60)
    print(f"Evaluation ({iter_black} vs {iter_red})")
    print("=" * 60)#Evaluation (1500 vs 1500)

    for i in range(n_games):
        print(f"Game {i+1}/{n_games}: ", end="", flush=True)
         #On lance N parties
        result = run_single_game(iter_black, iter_red)
        #On enregistre le résultat de chaque partie
        if result == "black":
            wins_black += 1
            print("black wins")
        elif result == "red":
            wins_red += 1
            print("red wins")
        else:
            draws += 1
            print("draw")
    #On affiche le bilan final
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Black wins : {wins_black}/{n_games}")
    print(f"Red wins   : {wins_red}/{n_games}")
    print(f"Draws      : {draws}/{n_games}")
    #On retourne les scores
    return wins_black, wins_red, draws



# TEST MULTI SIMULATIONS
def run_simulation_test(n_games=50):

    #iterations_list = [100, 500, 1000, 1500]
    iterations_list = [1500, 2000, 2500, 3000]
    results = {}#Un dictionnaire vide qui va stocker les résultats de chaque configuration

    for iters in iterations_list:
        #Pour chaque nombre de simulations, on lance un tournoi complet. Les deux IA ont toujours le même nombre de simulations
        w_b, w_r, d = run_evaluation(iters, iters, n_games)
        #stocke les résultats
        results[iters] = {
            "black": w_b,
            "red": w_r,
            "draws": d,
            "winrate": round((w_b / n_games) * 100, 1)
        }
        #Pour chaque configuration on sauvegarde les victoires, les nuls, et le winrate de BLACK. Par exemple si BLACK gagne 3 parties sur 5 → (3/5) * 100 = 60.0%. Le round(..., 1) arrondit à 1 décimale
    # affiche le résumé dans la console
    print("\nSummary")
    print("=" * 50)
    print("iters | black | red | winrate")
    print("-" * 50)

    for iters, stats in results.items():
        print(f"{iters:<5} | {stats['black']:<5} | {stats['red']:<5} | {stats['winrate']}%")
        #stats c'est un dictionnaire. On accède à la valeur avec la clé 'black' par exemple 
    return results


# ============================================================
# GRAPHIQUES
# ============================================================
def plot_results(results, n_games):
    iters = list(results.keys())
    winrates = [results[i]["winrate"] for i in iters]
    blacks = [results[i]["black"] for i in iters]
    reds = [results[i]["red"] for i in iters]
    draws = [results[i]["draws"] for i in iters]

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle("IA Heuristique (BLACK) vs IA Classique (RED)\nImpact du nombre de simulations", fontsize=14, fontweight='bold')

    # Graphique 1 : Winrate
    ax1 = axes[0]
    ax1.plot(iters, winrates, marker="o", color="black", label="IA Heuristique (BLACK)")
    ax1.axhline(50, linestyle="--", color="red", label="50% (égalité)")
    ax1.fill_between(iters, winrates, 50, where=[w >= 50 for w in winrates], alpha=0.3, color="green", label="Avantage IA Heuristique")
    ax1.fill_between(iters, winrates, 50, where=[w < 50 for w in winrates], alpha=0.3, color="red", label="Avantage IA Classique")
    for x, y in zip(iters, winrates):
        ax1.annotate(f"{y}%", (x, y), textcoords="offset points", xytext=(0, 8), ha='center')
    ax1.set_title("Winrate de l'IA Heuristique (%)")
    ax1.set_xlabel("Nombre de simulations")
    ax1.set_ylabel("Winrate (%)")
    ax1.set_ylim(0, 100)
    ax1.legend(fontsize=8)
    ax1.grid(True)

    # Graphique 2 : Barres
    ax2 = axes[1]
    x = np.arange(len(iters))
    width = 0.25
    ax2.bar(x - width, blacks, width, label="IA Heuristique (BLACK)", color="black")
    ax2.bar(x,         reds,   width, label="IA Classique (RED)",     color="red")
    ax2.bar(x + width, draws,  width, label="Nuls",                   color="gray")
    for i, (b, r, d) in enumerate(zip(blacks, reds, draws)):
        ax2.text(i - width, b + 0.05, str(b), ha='center', fontsize=9)
        ax2.text(i,         r + 0.05, str(r), ha='center', fontsize=9)
        ax2.text(i + width, d + 0.05, str(d), ha='center', fontsize=9)
    ax2.set_title("Victoires par nombre de simulations")
    ax2.set_xlabel("Nombre de simulations")
    ax2.set_ylabel(f"Nombre de victoires / {n_games} parties")
    ax2.set_xticks(x)
    ax2.set_xticklabels(iters)
    ax2.legend(fontsize=8)
    ax2.grid(True, axis='y')

    # Graphique 3 : Pie chart du meilleur résultat
    best_iters = max(results, key=lambda i: results[i]["black"])
    best = results[best_iters]
    ax3 = axes[2]
    sizes  = [best["black"], best["red"], best["draws"]]
    labels = [f"IA Heuristique gagne\n({best['black']} parties)",
              f"IA Classique gagne\n({best['red']} parties)",
              f"Nuls\n({best['draws']} parties)"]
    colors = ["black", "red", "gray"]
    ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax3.set_title(f"Répartition avec {best_iters} simulations\n(meilleur résultat IA Heuristique)")

    plt.tight_layout()
    plt.show()



# MAIN
if __name__ == "__main__":
    #On lance les 4 tournois (1500, 2000, 2500, 3000 simulations), 5 parties chacun. Les résultats sont stockés dans results
    results = run_simulation_test(n_games=50)
    #On prend ces résultats et on affiche les 3 graphiques matplotlib
    plot_results(results, n_games=50)