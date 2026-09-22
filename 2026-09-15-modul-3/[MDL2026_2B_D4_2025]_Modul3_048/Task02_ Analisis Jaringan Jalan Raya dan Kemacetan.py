# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 3 - Task02: jaringan jalan di sekitar Simpang Lima Bandung, cut vertex dan cut edge
# Simpul = persimpangan, sisi = ruas jalan. Koordinat dan nama jalan diambil dari peta OpenStreetMap.

import math
import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")

# koordinat (lintang, bujur) tiap persimpangan
persimpangan = {
    "Simpang Lima": (-6.922352, 107.617514),
    "Asia Afrika - Kaca Kaca Wetan": (-6.922330, 107.616920),
    "Asia Afrika - Embong": (-6.922078, 107.614925),
    "Sunda - Naripan": (-6.921186, 107.617763),
    "Sunda - Veteran": (-6.920433, 107.617852),
    "Ahmad Yani - Veteran": (-6.921350, 107.619459),
    "Gatot Subroto - Ketapang": (-6.922616, 107.619544),
    "Karapitan - Lengkong Kecil": (-6.923880, 107.617464),
    "Karapitan - Emong": (-6.925034, 107.617353),
    "Lengkong Kecil - Kaca Kaca Wetan": (-6.923648, 107.616610),
    "Naripan - Embong": (-6.920710, 107.615336),
    "Burangrang - Emong": (-6.924204, 107.619929),
}

# model A: hanya lima jalan besar yang bertemu di Simpang Lima
jalan_utama = [
    ("Simpang Lima", "Asia Afrika - Kaca Kaca Wetan", "Jl. Asia Afrika"),
    ("Asia Afrika - Kaca Kaca Wetan", "Asia Afrika - Embong", "Jl. Asia Afrika"),
    ("Simpang Lima", "Sunda - Naripan", "Jl. Sunda"),
    ("Sunda - Naripan", "Sunda - Veteran", "Jl. Sunda"),
    ("Simpang Lima", "Ahmad Yani - Veteran", "Jl. Jend. Ahmad Yani"),
    ("Simpang Lima", "Gatot Subroto - Ketapang", "Jl. Jend. Gatot Subroto"),
    ("Simpang Lima", "Karapitan - Lengkong Kecil", "Jl. Sunda - Karapitan"),
    ("Karapitan - Lengkong Kecil", "Karapitan - Emong", "Jl. Karapitan"),
]
# model B: ditambah jalan kecil di sekitarnya yang bisa dipakai sebagai jalur alternatif
jalan_alternatif = [
    ("Sunda - Naripan", "Ahmad Yani - Veteran", "Jl. Naripan"),
    ("Sunda - Veteran", "Ahmad Yani - Veteran", "Jl. Veteran"),
    ("Ahmad Yani - Veteran", "Gatot Subroto - Ketapang", "Jl. Ketapang"),
    ("Asia Afrika - Kaca Kaca Wetan", "Lengkong Kecil - Kaca Kaca Wetan", "Jl. Kaca Kaca Wetan"),
    ("Lengkong Kecil - Kaca Kaca Wetan", "Karapitan - Lengkong Kecil", "Jl. Lengkong Kecil"),
    ("Asia Afrika - Embong", "Naripan - Embong", "Jl. Embong"),
    ("Naripan - Embong", "Sunda - Naripan", "Jl. Naripan"),
    ("Karapitan - Emong", "Burangrang - Emong", "Jl. Emong"),
    ("Burangrang - Emong", "Gatot Subroto - Ketapang", "Jl. Burangrang"),
]


def buat_graf(daftar_sisi):
    G = nx.Graph()
    for u, v, jalan in daftar_sisi:
        G.add_edge(u, v, jalan=jalan)
    return G


def analisis(G, nama):
    print(f"===== {nama} =====")
    print(f"Simpul: {G.number_of_nodes()}, sisi: {G.number_of_edges()}, terhubung: {nx.is_connected(G)}")
    cut_vertex = list(nx.articulation_points(G))
    cut_edge = list(nx.bridges(G))
    print("Cut vertex:", cut_vertex if cut_vertex else "tidak ada")
    print("Cut edge  :", "" if cut_edge else "tidak ada")
    for u, v in cut_edge:
        print(f"  {u} -- {v} ({G.edges[u, v]['jalan']})")
    H = G.copy()
    H.remove_node("Simpang Lima")
    komponen = [sorted(k) for k in nx.connected_components(H)]
    print(f"Setelah Simpang Lima dihapus: terhubung = {nx.is_connected(H)}, jumlah komponen = {len(komponen)}")
    for i, k in enumerate(komponen, 1):
        print(f"  komponen {i}: {k}")
    print()
    return cut_vertex, cut_edge, H


A = buat_graf(jalan_utama)
B = buat_graf(jalan_utama + jalan_alternatif)
cv_a, ce_a, A_tanpa = analisis(A, "Model A: jalan utama saja")
cv_b, ce_b, B_tanpa = analisis(B, "Model B: jalan utama + jalan alternatif")

# posisi simpul mengikuti koordinat asli, bujur dikali cos(lintang) supaya skala x dan y sama
pos = {n: (lon * math.cos(math.radians(lat)), lat) for n, (lat, lon) in persimpangan.items()}
label = {n: n.replace(" - ", "-\n") for n in persimpangan}
# label ditaruh di bawah simpul, kecuali dua simpul yang jaraknya cuma sekitar 65 m
geser = {"Asia Afrika - Kaca Kaca Wetan": (-0.00012, 0.00030)}
pos_label = {n: (x + geser.get(n, (0, 0))[0], y + geser.get(n, (0, -0.00030))[1]) for n, (x, y) in pos.items()}
fig, axes = plt.subplots(2, 2, figsize=(13, 12.5))
panel = [(A, "Model A: jalan utama", cv_a, ce_a), (A_tanpa, "Model A setelah Simpang Lima dihapus", [], []),
         (B, "Model B: dengan jalan alternatif", cv_b, ce_b), (B_tanpa, "Model B setelah Simpang Lima dihapus", [], [])]
for ax, (G, judul, cv, ce) in zip(axes.flat, panel):
    warna = ["tomato" if n in cv else "gold" if n == "Simpang Lima" else "skyblue" for n in G.nodes()]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", width=2)
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=ce, edge_color="red", width=3.5)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=warna, node_size=520, edgecolors="black", linewidths=0.6)
    nx.draw_networkx_labels(G, pos_label, labels={n: label[n] for n in G.nodes()}, ax=ax, font_size=8,
                            bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=0.8))
    ax.set_title(f"{judul}\n{nx.number_connected_components(G)} komponen terhubung", fontsize=12)
    ax.axis("off")
    ax.margins(0.12)
fig.text(0.5, 0.01, "merah = cut vertex / cut edge, kuning = Simpang Lima", ha="center", fontsize=11)
fig.tight_layout(rect=(0, 0.02, 1, 1))
fig.savefig(os.path.join(HASIL, "task02_simpang_lima.png"), dpi=110)
