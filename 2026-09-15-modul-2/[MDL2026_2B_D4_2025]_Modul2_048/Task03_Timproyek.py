# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task03 (kelompok): pembagian tugas tim proyek sebagai graf bipartit

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

developer = ["Alyn", "Betty", "Carol", "David"]
tugas = ["UI/UX", "Backend", "Database", "Testing"]
keahlian = {
    "Alyn": ["UI/UX", "Testing"],
    "Betty": ["UI/UX", "Backend"],
    "Carol": ["UI/UX", "Database"],
    "David": ["Backend", "Testing"],
}

G = nx.Graph()
G.add_nodes_from(developer, bipartite=0)
G.add_nodes_from(tugas, bipartite=1)
for dev, daftar in keahlian.items():
    for t in daftar:
        G.add_edge(dev, t)

print("Apakah graf bipartit?", nx.is_bipartite(G))
print()

print("Adjacency list:")
for v in G.nodes():
    print(f"  {v}: {list(G.neighbors(v))}")

urutan = developer + tugas
M = nx.to_numpy_array(G, nodelist=urutan, dtype=int)
print("\nAdjacency matrix:")
print(" " * 10 + " ".join(f"{v[:4]:>5}" for v in urutan))
for v, baris in zip(urutan, M):
    print(f"{v:>9} " + " ".join(f"{int(x):>5}" for x in baris))

derajat = dict(G.degree())
print("\nDerajat tiap simpul:", derajat)
print(f"Jumlah derajat = {sum(derajat.values())}, 2 x |E| = 2 x {G.number_of_edges()} = {2 * G.number_of_edges()}")
print("Handshaking Theorem terbukti:", sum(derajat.values()) == 2 * G.number_of_edges())


def invarian(H):
    return H.number_of_nodes(), H.number_of_edges(), sorted((d for _, d in H.degree()), reverse=True)


# graf khusus yang jumlah simpulnya sama-sama 8
print("\nPerbandingan dengan graf khusus (simpul, sisi, barisan derajat):")
for H, nama in [(G, "Graf tim proyek"), (nx.complete_bipartite_graph(4, 4), "K4,4"), (nx.cycle_graph(8), "C8")]:
    print(f"  {nama:<16} {invarian(H)}")
    if H is not G:
        print(f"  {'':<16} isomorfik dengan graf tim proyek? {nx.is_isomorphic(G, H)}")

siklus = ["Alyn", "UI/UX", "Betty", "Backend", "David", "Testing"]
print("\nSubgraf", siklus, "isomorfik dengan C6?", nx.is_isomorphic(G.subgraph(siklus), nx.cycle_graph(6)))

pasangan = nx.bipartite.hopcroft_karp_matching(G, top_nodes=developer)
print("\nContoh pembagian tugas (satu developer satu tugas):")
for dev in developer:
    print(f"  {dev} -> {pasangan[dev]}")

# developer di kolom kiri, tugas di kolom kanan, urutannya sama seperti di soal
pos = {v: (0, -i) for i, v in enumerate(developer)}
pos.update({t: (1, -i) for i, t in enumerate(tugas)})
warna = ["lightblue" if v in developer else "lightsalmon" for v in G.nodes()]
fig, ax = plt.subplots(figsize=(7, 5))
nx.draw(G, pos, ax=ax, with_labels=True, node_color=warna, edgecolors="black", node_size=2600, font_size=8)
ax.margins(0.15)
ax.set_title("Graf bipartit developer (biru) dan tugas (oranye)")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task03_timproyek.png"), dpi=150)
plt.show()
