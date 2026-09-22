# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 4 - Task03: jalur penerbangan tercepat Bandung ke Lombok dengan algoritma Dijkstra

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

# bobot sisi = waktu tempuh penerbangan dalam jam, sesuai soal
penerbangan = [
    ("Bandung", "Jakarta", 1), ("Jakarta", "Surabaya", 2), ("Jakarta", "Yogyakarta", 1.5),
    ("Surabaya", "Bali", 2), ("Yogyakarta", "Bali", 3), ("Bali", "Lombok", 0.5), ("Jakarta", "Lombok", 3.5),
]
G = nx.Graph()
G.add_weighted_edges_from(penerbangan)
print(f"Jumlah kota: {G.number_of_nodes()}, jumlah jalur penerbangan: {G.number_of_edges()}")

jalur = nx.dijkstra_path(G, "Bandung", "Lombok")
total = nx.dijkstra_path_length(G, "Bandung", "Lombok")
print("\nJalur tercepat Bandung ke Lombok:", " -> ".join(jalur))
for u, v in zip(jalur, jalur[1:]):
    print(f"  {u} -> {v}: {G[u][v]['weight']} jam")
print(f"Total waktu tempuh: {total} jam")

print("\nJarak tercepat dari Bandung ke setiap kota (hasil Dijkstra):")
jarak, lewat = nx.single_source_dijkstra(G, "Bandung")
for kota in sorted(jarak, key=jarak.get):
    print(f"  {kota:10s} {jarak[kota]:>4} jam  lewat {' -> '.join(lewat[kota])}")

print("\nPembanding, semua jalur sederhana Bandung ke Lombok:")
semua = sorted(nx.all_simple_paths(G, "Bandung", "Lombok"), key=lambda j: nx.path_weight(G, j, "weight"))
for j in semua:
    print(f"  {nx.path_weight(G, j, 'weight'):>4} jam  {' -> '.join(j)}")
print("Hasil Dijkstra sama dengan jalur termurah dari daftar di atas:", semua[0] == jalur)

# posisi kira-kira mengikuti peta, Lombok dinaikkan supaya garis Jakarta-Lombok tidak melewati Surabaya
pos = {"Bandung": (0, 0), "Jakarta": (1, 1.2), "Yogyakarta": (2.2, -0.6), "Surabaya": (3.2, 0.5),
       "Bali": (4.4, -0.5), "Lombok": (5.6, 1.7)}
sisi_jalur = list(zip(jalur, jalur[1:]))
fig, ax = plt.subplots(figsize=(10, 4.8))
nx.draw(G, pos, ax=ax, with_labels=True, node_color="lightyellow", edgecolors="black", node_size=1900,
        font_size=9, font_weight="bold", width=1.4, edge_color="gray")
nx.draw_networkx_edges(G, pos, edgelist=sisi_jalur, ax=ax, edge_color="red", width=3.5)
nx.draw_networkx_nodes(G, pos, nodelist=jalur, ax=ax, node_color="salmon", edgecolors="black", node_size=1900)
nx.draw_networkx_labels(G, pos, labels={v: v for v in jalur}, ax=ax, font_size=9, font_weight="bold")
nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): f"{d['weight']} jam" for u, v, d in G.edges(data=True)},
                             ax=ax, font_size=8)
ax.set_title(f"Jalur tercepat Bandung ke Lombok: {' - '.join(jalur)} ({total} jam)")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task03_dijkstra_penerbangan.png"), dpi=150)
plt.show()
