# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 3 - Task01: menjalankan dan menganalisis Tutorial01.py (path, circuit, keterhubungan, cut vertex, cut edge)
# Alur dan graf sama dengan tutorial. Bedanya, semua gambar disimpan dalam satu file dan ada pengecekan tambahan.

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
daftar_gambar = []  # (graf, judul, sisi yang di-highlight)


def visualize_graph(G, title, highlight_edges=None):
    # di tutorial langsung plt.show(), di sini dikumpulkan dulu supaya bisa digambar dalam satu figure
    daftar_gambar.append((G.copy(), title, highlight_edges))


# --- Materi: Path dan Circuit ---
print("--- Materi: Path dan Circuit ---")
G_path = nx.Graph()
G_path.add_edges_from([("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "a"), ("b", "d")])
visualize_graph(G_path, "Contoh Graf dengan Path dan Circuit")

path_nodes = ["a", "b", "c", "d", "e"]
path_edges = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
print("Path dari a ke e: a -> b -> c -> d -> e")
print("  nx.is_path:", nx.is_path(G_path, path_nodes))
visualize_graph(G_path, "Visualisasi Path", highlight_edges=path_edges)

circuit_nodes = ["a", "b", "d", "c", "a"]
circuit_edges = [("a", "b"), ("b", "d"), ("d", "c"), ("c", "a")]
print("\nCircuit di tutorial: a -> b -> d -> c -> a")
print("  nx.is_path:", nx.is_path(G_path, circuit_nodes))
print("  sisi yang tidak ada di graf:", [e for e in circuit_edges if not G_path.has_edge(*e)])
visualize_graph(G_path, "Circuit tutorial (c-a tidak ada di graf)", highlight_edges=circuit_edges)

# circuit pengganti yang semua sisinya memang ada
circuit_benar = ["a", "b", "d", "e", "a"]
print("Circuit pengganti: a -> b -> d -> e -> a")
print("  nx.is_path:", nx.is_path(G_path, circuit_benar))
print("  cycle basis graf:", [sorted(c) for c in nx.cycle_basis(G_path)])
visualize_graph(G_path, "Circuit pengganti a-b-d-e-a",
                highlight_edges=list(zip(circuit_benar, circuit_benar[1:])))

print("\n--- Materi: Keterhubungan Graf Tak Berarah ---")
G_connected = nx.Graph()
G_connected.add_edges_from([("1", "2"), ("2", "3"), ("3", "4"), ("4", "1"), ("1", "3")])
visualize_graph(G_connected, "Graf Terhubung")
print(f"Apakah graf terhubung? {nx.is_connected(G_connected)}")

G_disconnected = nx.Graph()
G_disconnected.add_edges_from([("1", "2"), ("3", "4"), ("5", "6")])
visualize_graph(G_disconnected, "Graf Tidak Terhubung")
print(f"Apakah graf terhubung? {nx.is_connected(G_disconnected)}")
print(f"Jumlah komponen terhubung: {nx.number_connected_components(G_disconnected)}")

G_cut = nx.Graph()
G_cut.add_edges_from([("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "f"), ("f", "g"), ("g", "d")])
visualize_graph(G_cut, "Contoh Cut Vertex dan Cut Edge")

cut_vertices = list(nx.articulation_points(G_cut))
print(f"Cut Vertices (Titik Potong): {cut_vertices}")
G_cut_d = G_cut.copy()
G_cut_d.remove_node("d")
print("  komponen setelah d dihapus:", [sorted(c) for c in nx.connected_components(G_cut_d)])
visualize_graph(G_cut_d, "Setelah Cut Vertex 'd' dihapus")

cut_edges = list(nx.bridges(G_cut))
print(f"Cut Edges (Sisi Potong): {cut_edges}")
G_cut_ab = G_cut.copy()
G_cut_ab.remove_edge("a", "b")
print("  komponen setelah sisi a-b dihapus:", [sorted(c) for c in nx.connected_components(G_cut_ab)])
visualize_graph(G_cut_ab, "Setelah Cut Edge ('a', 'b') dihapus")

print("\n--- Latihan Praktikum Minggu 3 ---")
G_latihan_1 = nx.Graph()
G_latihan_1.add_edges_from([("1", "2"), ("1", "3"), ("2", "3"), ("3", "4"), ("4", "5"), ("5", "6"), ("4", "6")])
visualize_graph(G_latihan_1, "Latihan 1: Analisis Keterhubungan")
print("\nLatihan 1:")
print(f"Apakah graf terhubung? {nx.is_connected(G_latihan_1)}")
print(f"Cut Vertices (Titik Potong): {list(nx.articulation_points(G_latihan_1))}")
print(f"Cut Edges (Sisi Potong): {list(nx.bridges(G_latihan_1))}")

G_latihan_2 = nx.DiGraph()
G_latihan_2.add_edges_from([("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")])
visualize_graph(G_latihan_2, "Latihan 2: Keterhubungan Graf Berarah")
print("\nLatihan 2:")
print(f"Apakah graf terhubung kuat? {nx.is_strongly_connected(G_latihan_2)}")
print(f"Apakah graf terhubung lemah? {nx.is_weakly_connected(G_latihan_2)}")
print(f"Strongly Connected Components: {[sorted(c) for c in nx.strongly_connected_components(G_latihan_2)]}")
print(f"Ada path d -> a? {nx.has_path(G_latihan_2, 'd', 'a')}, derajat keluar d = {G_latihan_2.out_degree('d')}")

# semua graf digambar dalam satu figure, pos memakai seed yang sama dengan tutorial
fig, axes = plt.subplots(4, 3, figsize=(13, 16))
for ax, (G, judul, sorot) in zip(axes.flat, daftar_gambar):
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color="skyblue", node_size=600, ax=ax)
    panah = {"arrows": True, "arrowsize": 18} if G.is_directed() else {}  # arrowsize hanya berlaku untuk panah
    nx.draw_networkx_edges(G, pos, edge_color="gray", ax=ax, node_size=600, **panah)
    if sorot:
        # sisi yang tidak ada di graf tetap tergambar karena draw_networkx_edges hanya memakai posisi simpul
        nx.draw_networkx_edges(G, pos, edgelist=sorot, edge_color="red", width=2.5, ax=ax, node_size=600)
    nx.draw_networkx_labels(G, pos, font_size=12, ax=ax)
    ax.set_title(judul, fontsize=11)
    ax.axis("off")
    ax.margins(0.12)
for ax in axes.flat[len(daftar_gambar):]:
    ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task01_tutorial.png"), dpi=110)
