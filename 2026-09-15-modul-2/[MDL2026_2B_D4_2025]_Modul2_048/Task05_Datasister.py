# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task05 (kelompok): aliran data antar komponen sistem sebagai graf berarah

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

aliran = [("Processor", "Memory"), ("Processor", "Storage"), ("Memory", "Processor"),
          ("Storage", "Network Interface"), ("Network Interface", "Processor")]
G = nx.DiGraph()
G.add_edges_from(aliran)

print("Adjacency list (simpul -> tujuan aliran):")
for v in G.nodes():
    print(f"  {v}: {list(G.successors(v))}")

urutan = list(G.nodes())
M = nx.to_numpy_array(G, nodelist=urutan, dtype=int)
print("\nAdjacency matrix (baris = asal, kolom = tujuan):")
print(" " * 18 + " ".join(f"{v[:4]:>5}" for v in urutan))
for v, baris in zip(urutan, M):
    print(f"{v:>17} " + " ".join(f"{int(x):>5}" for x in baris))

print("\nDerajat masuk dan keluar:")
for v in urutan:
    print(f"  {v:<18} masuk {G.in_degree(v)}, keluar {G.out_degree(v)}")
total_masuk = sum(d for _, d in G.in_degree())
total_keluar = sum(d for _, d in G.out_degree())
print(f"Jumlah derajat masuk = {total_masuk}, jumlah derajat keluar = {total_keluar}, |E| = {G.number_of_edges()}")
print("Handshaking Theorem versi berarah terbukti:", total_masuk == total_keluar == G.number_of_edges())

# graf pembanding dengan nama simpul berbeda tapi pola aliran sama
H = nx.DiGraph([("A", "B"), ("A", "C"), ("B", "A"), ("C", "D"), ("D", "A")])
print("\nIsomorfik dengan graf A->B, A->C, B->A, C->D, D->A?", nx.is_isomorphic(G, H))
print("Pemetaan simpul:", nx.vf2pp_isomorphism(G, H))

C4 = nx.cycle_graph(4, create_using=nx.DiGraph)
print("Isomorfik dengan siklus berarah C4?", nx.is_isomorphic(G, C4))

U = G.to_undirected()
print(f"\nGraf tak berarah pembentuknya: {U.number_of_nodes()} simpul, {U.number_of_edges()} sisi")
print("Isomorfik dengan tadpole graph (C3 + satu simpul bandul)?", nx.is_isomorphic(U, nx.tadpole_graph(3, 1)))

pos = {"Memory": (0, 1.6), "Processor": (0, 0.3), "Storage": (1.6, -1.0), "Network Interface": (-1.6, -1.0)}
label = {v: v.replace(" ", "\n") for v in G.nodes()}
fig, ax = plt.subplots(figsize=(7, 6))
nx.draw_networkx_nodes(G, pos, ax=ax, node_color="lightblue", edgecolors="black", node_size=3000)
nx.draw_networkx_labels(G, pos, labels=label, ax=ax, font_size=9)
# sisi dibuat sedikit melengkung supaya Processor->Memory dan Memory->Processor tidak menumpuk
nx.draw_networkx_edges(G, pos, ax=ax, node_size=3000, arrowsize=20, connectionstyle="arc3,rad=0.15")
ax.set_title("Aliran data antar komponen (graf berarah)")
ax.margins(0.15)
ax.axis("off")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task05_datasister.png"), dpi=150)
plt.show()
