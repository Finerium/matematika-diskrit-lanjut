# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 4 - Task02: rute kurir yang melewati setiap jalan perumahan tepat satu kali (Euler circuit)

import itertools
import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

# simpul = persimpangan di perumahan, sisi = ruas jalan
# jalan lingkar luar melewati 8 persimpangan, ditambah 4 jalan tengah yang menghubungkan
# Gerbang, Masjid, Lapangan, dan Taman sehingga keempatnya jadi persimpangan besar
lingkar = ["Gerbang", "Blok A", "Masjid", "Blok B", "Lapangan", "Blok C", "Taman", "Blok D"]
jalan = list(zip(lingkar, lingkar[1:] + lingkar[:1]))
jalan += [("Gerbang", "Masjid"), ("Masjid", "Lapangan"), ("Lapangan", "Taman"), ("Taman", "Gerbang")]
G = nx.Graph(jalan)

print(f"Jumlah simpul (persimpangan): {G.number_of_nodes()}")
print(f"Jumlah sisi (ruas jalan)    : {G.number_of_edges()}")
derajat = dict(G.degree())
print("\nDerajat tiap simpul:")
for v in lingkar:
    print(f"  {v:9s}: {derajat[v]} ({'genap' if derajat[v] % 2 == 0 else 'GANJIL'})")
print(f"Jumlah derajat = {sum(derajat.values())} = 2 x {G.number_of_edges()}")

print("\nSyarat Euler circuit:")
print("  graf terhubung                :", nx.is_connected(G))
print("  semua simpul berderajat genap:", all(d % 2 == 0 for d in derajat.values()))
print("  nx.is_eulerian(G)             :", nx.is_eulerian(G))

rute = list(nx.eulerian_circuit(G, source="Gerbang"))
print("\nRute kurir (Euler circuit dari Gerbang):")
for i, (u, v) in enumerate(rute, 1):
    print(f"  {i:2d}. {u} -> {v}")
dilewati = [frozenset(e) for e in rute]
print("Tiap jalan dilewati tepat sekali:", len(dilewati) == len(set(dilewati)) == G.number_of_edges())
print("Kembali ke titik awal           :", rute[0][0] == rute[-1][1])


def hamilton_circuit(G, awal):
    for susunan in itertools.permutations([v for v in G if v != awal]):
        jalur = [awal, *susunan, awal]
        if all(G.has_edge(u, v) for u, v in zip(jalur, jalur[1:])):
            return jalur
    return None


ham = hamilton_circuit(G, "Gerbang")
print("\nPembanding, salah satu Hamilton circuit:", " -> ".join(ham))
print(f"  Hamilton circuit memakai {len(ham) - 1} dari {G.number_of_edges()} jalan, "
      f"jadi {G.number_of_edges() - (len(ham) - 1)} jalan tidak pernah dilewati kurir")

pos = {"Gerbang": (0, 2), "Blok A": (1, 3), "Masjid": (2, 2), "Blok B": (3, 1), "Lapangan": (2, 0),
       "Blok C": (1, -1), "Taman": (0, 0), "Blok D": (-1, 1)}
fig, ax = plt.subplots(figsize=(8, 6.2))
warna = ["orange" if derajat[v] == 4 else "lightblue" for v in G]
nx.draw(G, pos, ax=ax, with_labels=False, node_color=warna, edgecolors="black", node_size=2000, width=1.6)
nx.draw_networkx_labels(G, pos, labels={v: f"{v}\nd={derajat[v]}" for v in G}, ax=ax, font_size=7.5)
urutan_sisi = {frozenset(e): i for i, e in enumerate(rute, 1)}
nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): urutan_sisi[frozenset((u, v))] for u, v in G.edges()},
                             ax=ax, font_color="red", font_size=9)
ax.set_title("Jalan perumahan: 8 persimpangan, 12 jalan\nangka merah = urutan jalan pada Euler circuit")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task02_rute_postman.png"), dpi=150)
plt.show()
