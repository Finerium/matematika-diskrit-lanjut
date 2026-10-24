"""Benchmark skala: keempat algoritma max flow di jaringan jalan kisi (grid) buatan yang makin besar.

Jaringan k x k berisi jalan dua arah antarsimpang tetangga, super source tersambung ke kolom kiri dan super sink
ke kolom kanan. Kapasitas acak 500 - 4.500 skr/jam (bilangan bulat, seed tetap), lalu 30 event perubahan
kapasitas acak. Gunanya melihat tren waktu dan jumlah langkah saat graf membesar, karena graf Gasibu
(18 node) terlalu kecil untuk membedakan kompleksitas algoritma.

    python -m scripts.run_benchmark_skala
    python -m scripts.run_benchmark_skala --ukuran 5 10 15 --ulang 3
"""
import argparse
import csv
import random
import statistics
import sys
import time

import algorithms  # noqa: F401
import networkx as nx
from algorithms.registry import AlgorithmRegistry
from config.settings import OUTPUT_DIR
from core.graph_model import SpatialGraphModel

KEYS = ["ford_fulkerson", "ford_fulkerson_dfs", "push_relabel", "dynamic_dinic"]
BATAS_DETIK = 30.0  # kalau satu ukuran lebih lama dari ini, ukuran berikutnya dilewati untuk algoritma itu


def jaringan_kisi(k, seed=2026, n_event=30):
    rng = random.Random(seed + k)
    G = nx.DiGraph()
    nid = lambda r, c: 1 + r * k + c  # noqa: E731
    s, t = 0, k * k + 1
    for r in range(k):
        for c in range(k):
            G.add_node(nid(r, c), label=f"Simpang {r},{c}", pos=(float(c + 1), float(-r)))
    G.add_node(s, label="Sumber", pos=(0.0, -k / 2))
    G.add_node(t, label="Tujuan", pos=(float(k + 1), -k / 2))
    for r in range(k):
        for c in range(k):
            for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < k and 0 <= cc < k:
                    G.add_edge(nid(r, c), nid(rr, cc), weight=1.0, capacity=float(rng.randint(500, 4500)))
        G.add_edge(s, nid(r, 0), weight=1.0, capacity=float(rng.randint(2000, 6000)))
        G.add_edge(nid(r, k - 1), t, weight=1.0, capacity=float(rng.randint(2000, 6000)))
    edges = list(G.edges())
    events = [(rng.choice(edges), float(rng.randint(0, 4500))) for _ in range(n_event)]
    return G, s, t, events


def sekali(key, k):
    G, s, t, events = jaringan_kisi(k)
    solver = AlgorithmRegistry.create(key, SpatialGraphModel(G))
    t0 = time.perf_counter()
    solver.run(s, t)
    awal = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    for e, c in events:
        solver.handle_dynamic_event({"edge": e, "new_capacity": c, "start": s, "goal": t})
    ev = (time.perf_counter() - t0) * 1000
    hitung = {}
    for d in solver.delta_logs:
        hitung[d["event_type"]] = hitung.get(d["event_type"], 0) + 1
    cek = nx.maximum_flow_value(G, s, t)
    assert abs(solver.max_flow - cek) < 1e-6, f"{key} salah di k={k}"
    return awal, ev, solver, hitung, G


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts.run_benchmark_skala")
    ap.add_argument("--ukuran", type=int, nargs="*", default=[5, 10, 15, 20])
    ap.add_argument("--ulang", type=int, default=3)
    args = ap.parse_args(argv)
    rows, dilewati = [], set()
    for k in args.ukuran:
        for key in KEYS:
            if key in dilewati:
                continue
            awal, ev = [], []
            for _ in range(args.ulang):
                a, e, solver, hitung, G = sekali(key, k)
                awal.append(a)
                ev.append(e)
            rows.append({"k": k, "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
                         "algorithm": solver.__class__.__name__,
                         "augmenting_paths": hitung.get("AUGMENTING_PATH_FOUND", 0),
                         "push": hitung.get("PUSH", 0), "relabel": hitung.get("RELABEL", 0),
                         "initial_ms": round(statistics.median(awal), 2), "events_ms": round(statistics.median(ev), 2),
                         "final_max_flow": round(solver.max_flow, 1)})
            r = rows[-1]
            print(f"k={k:>2} | {r['nodes']:>4} node {r['edges']:>5} edge | {r['algorithm']:<17} | "
                  f"awal {r['initial_ms']:>9.2f} ms | 30 event {r['events_ms']:>10.2f} ms | aug {r['augmenting_paths']:>6} "
                  f"push {r['push']:>7} relabel {r['relabel']:>6} | max flow {r['final_max_flow']:>9.1f}")
            if (statistics.median(awal) + statistics.median(ev)) / 1000 > BATAS_DETIK:
                dilewati.add(key)
                print(f"      {r['algorithm']} lebih dari {BATAS_DETIK:.0f} detik, ukuran berikutnya dilewati")
    out = OUTPUT_DIR / "benchmark_maxflow_skala.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n[SUCCESS] {out}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1:])
