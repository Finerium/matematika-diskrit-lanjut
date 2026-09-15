# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 2 - Task02: derajat, Handshaking Theorem, adjacency list, dan adjacency matrix
# Soal tidak menyebut grafnya, jadi yang dianalisis tiga graf dari Task01 (K4, C5, W6).

import networkx as nx


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
        print(f"  {v}: {list(G.neighbors(v))}")

    print("Adjacency matrix:")
    M = nx.to_numpy_array(G, dtype=int)
    cetak_matriks(M, list(G.nodes()))
    # jumlah angka 1 di tiap baris harus sama dengan derajat simpul itu
    print("Jumlah tiap baris :", [int(x) for x in M.sum(axis=1)])
    print("Matriks simetris  :", bool((M == M.T).all()))
    print()


analisis(nx.complete_graph(4), "Graf lengkap K4")
analisis(nx.cycle_graph(5), "Graf lingkaran C5")
analisis(nx.wheel_graph(7), "Graf roda W6 (simpul 0 = pusat)")
