"""Benchmark baseline vs SOTA max flow di semua skenario max flow.

Setiap algoritma menjalankan run() lalu seluruh event skenario. Waktu diambil median dari beberapa
ulangan supaya tidak terpengaruh noise. Hasil dicetak dan disimpan ke output/benchmark_maxflow.csv.

    python -m scripts.run_benchmark_maxflow
    python -m scripts.run_benchmark_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml --ulang 50
"""
import argparse
import csv
import statistics
import sys
import time

import algorithms  # noqa: F401
from algorithms.registry import AlgorithmRegistry
from cases.scenario_loader import ScenarioLoader
from config.settings import CASES_DIR, OUTPUT_DIR

KEYS = ["ford_fulkerson", "push_relabel", "dynamic_dinic"]


def sekali(yaml_path, key):
    loader = ScenarioLoader(yaml_path)
    model = loader.build_graph_model()
    plan = loader.get_execution_plan()
    s, t = plan["start_node"], plan["goal_node"]
    solver = AlgorithmRegistry.create(key, model)
    t0 = time.perf_counter()
    solver.run(s, t)
    t_awal = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    for ev in plan.get("events", []):
        solver.handle_dynamic_event({"edge": tuple(ev["target_edge"]), "new_capacity": ev["new_capacity"],
                                     "start": s, "goal": t})
    t_event = (time.perf_counter() - t0) * 1000
    hitung = {}
    for d in solver.delta_logs:
        hitung[d["event_type"]] = hitung.get(d["event_type"], 0) + 1
    return t_awal, t_event, solver, hitung, len(plan.get("events", []))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts.run_benchmark_maxflow")
    ap.add_argument("scenarios", nargs="*")
    ap.add_argument("--ulang", type=int, default=30)
    args = ap.parse_args(argv)
    if args.scenarios:
        files = [p for p in map(__import__("pathlib").Path, args.scenarios)]
    else:
        files = sorted(p for p in CASES_DIR.glob("*.yaml") if "DYNAMIC_EDGE_CAPACITY" in p.read_text(encoding="utf-8"))
    rows = []
    for f in files:
        for key in KEYS:
            awal, event = [], []
            for _ in range(args.ulang):
                a, e, solver, hitung, n_event = sekali(f, key)
                awal.append(a)
                event.append(e)
            rows.append({
                "case": f.stem, "algorithm": solver.__class__.__name__, "events": n_event,
                "steps": solver.step_count,
                "augmenting_paths": hitung.get("AUGMENTING_PATH_FOUND", 0),
                "push": hitung.get("PUSH", 0), "relabel": hitung.get("RELABEL", 0),
                "initial_ms": round(statistics.median(awal), 4), "events_ms": round(statistics.median(event), 4),
                "final_max_flow": round(solver.max_flow, 1),
            })
    print(f"\n{'Case':<40} {'Algorithm':<14} {'Ev':>3} {'Steps':>6} {'Aug':>5} {'Push':>5} {'Relab':>6} "
          f"{'Init ms':>9} {'Event ms':>9} {'MaxFlow':>9}")
    print("-" * 115)
    for r in rows:
        print(f"{r['case']:<40} {r['algorithm']:<14} {r['events']:>3} {r['steps']:>6} {r['augmenting_paths']:>5} "
              f"{r['push']:>5} {r['relabel']:>6} {r['initial_ms']:>9.3f} {r['events_ms']:>9.3f} "
              f"{r['final_max_flow']:>9.1f}")
    out = OUTPUT_DIR / "benchmark_maxflow.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n[SUCCESS] {out}")
    return rows


if __name__ == "__main__":
    main(sys.argv[1:])
