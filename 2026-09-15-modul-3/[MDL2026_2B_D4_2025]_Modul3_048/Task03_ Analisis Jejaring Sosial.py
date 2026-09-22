# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 3 - Task03: jejaring sosial tokoh publik lulusan UGM, ITB, UI, dan Unpad (data pendidikan dari Wikipedia)
# Sisi adalah pertemanan yang diasumsikan terjadi antar tokoh satu almamater, bukan data pertemanan asli.

import os
import textwrap
from itertools import combinations

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")

tokoh = {
    "UGM": ["Joko Widodo", "Retno Marsudi", "Mahfud MD"],
    "ITB": ["Ridwan Kamil", "Budi Gunadi Sadikin", "Nurhayati Subakat"],
    "UI": ["Sri Mulyani Indrawati", "Najwa Shihab", "Chairul Tanjung"],
    "Unpad": ["Ahmad Fuadi", "Atalia Praratya", "Ferry Mursyidan Baldan"],
}

G = nx.Graph()
for kampus, orang in tokoh.items():
    G.add_nodes_from(orang, kampus=kampus)
    G.add_edges_from(combinations(orang, 2))  # tiap pasangan satu almamater dianggap saling kenal

print(f"Jumlah simpul: {G.number_of_nodes()}, jumlah sisi: {G.number_of_edges()}")
komponen = list(nx.connected_components(G))
print(f"Terhubung: {nx.is_connected(G)}")
print(f"Jumlah connected components: {nx.number_connected_components(G)}")
for i, k in enumerate(komponen, 1):
    kampus = {G.nodes[n]["kampus"] for n in k}
    print(f"  Komponen {i} ({', '.join(kampus)}): {sorted(k)}")
print(f"Ada path Joko Widodo -> Sri Mulyani Indrawati? {nx.has_path(G, 'Joko Widodo', 'Sri Mulyani Indrawati')}")

# percobaan: Pramono Anung lulusan tiga kampus sekaligus (Ir. ITB, M.M. UGM, Dr. Unpad)
H = G.copy()
for kampus in ("ITB", "UGM", "Unpad"):
    H.add_edges_from(("Pramono Anung", n) for n in tokoh[kampus])
H.nodes["Pramono Anung"]["kampus"] = "ITB, UGM, Unpad"
print("\nSetelah Pramono Anung ditambahkan:")
print(f"Jumlah connected components: {nx.number_connected_components(H)}")
for i, k in enumerate(nx.connected_components(H), 1):
    print(f"  Komponen {i}: {len(k)} simpul")
print(f"Cut vertex: {list(nx.articulation_points(H))}")
print(f"Ada path Joko Widodo -> Ridwan Kamil? {nx.has_path(H, 'Joko Widodo', 'Ridwan Kamil')}, "
      f"lewat: {nx.shortest_path(H, 'Joko Widodo', 'Ridwan Kamil')}")

# tiap kampus diletakkan di pojok berbeda, simpul satu komponen membentuk segitiga
pusat = {"UGM": (-1.6, 1.2), "ITB": (1.6, 1.2), "UI": (-1.6, -1.4), "Unpad": (1.6, -1.4)}
warna = {"UGM": "#f4a261", "ITB": "#2a9d8f", "UI": "#e9c46a", "Unpad": "#8ecae6"}
pos = {}
for kampus, orang in tokoh.items():
    for n, (dx, dy) in zip(orang, [(0, 0.55), (-0.6, -0.4), (0.6, -0.4)]):
        pos[n] = (pusat[kampus][0] + dx, pusat[kampus][1] + dy)
pos["Pramono Anung"] = (0, 0.1)

fig, axes = plt.subplots(1, 2, figsize=(15, 6.8))
for ax, graf, judul in ((axes[0], G, "Jejaring alumni empat kampus"),
                        (axes[1], H, "Ditambah Pramono Anung (ITB, UGM, Unpad)")):
    nx.draw_networkx_edges(graf, pos, ax=ax, edge_color="gray", width=1.6)
    for kampus in tokoh:
        nx.draw_networkx_nodes(graf, pos, nodelist=tokoh[kampus], node_color=warna[kampus], node_size=600,
                               edgecolors="black", linewidths=0.6, ax=ax, label=kampus)
    if "Pramono Anung" in graf:
        nx.draw_networkx_nodes(graf, pos, nodelist=["Pramono Anung"], node_color="tomato", node_size=800,
                               edgecolors="black", linewidths=0.6, ax=ax, label="lulusan 3 kampus")
    # nama ditulis di bawah simpul supaya nama panjang tidak menutupi simpul lain
    nx.draw_networkx_labels(graf, {n: (x, y - 0.3) for n, (x, y) in pos.items()},
                            labels={n: textwrap.fill(n, 12) for n in graf}, font_size=8.5, ax=ax,
                            verticalalignment="top")
    ax.set_title(f"{judul}\n{nx.number_connected_components(graf)} connected components", fontsize=12)
    ax.legend(loc="lower center", ncol=5, fontsize=9, markerscale=0.5, frameon=False, bbox_to_anchor=(0.5, -0.08))
    ax.axis("off")
    ax.margins(0.12)
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task03_jejaring_sosial.png"), dpi=110)
