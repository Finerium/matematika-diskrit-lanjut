# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task02: derajat, Handshaking Theorem, adjacency list, dan adjacency matrix
# Graf utama dari berkas Task02_Individu.py bawaan dosen (graf semu G3), ditambah K4, C5, dan W6 dari Task01.

import os

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")


def cetak_matriks(M, label):
    print("     " + " ".join(f"{v:>2}" for v in label))
    for v, baris in zip(label, M):
        print(f"  {v:>2} " + " ".join(f"{int(x):>2}" for x in baris))


def analisis(G, nama):
    print(f"===== {nama} =====")
    derajat = dict(G.degree())
    print("Derajat tiap simpul:", derajat)

    total = sum(derajat.values())
    m = G.number_of_edges()
    print(f"Jumlah derajat = {total}, 2 x |E| = 2 x {m} = {2 * m}")
    print("Handshaking Theorem terbukti\n" if total == 2 * m else "Handshaking Theorem TIDAK terpenuhi\n")

    print("Adjacency list:")
    for v in G.nodes():
        # pada multigraf tetangga ditulis berulang sebanyak sisinya
        print(f"  {v}: {[u for _, u in G.edges(v)]}")

    print("Adjacency matrix:")
    label = list(G.nodes())
    M = nx.to_numpy_array(G, nodelist=label, dtype=int)
    cetak_matriks(M, label)
    # gelang ditulis 1 di diagonal padahal menambah derajat 2, jadi diagonal ikut dihitung sekali lagi
    dari_matriks = [int(M[i].sum() + M[i, i]) for i in range(len(label))]
    print("Derajat dari matriks :", dict(zip(label, dari_matriks)))
    print("Sama dengan degree() :", dari_matriks == [derajat[v] for v in label])
    print("Matriks simetris     :", bool((M == M.T).all()))
    print()


# graf semu G3 dari berkas bawaan dosen: sisi ganda a-d dan c-d, gelang di c
G3 = nx.MultiGraph()
G3.add_nodes_from(["a", "b", "c", "d"])
G3.add_edges_from([("a", "b"), ("a", "d"), ("a", "d"), ("b", "c"), ("c", "c"), ("c", "d"), ("c", "d")])

analisis(G3, "Graf semu G3")
analisis(nx.complete_graph(4), "Graf lengkap K4")
analisis(nx.cycle_graph(5), "Graf lingkaran C5")
analisis(nx.wheel_graph(7), "Graf roda W6 (simpul 0 = pusat)")

# sisi kedua dari pasangan yang sama dibuat melengkung supaya tidak menumpuk
pos = {"a": (0, 0), "b": (0, 1), "c": (1, 1), "d": (1, 0)}
fig, ax = plt.subplots(figsize=(5, 4.6))
nx.draw_networkx_nodes(G3, pos, node_color="lightgreen", node_size=900, ax=ax)
nx.draw_networkx_labels(G3, pos, font_size=13, font_weight="bold", ax=ax)
tanpa_gelang = [(u, v, k) for u, v, k in G3.edges(keys=True) if u != v]
nx.draw_networkx_edges(G3, pos, edgelist=tanpa_gelang, ax=ax, width=2, arrows=True, arrowstyle="-", node_size=900,
                       connectionstyle=["arc3,rad=0.0", "arc3,rad=0.3"])
# gelang bawaan NetworkX tertutup simpul yang besar, jadi gelang di c digambar manual sebagai lingkaran
ax.add_patch(plt.Circle((1.1, 1.13), 0.12, fill=False, linewidth=2, zorder=0))
ax.set_title("Graf semu G3 dari berkas Task02 bawaan")
ax.axis("off")
ax.margins(0.25)
fig.tight_layout()
fig.savefig(os.path.join(HASIL, "task02_graf_semu_g3.png"), dpi=150)
