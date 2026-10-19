"""Runner analisis max flow (tanpa GUI): jalankan skenario, catat max flow tiap event, simpan trace JSON,
tabel CSV, dan gambar snapshot ke folder output/.

Contoh:
    python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml
    python -m scripts.run_maxflow cases/scenarios/case_04_pasar_tumpah_gasibu.yaml -a ford_fulkerson
"""
import argparse
import csv
import sys
from typing import List, Optional

import algorithms  # noqa: F401
from algorithms.registry import AlgorithmRegistry, resolve_algorithm_key
from cases.scenario_loader import ScenarioLoader
from config.settings import OUTPUT_DIR
from core.maxflow_visualizer import MaxFlowSnapshotVisualizer
from scripts.cli_utils import collect_scenario_paths


def angka(x):
    return f"{x:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")


def run_single(yaml_path, algorithm_override=None, gambar=True):
    loader = ScenarioLoader(yaml_path)
    meta = loader.get_metadata()
    plan = loader.get_execution_plan()
    model = loader.build_graph_model()
    key = resolve_algorithm_key(algorithm_override, plan, meta, "maxflow")
    solver = AlgorithmRegistry.create(key, model)
    G = model.nx_graph
    s, t = plan["start_node"], plan["goal_node"]
    nama = solver.__class__.__name__
    folder = OUTPUT_DIR / f"{meta['case_id']}_{key}"
    folder.mkdir(parents=True, exist_ok=True)
    viz = MaxFlowSnapshotVisualizer(G)

    def label_busur(u, v):
        return G[u][v].get("label", f"{u}->{v}")

    def cut_text():
        # busur berkapasitas 0 (ruas ditutup) ikut himpunan potong tapi tidak menyumbang kapasitas
        return "; ".join(label_busur(u, v).split(" ")[0] for u, v in solver.min_cut_edges
                         if G[u][v].get("capacity", 0.0) > 0)

    print(f"=== {meta['title']} ===")
    print(f"Algoritma: {nama} | simpul: {G.number_of_nodes()} | busur: {G.number_of_edges()}")
    _, nilai = solver.run(s, t)
    baris = [{"step": 0, "time": "-", "edge": "-", "old_capacity": "", "new_capacity": "",
              "max_flow": round(nilai, 1), "min_cut": cut_text(), "description": "Kondisi awal"}]
    print(f"[awal]  max flow = {angka(nilai)} skr/jam | min cut: {cut_text()}")
    if gambar:
        viz.save(folder / "00_awal.png", f"{meta['case_id']} - kondisi awal ({nama})", solver.flow,
                 solver.min_cut_edges, nilai)
    sebelumnya = nilai
    for k, ev in enumerate(plan.get("events", []), 1):
        u, v = ev["target_edge"]
        lama = G[u][v].get("capacity", 0.0)
        _, nilai = solver.handle_dynamic_event({"edge": (u, v), "new_capacity": ev["new_capacity"],
                                                "description": ev.get("description", ""), "start": s, "goal": t})
        baris.append({"step": k, "time": ev.get("time", ""), "edge": label_busur(u, v), "old_capacity": lama,
                      "new_capacity": ev["new_capacity"], "max_flow": round(nilai, 1), "min_cut": cut_text(),
                      "description": ev.get("description", "")})
        tanda = "  <- berubah" if abs(nilai - sebelumnya) > 1e-6 else ""
        print(f"[{ev.get('time', k):>5}] {label_busur(u, v).split(' ')[0]:<4} {angka(lama):>8} -> "
              f"{angka(ev['new_capacity']):>8} | max flow = {angka(nilai):>8}{tanda}")
        if gambar and abs(nilai - sebelumnya) > 1e-6:
            viz.save(folder / f"{k:02d}_event.png", f"Event {k} ({ev.get('time', '')}): {label_busur(u, v)}",
                     solver.flow, solver.min_cut_edges, nilai, highlighted_edge=(u, v))
        sebelumnya = nilai
    if gambar:
        viz.save(folder / "99_akhir.png", f"{meta['case_id']} - kondisi akhir ({nama})", solver.flow,
                 solver.min_cut_edges, nilai)

    with open(folder / "timeline_max_flow.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(baris[0].keys()))
        w.writeheader()
        w.writerows(baris)
    trace = solver.export_trace_json(
        f"output_{meta['case_id']}_{key}.json",
        metadata={**meta, "algorithm": nama, "registry_key": key,
                  "timeline_max_flow": [{k: r[k] for k in ("step", "time", "max_flow", "min_cut")} for r in baris]},
    )
    print(f"[SUCCESS] trace: {trace}")
    print(f"[SUCCESS] tabel dan gambar: {folder}")
    return baris, solver


def main(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(prog="scripts.run_maxflow", description="Analisis max flow berbasis skenario YAML.")
    ap.add_argument("scenarios", nargs="*", help="file YAML atau folder skenario")
    ap.add_argument("-a", "--algorithm", default=None, help="ford_fulkerson, push_relabel (maxflow), dynamic_dinic")
    ap.add_argument("--tanpa-gambar", action="store_true", help="lewati pembuatan PNG")
    args = ap.parse_args(argv)
    for p in collect_scenario_paths(args.scenarios):
        run_single(p, args.algorithm, gambar=not args.tanpa_gambar)


if __name__ == "__main__":
    main(sys.argv[1:])
