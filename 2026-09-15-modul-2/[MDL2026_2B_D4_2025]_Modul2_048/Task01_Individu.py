# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task01: graf lengkap K4, graf lingkaran C5, dan graf roda W6

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)


def properti(G, nama):
    print(f"--- {nama} ---")
    print(f"Jumlah simpul : {G.number_of_nodes()}")
    print(f"Jumlah sisi   : {G.number_of_edges()}")
    print("Derajat       : " + ", ".join(f"{v} = {d}" for v, d in G.degree()))
    print()


K4 = nx.complete_graph(4)
C5 = nx.cycle_graph(5)
# W6 menurut Rosen adalah C6 ditambah satu simpul pusat, jadi totalnya 7 simpul.
# wheel_graph(n) di NetworkX sudah menghitung simpul pusat, makanya dipakai wheel_graph(7).
W6 = nx.wheel_graph(7)

for G, nama in [(K4, "Graf lengkap K4"), (C5, "Graf lingkaran C5"), (W6, "Graf roda W6")]:
    properti(G, nama)

# simpul 0 pada W6 adalah pusat roda, sisanya disusun melingkar
pos_w6 = nx.circular_layout(range(1, 7))
pos_w6[0] = (0, 0)

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
for ax, G, pos, nama in [(axes[0], K4, nx.circular_layout(K4), "K4"),
                         (axes[1], C5, nx.circular_layout(C5), "C5"),
                         (axes[2], W6, pos_w6, "W6")]:
    nx.draw(G, pos, ax=ax, with_labels=True, node_color="lightblue", edgecolors="black",
            node_size=600, font_weight="bold")
    ax.set_title(f"{nama}: {G.number_of_nodes()} simpul, {G.number_of_edges()} sisi")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task01_k4_c5_w6.png"), dpi=150)
plt.show()
