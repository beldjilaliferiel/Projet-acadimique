from random import random, sample
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Parametres epidemiologiques
V_IRULENCE = 0.65
C_CONNECTION = 1.0
INCUBATION = 3
D_INFECTIOUS = 7
P_ASYM = 0.25
P_QUARANTINE = 0.30
OMEGA = 0.02
BETA = V_IRULENCE * C_CONNECTION

# Graphe Watts-Strogatz
N = 150
K = 6
P_REWIRE = 0.12
G = nx.connected_watts_strogatz_graph(N, K, P_REWIRE)

# Etats initiaux : 20% vaccines, 5% infectes
states = {i: ('S', None) for i in G.nodes}
for i in sample(list(G.nodes), int(0.20 * N)):
    states[i] = ('V', None)
for i in sample(list(G.nodes), int(0.05 * N)):
    states[i] = ('I', D_INFECTIOUS)

COLORS = {
    'S': 'cornflowerblue',
    'E': 'orange',
    'I': 'crimson',
    'A': 'salmon',
    'Q': 'purple',
    'R': 'mediumseagreen',
    'V': 'gold'
}

def epidemic(cell, neighbors):
    category, timer = cell
    if category == 'S':
        if OMEGA > 0 and random() < OMEGA:
            return ('V', None)
        nb = sum(1 for n in neighbors if n[0] in ('I', 'A'))
        if nb > 0 and random() < BETA * nb / max(1, len(neighbors)):
            return ('E', INCUBATION)
        return cell
    elif category == 'E':
        if timer == 0:
            return ('A', D_INFECTIOUS) if random() < P_ASYM else ('I', D_INFECTIOUS)
        return ('E', timer - 1)
    elif category == 'I':
        if random() < P_QUARANTINE:
            return ('Q', timer)
        return ('R', None) if timer == 0 else ('I', timer - 1)
    elif category == 'A':
        return ('R', None) if timer == 0 else ('A', timer - 1)
    elif category == 'Q':
        return ('R', None) if timer == 0 else ('Q', timer - 1)
    return cell

# Animation et courbes
pos = nx.spring_layout(G, seed=42)
fig = plt.figure(figsize=(14, 7))
ax_graph = fig.add_axes((0.02, 0.08, 0.46, 0.84))
ax_curve = fig.add_axes((0.55, 0.10, 0.42, 0.80))
countS, countE, countI, countA, countQ, countR, countV = [], [], [], [], [], [], []

def step():
    global states
    newstates = {}
    for node in G.nodes:
        neighbors = [states[j] for j in G.neighbors(node)]
        newstates[node] = epidemic(states[node], neighbors)
    states = newstates

def update(frame):
    step()
    vals = [states[i][0] for i in G.nodes]
    for lst, s in zip([countS, countE, countI, countA, countQ, countR, countV], ['S', 'E', 'I', 'A', 'Q', 'R', 'V']):
        lst.append(vals.count(s))
    
    ax_graph.clear()
    ax_curve.clear()
    
    nx.draw_networkx(
        G, pos=pos,
        node_color=[COLORS[states[n][0]] for n in G.nodes],
        with_labels=False, node_size=85, ax=ax_graph
    )
    ax_graph.set_title(f"Watts-Strogatz Epidemic Graph --- step {frame}")
    ax_graph.axis('off')
    
    t = range(len(countS))
    for lst, lbl in zip([countS, countE, countI, countA, countQ, countR, countV], ['S', 'E', 'I', 'A', 'Q', 'R', 'V']):
        ax_curve.plot(t, lst, label=lbl)
        
    ax_curve.set_xlim(0, 80)
    ax_curve.set_ylim(0, N)
    ax_curve.grid(True, linestyle='--')
    ax_curve.legend()

ani = FuncAnimation(fig, update, frames=80, interval=300, repeat=False)
plt.show()