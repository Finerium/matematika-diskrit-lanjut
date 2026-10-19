from collections import deque

from algorithms.maxflow.ford_fulkerson import EPS, FordFulkerson, angka
from algorithms.registry import AlgorithmRegistry


class DynamicDinic(FordFulkerson):
    """SOTA: Dinic (1970) dengan perbaikan aliran inkremental saat kapasitas berubah.

    run() memakai level graph (BFS) + blocking flow (DFS), jadi jumlah fase paling banyak O(V).
    handle_dynamic_event() tidak menghitung dari nol seperti baseline. Aliran lama dipertahankan:
    - kapasitas naik  -> cukup cari augmenting path tambahan dari aliran yang sudah ada;
    - kapasitas turun di bawah aliran edge itu -> kelebihan aliran dikembalikan dulu
      (aliran dikurangi di jalur s -> u dan v -> t), baru setelah itu diaugmentasi ulang.
    """

    def __init__(self, model):
        super().__init__(model)
        self.phase_count = 0

    # ------------------------------------------------------------------ Dinic
    def _level_graph(self, source, sink):
        level = {source: 0}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in self.residual_neighbors(u):
                if v not in level and self.residual(u, v) > EPS:
                    level[v] = level[u] + 1
                    queue.append(v)
        return level if sink in level else None

    def _blocking_flow(self, source, sink, level, fase):
        # DFS iteratif dengan pointer per simpul (dead end tidak dikunjungi ulang)
        adj = {u: [v for v in self.residual_neighbors(u)] for u in level}
        ptr = {u: 0 for u in level}
        total = 0.0
        while True:
            path, u = [source], source
            while u != sink:
                maju = False
                while ptr[u] < len(adj[u]):
                    v = adj[u][ptr[u]]
                    if level.get(v) == level[u] + 1 and self.residual(u, v) > EPS:
                        path.append(v)
                        u = v
                        maju = True
                        break
                    ptr[u] += 1
                if not maju:
                    if u == source:
                        return total
                    path.pop()
                    prev = path[-1]
                    ptr[prev] += 1
                    u = prev
            delta = min(self.residual(a, b) for a, b in zip(path[:-1], path[1:]))
            bu, bv = self.bottleneck_edge(path)
            for a, b in zip(path[:-1], path[1:]):
                self.push_along(a, b, delta)
            sebelum = self.max_flow
            self.max_flow += delta
            total += delta
            info = {"path": path, "flow_added": delta, "current_max_flow": self.max_flow,
                    "bottleneck_edge": [bu, bv], "fase": fase, "dinic_phase": self.phase_count}
            self.augmenting_paths.append(info)
            self.log_step(
                event_type="AUGMENTING_PATH_FOUND",
                state_mutations=info,
                narrative=(
                    f"Fase Dinic ke-{self.phase_count}, jalur {self.path_text(path)}. Busur kritis "
                    f"{self.edge_text(bu, bv)} menahan aliran tambahan {angka(delta)} skr/jam, "
                    f"total aliran naik dari {angka(sebelum)} jadi {angka(self.max_flow)} skr/jam."
                ),
            )

    def _augment_dinic(self, source, sink, fase):
        while True:
            level = self._level_graph(source, sink)
            if level is None:
                break
            self.phase_count += 1
            self.log_step(
                event_type="LEVEL_GRAPH_BUILT",
                state_mutations={"phase": self.phase_count, "level": {str(k): v for k, v in level.items()}},
                narrative=(
                    f"Fase Dinic ke-{self.phase_count}: level graph dibangun dengan BFS, tujuan ada di level "
                    f"{level[sink]}."
                ),
            )
            self._blocking_flow(source, sink, level, fase)

    def run(self, source_node: int, sink_node: int):
        self.source, self.sink = source_node, sink_node
        self.flow = {(u, v): 0.0 for u, v in self.graph.edges()}
        self.max_flow = 0.0
        self.augmenting_paths = []
        self.phase_count = 0
        self.log_step(
            event_type="INITIALIZATION",
            state_mutations={"source": source_node, "sink": sink_node, "max_flow": 0.0,
                             "total_edges": self.graph.number_of_edges()},
            narrative=(
                f"Semua aliran diset 0. Sumber = {self.label(source_node)} (node {source_node}), "
                f"tujuan = {self.label(sink_node)} (node {sink_node})."
            ),
        )
        self._augment_dinic(source_node, sink_node, fase="awal")
        return self._finish(source_node, sink_node)

    # ------------------------------------------------------------------ perbaikan inkremental
    def _cari_jalur_aliran(self, dari, ke):
        """BFS di graf berisi edge yang alirannya > 0 (arah sesuai aliran)."""
        parent = {dari: None}
        queue = deque([dari])
        while queue and ke not in parent:
            u = queue.popleft()
            for v in self.graph.successors(u):
                if v not in parent and self.flow.get((u, v), 0.0) > EPS:
                    parent[v] = u
                    queue.append(v)
        if ke not in parent:
            return None
        path = [ke]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        return path[::-1]

    def _kurangi(self, path, jumlah):
        for a, b in zip(path[:-1], path[1:]):
            self.flow[(a, b)] -= jumlah

    def handle_dynamic_event(self, event_data: dict):
        source, sink = event_data["start"], event_data["goal"]
        if self.source != source or self.sink != sink or not self.flow:
            # belum pernah dijalankan, perlakukan seperti baseline
            return super().handle_dynamic_event(event_data)

        (u, v), old_cap, new_cap = self.apply_capacity_event(event_data)
        self.flow.setdefault((u, v), 0.0)
        lebih = self.flow[(u, v)] - new_cap
        if lebih > EPS:
            # aliran di edge melebihi kapasitas baru: kembalikan kelebihannya
            self.flow[(u, v)] = new_cap
            sebelum = self.max_flow
            sisa = lebih
            while sisa > EPS:
                # kalau kelebihan itu bagian dari siklus aliran, cukup batalkan siklusnya (v -> ... -> u)
                siklus = self._cari_jalur_aliran(v, u)
                if siklus is not None:
                    jumlah = min([sisa] + [self.flow[(a, b)] for a, b in zip(siklus[:-1], siklus[1:])])
                    self._kurangi(siklus, jumlah)
                    sisa -= jumlah
                    continue
                # selain itu kurangi aliran di jalur s -> u dan v -> t dengan besar yang sama
                p1 = self._cari_jalur_aliran(source, u)
                p2 = self._cari_jalur_aliran(v, sink)
                jumlah = min([sisa] + [self.flow[(a, b)] for a, b in zip(p1[:-1], p1[1:])]
                             + [self.flow[(a, b)] for a, b in zip(p2[:-1], p2[1:])])
                self._kurangi(p1, jumlah)
                self._kurangi(p2, jumlah)
                self.max_flow -= jumlah
                sisa -= jumlah
            self.log_step(
                event_type="FLOW_REPAIRED",
                state_mutations={"target_edge": [u, v], "excess_removed": lebih, "current_max_flow": self.max_flow},
                narrative=(
                    f"Aliran lama di {self.edge_text(u, v)} melebihi kapasitas baru sebesar "
                    f"{angka(lebih)} skr/jam, jadi kelebihannya dikembalikan. Total aliran sementara turun dari "
                    f"{angka(sebelum)} jadi {angka(self.max_flow)} skr/jam, lalu dicari jalur pengganti."
                ),
            )
        else:
            self.log_step(
                event_type="FLOW_KEPT",
                state_mutations={"target_edge": [u, v], "current_max_flow": self.max_flow},
                narrative=(
                    f"Aliran lama di {self.edge_text(u, v)} masih muat di kapasitas baru, "
                    f"jadi aliran {angka(self.max_flow)} skr/jam dipertahankan dan hanya dicari tambahan."
                ),
            )
        self._augment_dinic(source, sink, fase="perbaikan")
        return self._finish(source, sink)


AlgorithmRegistry.register("dynamic_dinic", DynamicDinic)
AlgorithmRegistry.register_alias("dinic", "dynamic_dinic")
