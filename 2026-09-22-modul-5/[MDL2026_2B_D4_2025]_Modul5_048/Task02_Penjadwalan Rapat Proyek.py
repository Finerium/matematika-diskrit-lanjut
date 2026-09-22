# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 5 - Task02 (kelompok): penjadwalan rapat sub-tim dengan graph coloring

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


# simpul = sub-tim, sisi = dua sub-tim punya anggota yang sama sehingga rapatnya tidak boleh bersamaan
subtim = {
    "Sub-tim 1": {"Alyn", "Betty", "Erin"},
    "Sub-tim 2": {"Alyn", "Carol", "Frank"},
    "Sub-tim 3": {"Betty", "David"},
    "Sub-tim 4": {"Carol", "Erin", "Frank"},
    "Sub-tim 5": {"David", "Frank"},
}
G = nx.Graph()
G.add_nodes_from(subtim)
for (s1, a1), (s2, a2) in itertools.combinations(subtim.items(), 2):
    sama = a1 & a2
    if sama:
        G.add_edge(s1, s2, anggota=", ".join(sorted(sama)))

print(f"Graf konflik: {G.number_of_nodes()} simpul, {G.number_of_edges()} sisi")
for u, v, d in G.edges(data=True):
    print(f"  {u} - {v}  (anggota sama: {d['anggota']})")
print("Pasangan yang boleh rapat bersamaan:",
      [f"{u} & {v}" for u, v in itertools.combinations(subtim, 2) if not G.has_edge(u, v)])

segitiga = [c for c in nx.enumerate_all_cliques(G) if len(c) == 3]
print("\nSegitiga di graf:", segitiga)
chi, warna = bilangan_kromatik(G)
greedy = nx.coloring.greedy_color(G, strategy="largest_first")
print(f"Bilangan kromatik chi(G) = {chi} (brute force)")
print(f"Greedy largest_first memakai {len(set(greedy.values()))} warna")

print("\nJadwal rapat (satu warna = satu slot waktu):")
for slot in range(chi):
    anggota_slot = [s for s in subtim if warna[s] == slot]
    orang = sorted(set().union(*(subtim[s] for s in anggota_slot)))
    print(f"  Slot {slot + 1}: {', '.join(anggota_slot):22s} hadir: {', '.join(orang)}")

print("\nPerbandingan dengan graf bipartit minggu 2:")
B = nx.Graph()
developer = sorted(set().union(*subtim.values()))
B.add_nodes_from(developer, bipartite=0)
B.add_nodes_from(subtim, bipartite=1)
B.add_edges_from((d, s) for s, orang in subtim.items() for d in orang)
print(f"  Graf developer dan sub-tim: bipartit = {nx.is_bipartite(B)}, {B.number_of_nodes()} simpul, "
      f"{B.number_of_edges()} sisi")
proyeksi = nx.bipartite.projected_graph(B, list(subtim))
print("  Proyeksi graf bipartit ke sisi sub-tim sama dengan graf konflik:",
      nx.utils.graphs_equal(nx.Graph(proyeksi.edges()), nx.Graph(G.edges())))
print(f"  Graf konflik bipartit? {nx.is_bipartite(G)} (ada segitiga, jadi butuh minimal 3 warna)")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
pos = nx.circular_layout(G)
nx.draw(G, pos, ax=axes[0], with_labels=True, node_color=[PALET[warna[v]] for v in G], edgecolors="black",
        node_size=2300, font_size=9, width=1.5)
nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "anggota"), ax=axes[0], font_size=8)
axes[0].set_title(f"Graf konflik rapat, chi(G) = {chi} slot")
posB = nx.bipartite_layout(B, developer)
nx.draw(B, posB, ax=axes[1], with_labels=True, node_color=["lightblue" if v in developer else "lightgray" for v in B],
        edgecolors="black", node_size=1500, font_size=8)
axes[1].set_title("Graf bipartit developer dan sub-tim (gaya minggu 2)")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task02_rapat.png"), dpi=150)
plt.show()
