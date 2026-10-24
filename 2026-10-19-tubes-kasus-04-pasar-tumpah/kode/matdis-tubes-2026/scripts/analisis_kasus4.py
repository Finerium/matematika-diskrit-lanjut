"""Analisis tambahan Kasus 4 Gasibu di atas skenario YAML (tanpa GUI).

1. Akses kendaraan berat: max flow seluruh jaringan dibanding subgraf yang boleh dilewati bus dan truk
   (edge dengan heavy_vehicle: true, yaitu jalan arteri dan kolektor).
2. Sensitivitas edge: kenaikan max flow kalau satu edge (atau pasangan edge seri) tidak lagi membatasi.

Kondisi normal = kapasitas awal YAML, puncak pasar = setelah semua event lapak buka (sampai 07.30),
penataan = setelah semua event di skenario penataan.

    python -m scripts.analisis_kasus4
"""
import csv

import algorithms  # noqa: F401
import networkx as nx
import yaml
from algorithms.registry import AlgorithmRegistry
from config.settings import CASES_DIR, OUTPUT_DIR
from core.graph_model import SpatialGraphModel

GASIBU = CASES_DIR / "case_04_pasar_tumpah_gasibu.yaml"
PENATAAN = CASES_DIR / "case_04_pasar_tumpah_gasibu_penataan.yaml"
PASANGAN_SERI = [("E09", "E10"), ("E12", "E09", "E10")]


def angka(x):
    return f"{x:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def kode(label):
    return label.split(" ")[0]


def kondisi():
    """Kembalikan data YAML dan kapasitas tiap edge untuk tiga kondisi, dikunci dengan kode edge (E01 dst)."""
    data = yaml.safe_load(GASIBU.read_text(encoding="utf-8"))
    awal = {kode(e["label"]): e["capacity"] for e in data["edges"]}
    per_id = {(e["from"], e["to"]): kode(e["label"]) for e in data["edges"]}
    pasar = dict(awal)
    for ev in data["execution_plan"]["events"]:
        if ev["time"] == "11.00":
            break
        pasar[per_id[tuple(ev["target_edge"])]] = ev["new_capacity"]
    penataan = dict(awal)
    for ev in yaml.safe_load(PENATAAN.read_text(encoding="utf-8"))["execution_plan"]["events"]:
        penataan[per_id[tuple(ev["target_edge"])]] = ev["new_capacity"]
    return data, {"normal": awal, "pasar": pasar, "penataan": penataan}


def max_flow(data, kapasitas, filter_edge=lambda e: True, key="push_relabel"):
    G = nx.DiGraph()
    for n in data["nodes"]:
        G.add_node(n["id"], label=n["label"], pos=tuple(n["pos"]))
    for e in data["edges"]:
        if filter_edge(e):
            G.add_edge(e["from"], e["to"], weight=e["weight"], capacity=float(kapasitas[kode(e["label"])]),
                       label=e["label"])
    s, t = data["execution_plan"]["start_node"], data["execution_plan"]["goal_node"]
    solver = AlgorithmRegistry.create(key, SpatialGraphModel(G))
    _, nilai = solver.run(s, t)
    cut = [kode(G[u][v]["label"]) for u, v in solver.min_cut_edges if G[u][v]["capacity"] > 0]
    return nilai, cut


def akses_kendaraan_berat(data, kap):
    rows = []
    for nama, c in kap.items():
        semua, cut_semua = max_flow(data, c)
        berat, cut_berat = max_flow(data, c, lambda e: e.get("heavy_vehicle", True))
        rows.append({"kondisi": nama, "max_flow_semua": round(semua, 1), "min_cut_semua": " + ".join(cut_semua),
                     "max_flow_kendaraan_berat": round(berat, 1), "min_cut_kendaraan_berat": " + ".join(cut_berat),
                     "hanya_mobil_dan_motor": round(semua - berat, 1)})
    return rows


def sensitivitas(data, kap):
    besar = sum(kap["normal"].values())          # cukup besar supaya edge itu tidak pernah membatasi
    rows = []
    for nama in ("normal", "pasar"):
        dasar, _ = max_flow(data, kap[nama])
        kelompok = [(k,) for k in kap[nama]] + PASANGAN_SERI
        for grup in kelompok:
            c = dict(kap[nama])
            for k in grup:
                c[k] = besar
            nilai, cut = max_flow(data, c)
            if nilai - dasar > 0.05 or len(grup) > 1:
                rows.append({"kondisi": nama, "edge_dilepas": " + ".join(grup), "max_flow_awal": round(dasar, 1),
                             "max_flow_baru": round(nilai, 1), "kenaikan": round(nilai - dasar, 1),
                             "pembatas_berikutnya": " + ".join(cut)})
    return rows


def simpan(nama, rows):
    path = OUTPUT_DIR / nama
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def main():
    data, kap = kondisi()
    print("=== 1. Akses kendaraan berat (bus dan truk hanya di jalan arteri dan kolektor) ===")
    print(f"{'Kondisi':<10} {'Semua':>9}  {'Min cut':<14} {'Kend. berat':>11}  {'Min cut':<9} {'Selisih':>8}")
    a = akses_kendaraan_berat(data, kap)
    for r in a:
        print(f"{r['kondisi']:<10} {angka(r['max_flow_semua']):>9}  {r['min_cut_semua']:<14} "
              f"{angka(r['max_flow_kendaraan_berat']):>11}  {r['min_cut_kendaraan_berat']:<9} "
              f"{angka(r['hanya_mobil_dan_motor']):>8}")
    print("\n=== 2. Sensitivitas: edge dibuat tidak membatasi ===")
    print(f"{'Kondisi':<8} {'Edge':<14} {'Awal':>8} {'Baru':>8} {'Naik':>8}  Pembatas berikutnya")
    s = sensitivitas(data, kap)
    for r in s:
        print(f"{r['kondisi']:<8} {r['edge_dilepas']:<14} {angka(r['max_flow_awal']):>8} {angka(r['max_flow_baru']):>8} "
              f"{angka(r['kenaikan']):>8}  {r['pembatas_berikutnya']}")
    print(f"\n[SUCCESS] {simpan('analisis_kasus4_akses.csv', a)}")
    print(f"[SUCCESS] {simpan('analisis_kasus4_sensitivitas.csv', s)}")
    return a, s


if __name__ == "__main__":
    main()
