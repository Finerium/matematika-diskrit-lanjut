# Nama  : Ghaisan Khoirul Badruzaman
# NIM   : 251524048
# Kelas : 2B-D4
# Modul 1 - Task02: Hello Networkx (latihan G1 sampai G5 dan tugas praktikum)

import os
import textwrap

import matplotlib.pyplot as plt
import networkx as nx

HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil")
os.makedirs(HASIL, exist_ok=True)


def analisis(G, nama):
    print(f"--- Analisis {nama} ---")
    print(f"Jumlah simpul : {G.number_of_nodes()}")
    print(f"Jumlah sisi   : {G.number_of_edges()}")
    if G.is_directed():
        isi = [f"{v} (masuk {G.in_degree(v)}, keluar {G.out_degree(v)})" for v in G.nodes()]
    else:
        isi = [f"{v} = {G.degree(v)}" for v in G.nodes()]
    print(textwrap.fill("Derajat : " + ", ".join(isi), width=90, subsequent_indent="          "))
    print()


def gambar(ax, G, pos, judul, warna="lightblue", ukuran=600, font=11, geser_label=0.0):
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=warna, node_size=ukuran, edgecolors="black")
    label_pos = {v: (x, y + geser_label) for v, (x, y) in pos.items()}
    # label diberi latar putih supaya tetap terbaca kalau tertimpa garis sisi
    latar = dict(facecolor="white", edgecolor="none", pad=0.3) if geser_label else None
    nx.draw_networkx_labels(G, label_pos, ax=ax, font_size=font, font_weight="bold", bbox=latar)
    if G.is_multigraph():
        # sisi ke-k antara dua simpul yang sama dibuat melengkung beda-beda supaya tidak menumpuk
        rad = [0.1, 0.35, -0.2, 0.55] if G.is_directed() else [0.0, 0.18, -0.18, 0.35]
        nx.draw_networkx_edges(G, pos, ax=ax, node_size=ukuran, arrows=True, arrowsize=18,
                               arrowstyle="-|>" if G.is_directed() else "-",
                               connectionstyle=[f"arc3,rad={r}" for r in rad])
    elif G.is_directed():
        nx.draw_networkx_edges(G, pos, ax=ax, node_size=ukuran, arrows=True, arrowsize=18)
    else:
        nx.draw_networkx_edges(G, pos, ax=ax, node_size=ukuran)
    ax.set_title(judul)
    ax.margins(x=0.06, y=0.2)
    ax.axis("off")


def simpan(fig, nama_file):
    fig.tight_layout()
    fig.savefig(os.path.join(HASIL, nama_file), dpi=150)
    plt.show()


def latihan():
    print("===== LATIHAN: JENIS-JENIS GRAF (GAMBAR 12) =====\n")
    pos = {"a": (0, 0), "b": (-1, 1), "c": (0, 2), "d": (1, 1)}

    G1 = nx.Graph()
    G1.add_edges_from([("a", "b"), ("a", "c"), ("b", "c"), ("c", "d"), ("d", "a")])

    # e4 dan e5 sama-sama menghubungkan c-d, e6 dan e7 sama-sama a-d
    G2 = nx.MultiGraph()
    G2.add_edges_from([("a", "b"), ("b", "c"), ("a", "c"), ("c", "d"), ("c", "d"), ("a", "d"), ("a", "d")])

    # graf semu = graf ganda G2 ditambah gelang e8 di simpul b
    G3 = nx.MultiGraph(G2)
    G3.add_edge("b", "b")

    G4 = nx.DiGraph()
    G4.add_edges_from([("a", "b"), ("b", "c"), ("a", "c"), ("d", "c"), ("d", "a")])

    G5 = nx.MultiDiGraph()
    G5.add_edges_from([("a", "b"), ("b", "c"), ("a", "c"), ("d", "c"), ("d", "c"),
                       ("a", "d"), ("d", "a"), ("b", "b")])

    daftar = [(G1, "G1 graf sederhana"), (G2, "G2 graf ganda"), (G3, "G3 graf semu"),
              (G4, "G4 graf berarah"), (G5, "G5 graf ganda berarah")]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for (G, nama), ax in zip(daftar, axes.flat):
        analisis(G, nama)
        gambar(ax, G, pos, nama, warna="lightgreen" if G.is_multigraph() else "lightblue")
    axes.flat[-1].axis("off")
    simpan(fig, "latihan_G1_G5.png")


def tugas():
    print("===== TUGAS PRAKTIKUM =====\n")

    # Figure 1 sampai 3: jaringan komputer antar data center
    kota = {"San Francisco": (0.5, 2.3), "Los Angeles": (1.0, 1.0), "Denver": (3.5, 2.2), "Chicago": (6.8, 3.0),
            "Detroit": (8.1, 3.4), "New York": (9.7, 3.2), "Washington": (9.2, 2.4)}
    jalur = [("San Francisco", "Los Angeles"), ("San Francisco", "Denver"), ("Los Angeles", "Denver"),
             ("Denver", "Chicago"), ("Chicago", "Detroit"), ("Chicago", "New York"), ("Chicago", "Washington"),
             ("Detroit", "New York"), ("New York", "Washington")]

    F1 = nx.Graph()
    F1.add_edges_from(jalur)

    # jalur ganda: LA-Denver, Denver-Chicago, Chicago-New York, New York-Washington
    F2 = nx.MultiGraph()
    F2.add_edges_from(jalur)
    F2.add_edges_from([("Los Angeles", "Denver"), ("Denver", "Chicago"), ("Chicago", "New York"),
                       ("New York", "Washington")])

    # diagnostic link = gelang di setiap data center
    F3 = nx.MultiGraph(F2)
    F3.add_edges_from((k, k) for k in kota)

    fig, axes = plt.subplots(3, 1, figsize=(11, 11))
    for G, nama, ax in [(F1, "Figure 1 jaringan komputer (graf sederhana)", axes[0]),
                        (F2, "Figure 2 jalur ganda antar data center (graf ganda)", axes[1]),
                        (F3, "Figure 3 dengan diagnostic link (graf semu)", axes[2])]:
        analisis(G, nama)
        gambar(ax, G, kota, nama, ukuran=120, font=9, geser_label=-0.3)  # label di bawah, gelang di atas
    simpan(fig, "tugas_figure1_3.png")

    # Figure 6: graf pertemanan
    orang = {"Eduardo": (7.5, -1.3), "Jan": (3.1, -2.6), "Paula": (6.2, -2.6), "Todd": (9.2, -2.6),
             "Kamlesh": (12.2, -2.6), "Kamini": (2.0, -3.2), "Ching": (12.2, -3.2), "Amy": (7.7, -3.6),
             "Lila": (3.1, -4.6), "Liz": (6.2, -4.6), "Steve": (9.2, -4.6), "Joel": (3.1, -5.5),
             "Gail": (6.2, -5.5), "Koko": (10.7, -5.7), "Kari": (3.1, -6.4), "Shaquira": (9.2, -6.4)}
    kenal = [("Jan", "Kamini"), ("Jan", "Paula"), ("Jan", "Lila"), ("Jan", "Joel"), ("Paula", "Eduardo"),
             ("Paula", "Todd"), ("Paula", "Liz"), ("Paula", "Lila"), ("Paula", "Joel"), ("Paula", "Amy"),
             ("Amy", "Steve"), ("Steve", "Koko"), ("Todd", "Amy"), ("Amy", "Liz"), ("Todd", "Kamlesh"),
             ("Kamlesh", "Ching"), ("Todd", "Steve"), ("Lila", "Liz"), ("Liz", "Steve"), ("Lila", "Joel"),
             ("Lila", "Gail"), ("Gail", "Shaquira"), ("Joel", "Gail"), ("Joel", "Kari"), ("Steve", "Shaquira")]
    F6 = nx.Graph()
    F6.add_edges_from(kenal)
    analisis(F6, "Figure 6 graf pertemanan")

    fig, ax = plt.subplots(figsize=(11, 6))
    lurus = [e for e in kenal if e != ("Jan", "Joel")]
    nx.draw_networkx_nodes(F6, orang, ax=ax, node_color="lightblue", node_size=120, edgecolors="black")
    nx.draw_networkx_labels(F6, {v: (x, y + 0.3) for v, (x, y) in orang.items()}, ax=ax, font_size=9,
                            bbox=dict(facecolor="white", edgecolor="none", pad=0.3))
    nx.draw_networkx_edges(F6, orang, ax=ax, edgelist=lurus, node_size=120)
    # Jan-Joel segaris dengan Jan-Lila-Joel, jadi digambar melengkung supaya tidak tertutup
    nx.draw_networkx_edges(F6, orang, ax=ax, edgelist=[("Jan", "Joel")], node_size=120, arrows=True,
                           arrowstyle="-", connectionstyle="arc3,rad=0.3")
    ax.set_title("Figure 6 graf pertemanan (acquaintanceship graph)")
    ax.axis("off")
    simpan(fig, "tugas_figure6.png")

    # Figure 13: jaringan semantik kata yang maknanya dekat dengan "mouse"
    kata = {"Printer": (6.0, 0.8), "Wolf": (0.9, 1.7), "Fox": (1.8, 2.1), "Desktop": (5.5, 1.9),
            "Laptop": (7.6, 1.7), "Tablet": (8.9, 1.7), "Dog": (1.2, 2.9), "Rabbit": (2.4, 2.8),
            "Router": (7.7, 2.8), "Keyboard": (6.0, 2.9), "Cat": (1.1, 3.9), "Rat": (2.1, 3.6),
            "Mouse": (4.0, 3.8), "Trackpad": (6.9, 3.7), "Duck": (1.5, 4.8), "Lizard": (3.0, 4.9),
            "Turtle": (1.9, 5.6), "Fly": (3.9, 6.0), "Spider": (2.7, 6.4), "Cockroach": (3.7, 7.1)}
    kata = {k: (x, -y) for k, (x, y) in kata.items()}
    mirip = [("Wolf", "Fox"), ("Fox", "Dog"), ("Fox", "Rabbit"), ("Dog", "Rabbit"), ("Dog", "Cat"), ("Dog", "Rat"),
             ("Cat", "Rat"), ("Rat", "Mouse"), ("Rabbit", "Mouse"), ("Mouse", "Desktop"), ("Mouse", "Keyboard"),
             ("Mouse", "Trackpad"), ("Mouse", "Lizard"), ("Lizard", "Duck"), ("Lizard", "Turtle"),
             ("Lizard", "Fly"), ("Fly", "Spider"), ("Fly", "Cockroach"), ("Desktop", "Printer"),
             ("Desktop", "Laptop"), ("Desktop", "Router"), ("Desktop", "Keyboard"), ("Printer", "Laptop"),
             ("Printer", "Router"), ("Laptop", "Tablet"), ("Laptop", "Router"), ("Laptop", "Keyboard"),
             ("Keyboard", "Trackpad")]
    F13 = nx.Graph()
    F13.add_edges_from(mirip)
    analisis(F13, "Figure 13 jaringan semantik kata mouse")

    fig, ax = plt.subplots(figsize=(10, 7))
    gambar(ax, F13, kata, "Figure 13 jaringan semantik kata \"mouse\"", ukuran=120, font=9, geser_label=0.22)
    simpan(fig, "tugas_figure13.png")

    # Figure 15: turnamen sistem gugur, tiap simpul adalah satu pertandingan
    laga = {"Stanford vs Georgia": (0, 7), "Xavier vs Gonzaga": (0, 5), "Oklahoma vs Notre Dame": (0, 3),
            "Kentucky vs Nebraska": (0, 1), "Stanford vs Xavier": (1, 6), "Oklahoma vs Kentucky": (1, 2),
            "Stanford vs Oklahoma": (2, 4), "Connecticut vs Stanford": (3, 4), "Connecticut vs Baylor": (4, 4),
            "Connecticut vs Florida State": (5, 6), "Baylor vs Duke": (5, 2),
            "Connecticut vs Iowa State": (6, 7), "Florida State vs Mississippi State": (6, 5),
            "Baylor vs Tennessee": (6, 3), "Duke vs San Diego State": (6, 1)}
    lanjut = [("Stanford vs Georgia", "Stanford vs Xavier"), ("Xavier vs Gonzaga", "Stanford vs Xavier"),
              ("Oklahoma vs Notre Dame", "Oklahoma vs Kentucky"), ("Kentucky vs Nebraska", "Oklahoma vs Kentucky"),
              ("Stanford vs Xavier", "Stanford vs Oklahoma"), ("Oklahoma vs Kentucky", "Stanford vs Oklahoma"),
              ("Stanford vs Oklahoma", "Connecticut vs Stanford"), ("Connecticut vs Baylor", "Connecticut vs Stanford"),
              ("Connecticut vs Florida State", "Connecticut vs Baylor"), ("Baylor vs Duke", "Connecticut vs Baylor"),
              ("Connecticut vs Iowa State", "Connecticut vs Florida State"),
              ("Florida State vs Mississippi State", "Connecticut vs Florida State"),
              ("Baylor vs Tennessee", "Baylor vs Duke"), ("Duke vs San Diego State", "Baylor vs Duke")]
    F15 = nx.Graph()
    F15.add_edges_from(lanjut)
    analisis(F15, "Figure 15 turnamen sistem gugur")
    print(f"Apakah graf berbentuk pohon (tree)? {nx.is_tree(F15)}")
    # nama sebelum "vs" adalah pemenang, jadi juara diambil dari pertandingan final
    final = "Connecticut vs Stanford"
    print(f"Pertandingan final: {final}, derajat {F15.degree(final)}")
    print(f"Juara turnamen: {final.split(' vs ')[0]}\n")

    fig, ax = plt.subplots(figsize=(13, 6))
    label = {v: v.replace(" vs ", "\nvs ") for v in F15.nodes()}
    nx.draw_networkx_nodes(F15, laga, ax=ax, node_color="gold", node_size=180, edgecolors="black")
    nx.draw_networkx_edges(F15, laga, ax=ax, node_size=180)
    nx.draw_networkx_labels(F15, {v: (x, y + 0.45) for v, (x, y) in laga.items()}, labels=label, ax=ax, font_size=8)
    ax.set_title("Figure 15 turnamen sistem gugur (pemenang ditulis di depan)")
    ax.axis("off")
    simpan(fig, "tugas_figure15.png")


if __name__ == "__main__":
    latihan()
    tugas()
