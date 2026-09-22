# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 4 - Task01: menjalankan dan menganalisis Tutorial01 (Euler, Hamilton, dan Dijkstra)

import itertools
import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

# ---------------------------------------------------------------- bagian 1: kode Tutorial01 apa adanya

print("--- Bagian 1: Euler Path dan Circuit ---")
G_euler_circuit = nx.Graph([('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'), ('C', 'D')])
print("Derajat simpul pada graf G_euler_circuit:")
for node in G_euler_circuit.nodes():
    print(f"Simpul {node}: {G_euler_circuit.degree(node)}")
print(f"Apakah memiliki Euler Circuit? {nx.is_eulerian(G_euler_circuit)}")

print("\n--- Bagian 2: Hamilton Path dan Circuit ---")
G_hamilton_circuit = nx.cycle_graph(5)
print("C5 dibuat dengan", G_hamilton_circuit.number_of_nodes(), "simpul dan",
      G_hamilton_circuit.number_of_edges(), "sisi")

print("\n--- Bagian 3: Algoritma Dijkstra ---")
G_dijkstra = nx.Graph()
edges = [
    ('A', 'B', 4), ('A', 'C', 2), ('B', 'C', 1),
    ('B', 'D', 5), ('C', 'D', 8), ('C', 'E', 10),
    ('D', 'E', 2), ('D', 'F', 6), ('E', 'F', 3)
]
G_dijkstra.add_weighted_edges_from(edges)
shortest_path = nx.dijkstra_path(G_dijkstra, source='A', target='F')
shortest_path_length = nx.dijkstra_path_length(G_dijkstra, source='A', target='F')
print(f"Jalur terpendek dari A ke F: {shortest_path}")
print(f"Panjang jalur terpendek: {shortest_path_length}")

# ---------------------------------------------------------------- bagian 2: analisis tambahan

def urutan(sisi):
    """Daftar sisi hasil eulerian_path/eulerian_circuit diubah jadi urutan simpul."""
    sisi = list(sisi)
    return " -> ".join([u for u, _ in sisi] + [sisi[-1][1]])


print("\n=== ANALISIS 1: graf 'Euler Circuit' di tutorial ===")
ganjil = [v for v, d in G_euler_circuit.degree() if d % 2 == 1]
print("Simpul berderajat ganjil:", ganjil)
print("Punya Euler path?", nx.has_eulerian_path(G_euler_circuit))
print("Euler path dari B:", urutan(nx.eulerian_path(G_euler_circuit, source="B")))

# sisi B-C dibuang supaya semua simpul genap, hasilnya lingkaran A-B-D-C-A
G_circuit = G_euler_circuit.copy()
G_circuit.remove_edge("B", "C")
print("\nSetelah sisi B-C dibuang, derajat:", dict(G_circuit.degree()))
print("Punya Euler circuit?", nx.is_eulerian(G_circuit))
print("Euler circuit dari nx.eulerian_circuit:", urutan(nx.eulerian_circuit(G_circuit, source="A")))

print("\n=== ANALISIS 2: Hamilton circuit dicek dengan brute force ===")


def cari_hamilton(G):
    """Coba semua urutan simpul dengan simpul pertama tetap. Hanya layak untuk graf kecil (n! urutan)."""
    simpul = list(G.nodes())
    awal = simpul[0]
    dicoba = 0
    for susunan in itertools.permutations(simpul[1:]):
        dicoba += 1
        jalur = [awal, *susunan, awal]
        if all(G.has_edge(u, v) for u, v in zip(jalur, jalur[1:])):
            return jalur, dicoba
    return None, dicoba


for nama, G in [("C5", G_hamilton_circuit), ("graf tutorial bagian 1", G_euler_circuit),
                ("K4 ditambah satu simpul daun", nx.Graph([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3), (3, 4)]))]:
    jalur, dicoba = cari_hamilton(G)
    print(f"{nama:30s}: {'Hamilton circuit ' + str(jalur) if jalur else 'tidak ada Hamilton circuit'}"
          f" (mencoba {dicoba} urutan)")

print("\n=== ANALISIS 3: langkah Dijkstra ===")
jarak = nx.single_source_dijkstra_path_length(G_dijkstra, "A")
for v in sorted(jarak, key=jarak.get):
    print(f"  jarak A ke {v} = {jarak[v]:>2}  lewat {nx.dijkstra_path(G_dijkstra, 'A', v)}")
print("Jalur langsung D-F berbobot 6 kalah dari D-E-F yang totalnya", 2 + 3)

# ---------------------------------------------------------------- visualisasi

fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
pos1 = nx.spring_layout(G_euler_circuit, seed=42)
nx.draw(G_euler_circuit, pos1, ax=axes[0], with_labels=True, node_color="lightgreen", font_weight="bold",
        edgecolors="black", node_size=650)
nx.draw_networkx_nodes(G_euler_circuit, pos1, nodelist=ganjil, ax=axes[0], node_color="salmon",
                       edgecolors="black", node_size=650)
axes[0].set_title("Graf tutorial: B dan C berderajat 3\n(hanya Euler path)")
nx.draw(G_hamilton_circuit, nx.circular_layout(G_hamilton_circuit), ax=axes[1], with_labels=True,
        node_color="lightblue", font_weight="bold", edgecolors="black", node_size=650)
axes[1].set_title("C5: Hamilton circuit 0-1-2-3-4-0")
# posisi diatur manual, planar_layout membuat D, E, dan F saling berimpit
pos3 = {"A": (0, 0), "B": (1.5, 1), "C": (1.5, -1), "D": (3, 1), "E": (3, -1), "F": (4.5, 0)}
jalur_sisi = list(zip(shortest_path, shortest_path[1:]))
nx.draw(G_dijkstra, pos3, ax=axes[2], with_labels=True, node_color="lightyellow", font_weight="bold",
        edgecolors="black", node_size=650)
nx.draw_networkx_edges(G_dijkstra, pos3, edgelist=jalur_sisi, ax=axes[2], edge_color="red", width=2.5)
nx.draw_networkx_edge_labels(G_dijkstra, pos3, edge_labels=nx.get_edge_attributes(G_dijkstra, "weight"), ax=axes[2])
axes[2].set_title(f"Dijkstra A ke F, total {shortest_path_length}")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task01_tutorial.png"), dpi=150)
plt.show()
