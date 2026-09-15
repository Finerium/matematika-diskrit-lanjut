# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task04 (kelompok): topologi full-mesh enam server sebagai graf lengkap K6

import os

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)

server = [f"S{i}" for i in range(1, 7)]
G = nx.complete_graph(server)
sisi = list(G.edges())

print(f"Jumlah server (simpul) : {G.number_of_nodes()}")
print(f"Jumlah kabel (sisi)    : {G.number_of_edges()}")
print("Daftar sisi:", ", ".join(f"e{i}={u}-{v}" for i, (u, v) in enumerate(sisi, 1)))

# incidence matrix: baris = server, kolom = sisi, isinya 1 kalau server itu ujung dari sisi tersebut
M = np.array([[1 if v in e else 0 for e in sisi] for v in server])
print("\nIncidence matrix:")
print("    " + "".join(f"{f'e{i}':>4}" for i in range(1, len(sisi) + 1)))
for v, baris in zip(server, M):
    print(f"{v:>3} " + "".join(f"{x:>4}" for x in baris))

M_nx = nx.incidence_matrix(G, nodelist=server, edgelist=sisi).toarray().astype(int)
print("Sama dengan nx.incidence_matrix:", bool((M == M_nx).all()))
print("Jumlah angka 1 tiap kolom (harus 2):", sorted(set(M.sum(axis=0).tolist())))

derajat = dict(G.degree())
print("\nDerajat tiap server:", derajat)
print(f"Jumlah derajat = {sum(derajat.values())}, 2 x |E| = 2 x {len(sisi)} = {2 * len(sisi)}")
print("Handshaking Theorem terbukti:", sum(derajat.values()) == 2 * len(sisi))

H = G.copy()
H.remove_node("S1")
print("\nSimulasi server S1 mati:")
print(f"  Sisa simpul {H.number_of_nodes()}, sisa sisi {H.number_of_edges()} (hilang {len(sisi) - H.number_of_edges()} kabel)")
print(f"  Masih terhubung (connected)? {nx.is_connected(H)}")
print(f"  Sisa jaringan isomorfik dengan K5? {nx.is_isomorphic(H, nx.complete_graph(5))}")
print(f"  Node connectivity K6 = {nx.node_connectivity(G)}, edge connectivity K6 = {nx.edge_connectivity(G)}")

pos = nx.circular_layout(G)
fig, axes = plt.subplots(1, 2, figsize=(11, 5))
nx.draw(G, pos, ax=axes[0], with_labels=True, node_color="lightblue", edgecolors="black", node_size=700)
axes[0].set_title("Full-mesh 6 server (K6)")
nx.draw(H, pos, ax=axes[1], with_labels=True, node_color="lightblue", edgecolors="black", node_size=700)
nx.draw_networkx_nodes(G, pos, nodelist=["S1"], ax=axes[1], node_color="white", edgecolors="red",
                       node_size=700, linewidths=2)
nx.draw_networkx_labels(G, pos, labels={"S1": "S1"}, ax=axes[1], font_color="red")
axes[1].set_title("Setelah S1 mati (sisa K5)")
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task04_fullmesh.png"), dpi=150)
plt.show()
