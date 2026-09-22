# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 5 - Task04 (kelompok): rute kurir (Euler) dan alokasi loker (graph coloring)

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


# soal tidak memberikan daftar jalan, jadi jaringan 6 area ini dirancang sendiri:
# simpul = area, sisi = jalan antar area yang harus dilewati kurir tepat satu kali
jalan = [("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "D"), ("C", "E"), ("D", "F"), ("E", "F")]
G = nx.Graph(jalan)
derajat = dict(G.degree())
print(f"Graf area: {G.number_of_nodes()} simpul, {G.number_of_edges()} sisi")
print("Derajat:", derajat)
ganjil = [v for v, d in derajat.items() if d % 2]
print("Simpul berderajat ganjil:", ganjil)
print("Euler circuit?", nx.is_eulerian(G), "| Euler path?", nx.has_eulerian_path(G))
rute = list(nx.eulerian_path(G, source=ganjil[0]))
print("Rute kurir (Euler path):", " -> ".join([u for u, _ in rute] + [rute[-1][1]]))
print("Semua jalan dilewati tepat sekali:", len({frozenset(e) for e in rute}) == G.number_of_edges() == len(rute))

chi, warna = bilangan_kromatik(G)
print(f"\nAlokasi loker: chi(G) = {chi}")
print("Segitiga di graf:", [c for c in nx.enumerate_all_cliques(G) if len(c) == 3])
for k in range(chi):
    print(f"  Jenis loker {k + 1}: area {sorted(v for v in G if warna[v] == k)}")

print("\nApakah dua sifat ini saling bergantung?")
M = nx.MultiGraph(jalan)
M.add_edge("B", "D")
print("  Tambah satu jalan baru B-D (jalan kedua di antara B dan D):")
print("    derajat baru:", dict(M.degree()))
print("    Euler circuit sekarang?", nx.is_eulerian(M))
print("    chi tetap", bilangan_kromatik(nx.Graph(M))[0], "karena pasangan area yang bertetangga tidak berubah")
T = nx.Graph(jalan)
T.remove_edge("B", "C")
print("  Hapus jalan B-C:")
print("    Euler path?", nx.has_eulerian_path(T), "| simpul ganjil:", [v for v, d in T.degree() if d % 2])
print("    chi sekarang", bilangan_kromatik(T)[0])

pos = {"A": (0, 1), "B": (1, 2), "C": (1, 0), "D": (2.4, 2), "E": (2.4, 0), "F": (3.4, 1)}
fig, ax = plt.subplots(figsize=(8, 5))
nx.draw(G, pos, ax=ax, with_labels=True, node_color=[PALET[warna[v]] for v in G], edgecolors="black",
        node_size=1300, font_weight="bold", width=1.6)
nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): i for i, (u, v) in enumerate(rute, 1)}, ax=ax,
                             font_color="red")
ax.set_title(f"Euler path {ganjil[0]} ke {ganjil[1]} (angka merah = urutan jalan), chi(G) = {chi} jenis loker")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task04_kurir_loker.png"), dpi=150)
plt.show()
