# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 3 - Task04: alur komando dan informasi saat demonstrasi sebagai graf berarah
# Sisi u -> v berarti u memberi perintah atau menyampaikan informasi langsung ke v.

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")

pihak = {
    "Mahasiswa": ["Ketua BEM", "Korlap Mahasiswa", "Massa Mahasiswa", "Jubir Mahasiswa"],
    "Penyusup": ["Penyandang Dana", "Provokator Bayaran"],
    "Polisi": ["Kapolda", "Kapolrestabes", "Pasukan Dalmas", "Intel Polisi"],
    "TNI": ["Pangdam", "Pasukan TNI"],
    "Pemerintah": ["Menko Polhukam", "Jubir Pemerintah"],
    "Media": ["Media"],
}

alur = [
    # di dalam satu organisasi perintah turun dan laporan naik, jadi dua arah
    ("Ketua BEM", "Korlap Mahasiswa"), ("Korlap Mahasiswa", "Ketua BEM"),
    ("Korlap Mahasiswa", "Massa Mahasiswa"), ("Massa Mahasiswa", "Korlap Mahasiswa"),
    ("Ketua BEM", "Jubir Mahasiswa"), ("Jubir Mahasiswa", "Ketua BEM"),
    ("Kapolda", "Kapolrestabes"), ("Kapolrestabes", "Kapolda"),
    ("Kapolrestabes", "Pasukan Dalmas"), ("Pasukan Dalmas", "Kapolrestabes"),
    ("Kapolrestabes", "Intel Polisi"), ("Intel Polisi", "Kapolrestabes"),
    ("Pangdam", "Pasukan TNI"), ("Pasukan TNI", "Pangdam"),
    # koordinasi antar lembaga negara
    ("Menko Polhukam", "Kapolda"), ("Kapolda", "Menko Polhukam"),
    ("Kapolda", "Pangdam"), ("Pangdam", "Kapolda"),
    # antar pihak hanya satu arah
    ("Menko Polhukam", "Jubir Pemerintah"),
    ("Jubir Pemerintah", "Media"),
    ("Jubir Mahasiswa", "Media"),
    ("Pasukan Dalmas", "Massa Mahasiswa"),
    ("Penyandang Dana", "Provokator Bayaran"),
    ("Provokator Bayaran", "Massa Mahasiswa"),
]

G = nx.DiGraph()
for nama_pihak, anggota in pihak.items():
    G.add_nodes_from(anggota, pihak=nama_pihak)
G.add_edges_from(alur)

print(f"Jumlah simpul: {G.number_of_nodes()}, jumlah sisi: {G.number_of_edges()}")
print(f"Terhubung lemah: {nx.is_weakly_connected(G)}")
print(f"Terhubung kuat : {nx.is_strongly_connected(G)}")

print("\nBukti tidak terhubung kuat (ada pasangan simpul yang tidak bisa saling mencapai):")
for u, v in [("Menko Polhukam", "Massa Mahasiswa"), ("Kapolda", "Provokator Bayaran"), ("Ketua BEM", "Media")]:
    jalur = nx.shortest_path(G, u, v) if nx.has_path(G, u, v) else None
    print(f"  {u} -> {v}: {' -> '.join(jalur) if jalur else 'TIDAK ADA'}")
    print(f"  {v} -> {u}: {'ada' if nx.has_path(G, v, u) else 'TIDAK ADA'}")

scc = sorted(nx.strongly_connected_components(G), key=len, reverse=True)
print(f"\nStrongly Connected Components ({len(scc)}):")
for i, k in enumerate(scc, 1):
    print(f"  SCC {i}: {sorted(k)}")

# condensation: tiap SCC dijadikan satu simpul, hasilnya pasti DAG
C = nx.condensation(G, scc)
nama_scc = {i: "SCC " + str(i + 1) for i in C.nodes()}
print("\nGraf kondensasi (SCC -> SCC):", [(nama_scc[u], nama_scc[v]) for u, v in C.edges()])
print("Kondensasi DAG:", nx.is_directed_acyclic_graph(C))
print("SCC tanpa sisi masuk :", [nama_scc[n] for n in C.nodes() if C.in_degree(n) == 0])
print("SCC tanpa sisi keluar:", [nama_scc[n] for n in C.nodes() if C.out_degree(n) == 0])

pos = {
    "Penyandang Dana": (0, 3.2), "Provokator Bayaran": (0, 1.6),
    "Ketua BEM": (2.4, 3.2), "Jubir Mahasiswa": (2.4, 4.8), "Korlap Mahasiswa": (3.4, 1.8), "Massa Mahasiswa": (2.0, 0.4),
    "Media": (4.8, 6.0), "Jubir Pemerintah": (7.2, 4.8),
    "Menko Polhukam": (7.2, 3.2), "Kapolda": (6.4, 1.8), "Pangdam": (8.4, 1.8), "Pasukan TNI": (8.4, 0.2),
    "Kapolrestabes": (5.6, 0.4), "Pasukan Dalmas": (4.0, -0.9), "Intel Polisi": (6.8, -0.9),
}
warna_scc = ["#8ecae6", "#f4a261", "#e76f51", "#e9c46a", "#b5e48c", "#cdb4db"]
indeks = {n: i for i, k in enumerate(scc) for n in k}
fig, ax = plt.subplots(figsize=(13, 9))
nx.draw_networkx_nodes(G, pos, node_color=[warna_scc[indeks[n]] for n in G.nodes()], node_size=2300,
                       edgecolors="black", linewidths=0.6, ax=ax)
nx.draw_networkx_edges(G, pos, ax=ax, node_size=2300, arrows=True, arrowsize=16, width=1.4, edge_color="dimgray",
                       connectionstyle="arc3,rad=0.12")
nx.draw_networkx_labels(G, pos, labels={n: n.replace(" ", "\n", 1) for n in G}, font_size=8.5, ax=ax)
for i, k in enumerate(scc):
    ax.scatter([], [], color=warna_scc[i], s=120, edgecolors="black", label=f"SCC {i + 1}: {len(k)} simpul")
ax.legend(loc="upper left", fontsize=9, frameon=False)
ax.set_title("Alur komando saat demonstrasi, warna menunjukkan Strongly Connected Component", fontsize=12)
ax.axis("off")
ax.margins(0.08)
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task04_alur_komando.png"), dpi=110)
