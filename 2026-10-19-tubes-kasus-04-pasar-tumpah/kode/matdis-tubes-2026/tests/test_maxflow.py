"""Tes kebenaran algoritma max flow (baseline Ford-Fulkerson/Edmonds-Karp, SOTA Push-Relabel, dan Dinic).

Pembanding: networkx.maximum_flow_value. Yang dicek di setiap skenario dan setiap event:
nilai max flow, batas kapasitas, konservasi aliran, dan teorema max-flow min-cut.
"""
import random

import networkx as nx
import pytest

import algorithms  # noqa: F401  (mendaftarkan semua algoritma ke registry)
from algorithms.registry import AlgorithmRegistry
from cases.scenario_loader import ScenarioLoader
from config.settings import CASES_DIR
from core.graph_model import SpatialGraphModel
from tests.test_scaffolding import SOTAScaffoldingAuditor

MAXFLOW_KEYS = ["ford_fulkerson", "push_relabel", "dynamic_dinic"]
SCENARIOS = sorted(p for p in CASES_DIR.glob("*.yaml") if "DYNAMIC_EDGE_CAPACITY" in p.read_text(encoding="utf-8"))
GASIBU = CASES_DIR / "case_04_pasar_tumpah_gasibu.yaml"


def _cek_aliran(solver, G, s, t, nilai):
    assert nilai == pytest.approx(nx.maximum_flow_value(G, s, t), abs=1e-6)
    for (u, v), f in solver.flow.items():
        assert -1e-7 <= f <= G[u][v]["capacity"] + 1e-7, f"aliran {u}->{v} melanggar kapasitas"
    for x in G.nodes():
        if x in (s, t):
            continue
        masuk = sum(solver.flow.get((a, x), 0.0) for a in G.predecessors(x))
        keluar = sum(solver.flow.get((x, b), 0.0) for b in G.successors(x))
        assert masuk == pytest.approx(keluar, abs=1e-6), f"konservasi gagal di node {x}"
    potong = sum(G[u][v]["capacity"] for u, v in solver.min_cut_edges)
    assert potong == pytest.approx(nilai, abs=1e-6), "kapasitas min cut harus sama dengan max flow"


@pytest.mark.parametrize("key", MAXFLOW_KEYS)
@pytest.mark.parametrize("yaml_path", SCENARIOS, ids=lambda p: p.stem)
def test_maxflow_tiap_skenario_dan_event(yaml_path, key):
    loader = ScenarioLoader(yaml_path)
    model = loader.build_graph_model()
    plan = loader.get_execution_plan()
    s, t = plan["start_node"], plan["goal_node"]
    solver = AlgorithmRegistry.create(key, model)

    path, nilai = solver.run(s, t)
    assert path[0] == s and path[-1] == t
    _cek_aliran(solver, model.nx_graph, s, t, nilai)

    for event in plan.get("events", []):
        path, nilai = solver.handle_dynamic_event({
            "edge": tuple(event["target_edge"]),
            "new_capacity": event["new_capacity"],
            "description": event.get("description", ""),
            "start": s,
            "goal": t,
        })
        _cek_aliran(solver, model.nx_graph, s, t, nilai)
    assert len(solver.delta_logs) == solver.step_count > 0


def test_hasil_kasus_gasibu():
    """Angka yang dipakai di slide: normal 5.055,1, puncak pasar 3.296,9, setelah pasar bubar kembali 5.055,1."""
    loader = ScenarioLoader(GASIBU)
    model = loader.build_graph_model()
    plan = loader.get_execution_plan()
    solver = AlgorithmRegistry.create("maxflow", model)
    s, t = plan["start_node"], plan["goal_node"]
    _, normal = solver.run(s, t)
    assert normal == pytest.approx(5055.1, abs=0.05)
    # E09 (6 -> 7) dan E10 (7 -> 9) seri dengan kapasitas sama, min cut yang dilaporkan adalah yang paling dekat
    # ke source (himpunan simpul yang terjangkau dari source di residual graph, sama untuk max flow apa pun)
    assert sorted(solver.min_cut_edges) == [(3, 8), (6, 7)]
    hasil = []
    for event in plan["events"]:
        _, nilai = solver.handle_dynamic_event({"edge": tuple(event["target_edge"]),
                                                "new_capacity": event["new_capacity"], "start": s, "goal": t})
        hasil.append((event["time"], round(nilai, 1)))
    puncak = min(v for _, v in hasil)
    assert puncak == pytest.approx(3296.9, abs=0.05)
    assert hasil[-1][1] == pytest.approx(5055.1, abs=0.05)


def test_min_cut_sama_di_semua_algoritma():
    """Min cut yang dilaporkan (sisi S paling dekat ke source) harus sama untuk ketiga algoritma setelah run()
    dan setelah setiap event. Skenario penataan berakhir di 4.817,5 (angka slide)."""
    for yaml_path, akhir in [(GASIBU, 5055.1), (CASES_DIR / "case_04_pasar_tumpah_gasibu_penataan.yaml", 4817.5)]:
        jejak = {}
        for key in MAXFLOW_KEYS:
            loader = ScenarioLoader(yaml_path)
            plan = loader.get_execution_plan()
            solver = AlgorithmRegistry.create(key, loader.build_graph_model())
            s, t = plan["start_node"], plan["goal_node"]
            _, nilai = solver.run(s, t)
            catat = [(sorted(solver.min_cut_edges), sorted(solver.source_side))]
            for event in plan["events"]:
                _, nilai = solver.handle_dynamic_event({"edge": tuple(event["target_edge"]),
                                                        "new_capacity": event["new_capacity"], "start": s, "goal": t})
                catat.append((sorted(solver.min_cut_edges), sorted(solver.source_side)))
            assert nilai == pytest.approx(akhir, abs=0.05)
            jejak[key] = catat
        assert jejak["ford_fulkerson"] == jejak["push_relabel"] == jejak["dynamic_dinic"]


@pytest.mark.parametrize("key", MAXFLOW_KEYS)
def test_graf_acak_dengan_event(key):
    rng = random.Random(2026)
    for _ in range(120):
        n = rng.randint(3, 9)
        G = nx.gnp_random_graph(n, rng.choice([0.3, 0.5, 0.8]), directed=True, seed=rng.randint(0, 10**6))
        for u, v in G.edges():
            G[u][v]["capacity"] = float(rng.randint(0, 25))
            G[u][v]["weight"] = 1.0
        solver = AlgorithmRegistry.create(key, SpatialGraphModel(G))
        _, nilai = solver.run(0, n - 1)
        _cek_aliran(solver, G, 0, n - 1, nilai)
        for _ in range(6):
            if G.number_of_edges() == 0:
                break
            e = rng.choice(list(G.edges()))
            _, nilai = solver.handle_dynamic_event({"edge": e, "new_capacity": float(rng.randint(0, 25)),
                                                    "start": 0, "goal": n - 1})
            _cek_aliran(solver, G, 0, n - 1, nilai)


@pytest.mark.parametrize("key", ["push_relabel", "dynamic_dinic"])
def test_audit_sota_di_kasus_gasibu(key):
    kelas = AlgorithmRegistry._algorithms[key]
    auditor = SOTAScaffoldingAuditor(kelas, str(GASIBU))
    assert auditor.run_full_diagnostic() is True


def test_sota_lebih_hemat_dari_baseline():
    """Versi dinamis melanjutkan aliran lama, jadi total langkahnya harus lebih sedikit dari hitung ulang."""
    langkah = {}
    for key in ["ford_fulkerson", "dynamic_dinic"]:
        loader = ScenarioLoader(GASIBU)
        model = loader.build_graph_model()
        plan = loader.get_execution_plan()
        solver = AlgorithmRegistry.create(key, model)
        s, t = plan["start_node"], plan["goal_node"]
        solver.run(s, t)
        for event in plan["events"]:
            solver.handle_dynamic_event({"edge": tuple(event["target_edge"]),
                                         "new_capacity": event["new_capacity"], "start": s, "goal": t})
        langkah[key] = sum(1 for d in solver.delta_logs if d["event_type"] == "AUGMENTING_PATH_FOUND")
    assert langkah["dynamic_dinic"] < langkah["ford_fulkerson"]
