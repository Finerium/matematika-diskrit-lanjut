# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 5 - Task01: menjalankan dan menganalisis Tutorial01 (graph coloring)

import itertools
import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)


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


# ---------------------------------------------------------------- kode Tutorial01

G = nx.Graph()
G.add_edges_from([
    ('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'),
    ('C', 'E'), ('D', 'E'), ('D', 'F'), ('E', 'G'),
    ('F', 'G')
])
coloring = nx.coloring.greedy_color(G, strategy="largest_first")
print("Hasil Pewarnaan Greedy:")
print(coloring)
num_colors = len(set(coloring.values()))
print(f"Jumlah warna yang digunakan: {num_colors}")

G_bipartite = nx.Graph()
G_bipartite.add_nodes_from([1, 2, 3], bipartite=0)
G_bipartite.add_nodes_from(['a', 'b', 'c'], bipartite=1)
G_bipartite.add_edges_from([(1, 'a'), (1, 'b'), (2, 'a'), (2, 'c'), (3, 'b'), (3, 'c')])
coloring_bipartite = nx.coloring.greedy_color(G_bipartite)
print("\nHasil Pewarnaan Graf Bipartit:")
print(coloring_bipartite)
print(f"Jumlah warna yang digunakan: {len(set(coloring_bipartite.values()))}")

# ---------------------------------------------------------------- analisis tambahan

print("\n=== ANALISIS 1: apakah hasil greedy sudah minimum? ===")
print("Pewarnaan greedy valid:", pewarnaan_valid(G, coloring))
segitiga = [c for c in nx.enumerate_all_cliques(G) if len(c) == 3]
print("Segitiga (klik 3 simpul) di graf:", segitiga)
chi, contoh = bilangan_kromatik(G)
print(f"Bilangan kromatik eksak (brute force) = {chi}, contoh pewarnaan: {contoh}")
print("Batas bawah 3 dari segitiga, batas atas dari greedy =", num_colors,
      "-> keduanya sama, jadi greedy kebetulan optimal di graf ini")

print("\n=== ANALISIS 2: strategi greedy yang berbeda ===")
for strategi in ["largest_first", "smallest_last", "independent_set", "DSATUR"]:
    hasil = nx.coloring.greedy_color(G, strategy=strategi)
    print(f"  {strategi:18s}: {len(set(hasil.values()))} warna")

print("\n=== ANALISIS 3: contoh saat greedy tidak optimal ===")
# crown graph: dua kelompok simpul, u_i terhubung ke semua v_j kecuali j = i. Graf ini bipartit (chi = 2),
# tetapi kalau urutan kunjungannya u1, v1, u2, v2, ... greedy terpaksa memakai warna baru di setiap pasangan
n = 4
crown = nx.Graph([(f"u{i}", f"v{j}") for i in range(1, n + 1) for j in range(1, n + 1) if i != j])
urutan_jelek = [x for i in range(1, n + 1) for x in (f"u{i}", f"v{i}")]
warna_jelek = {}
for v in urutan_jelek:
    dipakai = {warna_jelek[t] for t in crown[v] if t in warna_jelek}
    warna_jelek[v] = next(c for c in range(len(crown)) if c not in dipakai)
print("Crown graph 8 simpul, bipartit:", nx.is_bipartite(crown))
print("Greedy dengan urutan u1, v1, u2, v2, ... memakai", len(set(warna_jelek.values())), "warna")
print("Bilangan kromatik sebenarnya =", bilangan_kromatik(crown)[0])

print("\n=== ANALISIS 4: graf bipartit tutorial ===")
print("nx.is_bipartite:", nx.is_bipartite(G_bipartite), "| bentuknya siklus C6:",
      nx.is_isomorphic(G_bipartite, nx.cycle_graph(6)))

palet = ["tomato", "mediumseagreen", "cornflowerblue", "gold", "orchid", "orange", "gray", "pink"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos, ax=axes[0], with_labels=True, node_color=[palet[coloring[v]] for v in G], edgecolors="black",
        node_size=650, font_weight="bold")
axes[0].set_title(f"Graf tutorial, greedy largest_first: {num_colors} warna")
nx.draw(G_bipartite, nx.bipartite_layout(G_bipartite, [1, 2, 3]), ax=axes[1], with_labels=True,
        node_color=[palet[coloring_bipartite[v]] for v in G_bipartite], edgecolors="black", node_size=650)
axes[1].set_title("Graf bipartit tutorial: 2 warna")
kiri = [f"u{i}" for i in range(1, n + 1)]
nx.draw(crown, nx.bipartite_layout(crown, kiri), ax=axes[2], with_labels=True,
        node_color=[palet[warna_jelek[v]] for v in crown], edgecolors="black", node_size=650)
axes[2].set_title(f"Crown graph: greedy urutan jelek {len(set(warna_jelek.values()))} warna, optimal 2")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task01_tutorial_coloring.png"), dpi=150)
plt.show()
