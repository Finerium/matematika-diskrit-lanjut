from collections import deque
from typing import Dict, List, Tuple

from algorithms.registry import AlgorithmRegistry
from core.base_algorithm import BaseGraphAlgorithm
from core.graph_model import SpatialGraphModel

EPS = 1e-9


def angka(x: float) -> str:
    """Format angka gaya Indonesia: 2.566,1"""
    s = f"{x:,.1f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


class FordFulkerson(BaseGraphAlgorithm):
    """Algoritma Dasar Maximum Flow (Ford-Fulkerson varian Edmonds-Karp, augmenting path dicari dengan BFS).

    Aliran disimpan per edge asli di self.flow. Kapasitas residual u -> v dihitung sebagai
    c(u, v) - f(u, v) + f(v, u), jadi graf yang punya edge bolak-balik tetap benar.
    """

    SUPPORTED_EVENT_TYPES = frozenset({"DYNAMIC_EDGE_CAPACITY"})
    # kalimat pembuka narasi saat algoritma selesai (Push-Relabel tidak memakai augmenting path)
    KALIMAT_SELESAI = "Tidak ada lagi augmenting path."

    def __init__(self, model: SpatialGraphModel):
        super().__init__(model)
        self.flow: Dict[Tuple[int, int], float] = {}
        self.max_flow = 0.0
        self.source = None
        self.sink = None
        self.augmenting_paths: List[Dict] = []
        self.min_cut_edges: List[Tuple[int, int]] = []
        self.source_side: List[int] = []

    # ------------------------------------------------------------------ helper graf
    def capacity(self, u, v) -> float:
        data = self.graph[u][v]
        return float(data.get("capacity", data.get("weight", 1.0)))

    def residual(self, u, v) -> float:
        r = 0.0
        if self.graph.has_edge(u, v):
            r += self.capacity(u, v) - self.flow.get((u, v), 0.0)
        if self.graph.has_edge(v, u):
            r += self.flow.get((v, u), 0.0)
        return r

    def residual_neighbors(self, u):
        for v in self.graph.successors(u):
            yield v
        for v in self.graph.predecessors(u):
            if not self.graph.has_edge(u, v):
                yield v

    def push_along(self, u, v, amount: float):
        """Tambah aliran u -> v sebesar amount, batalkan aliran balik v -> u lebih dulu kalau ada."""
        if self.graph.has_edge(v, u):
            batal = min(amount, self.flow.get((v, u), 0.0))
            self.flow[(v, u)] = self.flow.get((v, u), 0.0) - batal
            amount -= batal
        if amount > EPS:
            self.flow[(u, v)] = self.flow.get((u, v), 0.0) + amount

    def label(self, node) -> str:
        return self.graph.nodes[node].get("label", f"Node {node}")

    def edge_text(self, u, v) -> str:
        """Nama busur untuk narasi. Busur residual balik (v -> u) disebut sebagai pembatalan aliran."""
        if self.graph.has_edge(u, v):
            return self.model.get_edge_label(u, v)
        return f"arah balik {self.model.get_edge_label(v, u)} (pembatalan aliran)"

    def path_text(self, path) -> str:
        return " -> ".join(str(n) for n in path)

    def bottleneck_edge(self, path):
        pairs = list(zip(path[:-1], path[1:]))
        return min(pairs, key=lambda e: self.residual(*e))

    # ------------------------------------------------------------------ BFS (Edmonds-Karp)
    def _bfs(self, source, sink, parent) -> bool:
        visited = {source}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in self.residual_neighbors(u):
                if v not in visited and self.residual(u, v) > EPS:
                    visited.add(v)
                    parent[v] = u
                    if v == sink:
                        return True
                    queue.append(v)
        return False

    def _augment_bfs(self, source, sink, fase: str):
        """Cari augmenting path terpendek (jumlah busur) berulang kali sampai tidak ada lagi."""
        while True:
            parent = {}
            if not self._bfs(source, sink, parent):
                break
            path = [sink]
            while path[-1] != source:
                path.append(parent[path[-1]])
            path.reverse()
            delta = min(self.residual(u, v) for u, v in zip(path[:-1], path[1:]))
            bu, bv = self.bottleneck_edge(path)
            for u, v in zip(path[:-1], path[1:]):
                self.push_along(u, v, delta)
            sebelum = self.max_flow
            self.max_flow += delta
            info = {"path": path, "flow_added": delta, "current_max_flow": self.max_flow,
                    "bottleneck_edge": [bu, bv], "fase": fase}
            self.augmenting_paths.append(info)
            self.log_step(
                event_type="AUGMENTING_PATH_FOUND",
                state_mutations=info,
                narrative=(
                    f"Jalur augmentasi ke-{len(self.augmenting_paths)}: {self.path_text(path)}. "
                    f"Sisa kapasitas terkecil ada di {self.edge_text(bu, bv)} sebesar "
                    f"{angka(delta)} skr/jam, jadi total aliran naik dari {angka(sebelum)} jadi "
                    f"{angka(self.max_flow)} skr/jam."
                ),
            )

    # ------------------------------------------------------------------ hasil akhir
    def _finish(self, source, sink):
        """Hitung min cut dari residual graph lalu kembalikan (jalur utama, nilai max flow)."""
        seen = {source}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in self.residual_neighbors(u):
                if v not in seen and self.residual(u, v) > EPS:
                    seen.add(v)
                    queue.append(v)
        self.source_side = sorted(seen)
        self.min_cut_edges = sorted((u, v) for u, v in self.graph.edges() if u in seen and v not in seen)
        cut_value = sum(self.capacity(u, v) for u, v in self.min_cut_edges)
        self.log_step(
            event_type="MIN_CUT_FOUND",
            state_mutations={
                "max_flow": self.max_flow,
                "min_cut_edges": [list(e) for e in self.min_cut_edges],
                "min_cut_capacity": cut_value,
                "source_side": self.source_side,
                "edge_flows": [[u, v, round(self.flow.get((u, v), 0.0), 6)] for u, v in self.graph.edges()],
            },
            narrative=(
                f"{self.KALIMAT_SELESAI} Max flow = {angka(self.max_flow)} skr/jam. Min cut berisi "
                + ", ".join(self.edge_text(u, v) for u, v in self.min_cut_edges if self.capacity(u, v) > EPS)
                + f" dengan total kapasitas {angka(cut_value)} skr/jam, sama dengan max flow."
            ),
        )
        return self.main_path(source, sink), self.max_flow

    def flow_decomposition(self, source, sink) -> List[Tuple[List[int], float]]:
        """Pecah aliran akhir menjadi beberapa jalur s -> t beserta besar alirannya."""
        sisa = {e: f for e, f in self.flow.items() if f > EPS}
        hasil = []
        while True:
            parent = {source: None}
            queue = deque([source])
            while queue and sink not in parent:
                u = queue.popleft()
                for v in self.graph.successors(u):
                    if v not in parent and sisa.get((u, v), 0.0) > EPS:
                        parent[v] = u
                        queue.append(v)
            if sink not in parent:
                break
            path = [sink]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            path.reverse()
            jumlah = min(sisa[(u, v)] for u, v in zip(path[:-1], path[1:]))
            for u, v in zip(path[:-1], path[1:]):
                sisa[(u, v)] -= jumlah
            hasil.append((path, jumlah))
        return sorted(hasil, key=lambda t: -t[1])

    def main_path(self, source, sink) -> List[int]:
        jalur = self.flow_decomposition(source, sink)
        return jalur[0][0] if jalur else []

    # ------------------------------------------------------------------ kontrak BaseGraphAlgorithm
    def run(self, source_node: int, sink_node: int):
        self.source, self.sink = source_node, sink_node
        self.flow = {(u, v): 0.0 for u, v in self.graph.edges()}
        self.max_flow = 0.0
        self.augmenting_paths = []
        self.log_step(
            event_type="INITIALIZATION",
            state_mutations={"source": source_node, "sink": sink_node, "max_flow": 0.0,
                             "total_edges": self.graph.number_of_edges()},
            narrative=(
                f"Semua aliran diset 0. Sumber = {self.label(source_node)} (node {source_node}), "
                f"tujuan = {self.label(sink_node)} (node {sink_node})."
            ),
        )
        self._augment_bfs(source_node, sink_node, fase="awal")
        return self._finish(source_node, sink_node)

    def apply_capacity_event(self, event_data: dict) -> Tuple[Tuple[int, int], float, float]:
        u, v = event_data["edge"]
        new_capacity = event_data.get("new_capacity")
        if new_capacity is None:
            new_capacity = event_data.get("new_weight")
        old_capacity = self.model.update_edge_capacity(u, v, new_capacity)
        alasan = event_data.get("description", "")
        self.log_step(
            event_type="UPDATE_CAPACITY_EVENT",
            state_mutations={"target_edge": [u, v], "old_capacity": old_capacity, "new_capacity": new_capacity},
            narrative=(
                f"Kapasitas {self.edge_text(u, v)} berubah dari {angka(old_capacity)} jadi "
                f"{angka(new_capacity)} skr/jam. {alasan}".strip()
            ),
        )
        return (u, v), old_capacity, float(new_capacity)

    def handle_dynamic_event(self, event_data: dict):
        """Baseline: ubah kapasitas lalu hitung ulang max flow dari nol."""
        self.apply_capacity_event(event_data)
        return self.run(event_data["start"], event_data["goal"])


AlgorithmRegistry.register("ford_fulkerson", FordFulkerson)
AlgorithmRegistry.register_alias("edmonds_karp", "ford_fulkerson")
