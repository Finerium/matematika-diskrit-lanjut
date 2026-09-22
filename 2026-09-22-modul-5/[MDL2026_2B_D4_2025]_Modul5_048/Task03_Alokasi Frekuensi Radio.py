# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 5 - Task03 (kelompok): alokasi frekuensi radio, connected components, dan cut vertex

import itertools
import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

PALET = ["tomato", "mediumseagreen", "cornflowerblue", "gold", "orchid", "orange"]


def pewarnaan_valid(G, warna):
    return all(warna[u] != warna[v] for u, v in G.edges())


def bilangan_kromatik(G):
    """Coba k = 1, 2, 3, ... dan kembalikan k terkecil yang punya pewarnaan valid beserta pewarnaannya."""
    simpul = list(G.nodes())
    for k in range(1, len(simpul) + 1):
        # simpul pertama boleh dikunci ke warna 0 karena nama warna bisa ditukar tanpa mengubah hasil
        for sisa in itertools.product(range(k), repeat=len(simpul) - 1):
            warna = dict(zip(simpul, (0, *sisa)))
            if pewarnaan_valid(G, warna):
                return k, warna
    return 0, {}


# simpul = stasiun pemancar, sisi = dua stasiun berjarak kurang dari 10 km (tidak boleh satu frekuensi)
dekat = {
    "A": ["B", "C"], "B": ["A", "D"], "C": ["A", "E"], "D": ["B", "F"],
    "E": ["C", "G"], "F": ["D", "H"], "G": ["E", "H"], "H": ["F", "G"],
}
G = nx.Graph([(u, v) for u, daftar in dekat.items() for v in daftar])
print(f"Graf stasiun: {G.number_of_nodes()} simpul, {G.number_of_edges()} sisi")
print("Derajat:", dict(G.degree()))
print("Jumlah connected component:", nx.number_connected_components(G))
siklus = nx.cycle_basis(G)
print("Bentuk graf: satu siklus", " - ".join(siklus[0]), "| isomorfik dengan C8:",
      nx.is_isomorphic(G, nx.cycle_graph(8)))

chi, warna = bilangan_kromatik(G)
print(f"\nBilangan kromatik chi(G) = {chi}, graf bipartit: {nx.is_bipartite(G)}")
for f in range(chi):
    print(f"  Frekuensi {f + 1}: {sorted(v for v in G if warna[v] == f)}")

cut = list(nx.articulation_points(G))
print(f"\nCut vertex: {cut if cut else 'tidak ada'}")
print("Graf biconnected (tetap terhubung walau satu stasiun mati):", nx.is_biconnected(G))
for mati in ["A", "E"]:
    H = G.copy()
    H.remove_node(mati)
    print(f"  Kalau stasiun {mati} mati: sisa {H.number_of_nodes()} stasiun, terhubung = {nx.is_connected(H)}")

print("\nSkenario pembanding: jalur G-H putus sehingga siklus berubah jadi lintasan")
P = G.copy()
P.remove_edge("G", "H")
cut_p = sorted(nx.articulation_points(P))
print(f"  Cut vertex baru: {cut_p}")
H = P.copy()
H.remove_node("A")
print(f"  Kalau A mati di skenario ini, jumlah component jadi {nx.number_connected_components(H)}:",
      [sorted(c) for c in nx.connected_components(H)])

urut = siklus[0]
pos = nx.circular_layout(urut)
fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
nx.draw(G, pos, ax=axes[0], with_labels=True, node_color=[PALET[warna[v]] for v in G], edgecolors="black",
        node_size=900, font_weight="bold")
axes[0].set_title(f"8 stasiun (C8), chi(G) = {chi}, tanpa cut vertex")
nx.draw(P, pos, ax=axes[1], with_labels=True, node_color=["salmon" if v in cut_p else "lightgray" for v in P],
        edgecolors="black", node_size=900, font_weight="bold")
axes[1].set_title("Pembanding: G-H putus, simpul merah jadi cut vertex")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task03_frekuensi.png"), dpi=150)
plt.show()
