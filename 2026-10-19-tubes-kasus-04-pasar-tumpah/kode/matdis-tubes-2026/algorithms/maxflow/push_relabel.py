from collections import deque

from algorithms.maxflow.ford_fulkerson import EPS, FordFulkerson, angka
from algorithms.registry import AlgorithmRegistry


class PushRelabel(FordFulkerson):
    """SOTA: Push-Relabel FIFO (Goldberg dan Tarjan, 1988) yang bisa melanjutkan aliran lama.

    Push-Relabel tidak mencari jalur utuh seperti Ford-Fulkerson. Algoritma memegang preflow
    (aliran masuk simpul boleh lebih besar dari aliran keluar), lalu kelebihan (excess) di tiap
    simpul didorong (push) ke tetangga yang labelnya tepat satu lebih rendah. Simpul yang tidak bisa
    mendorong labelnya dinaikkan (relabel). Label awal memakai global relabeling, yaitu jarak BFS
    ke sink di residual graph.

    Override handle_dynamic_event(): aliran lama tidak dibuang.
    - Kapasitas turun di bawah aliran edge (u, v): kelebihan dipindah jadi excess di u, kekurangan di v
      ditutup dengan mengurangi aliran di jalur v -> sink.
    - Busur dari source diisi penuh lagi (preflow), label dihitung ulang, lalu excess didorong sampai habis.
    Hasilnya tetap max flow, tetapi kerjanya jauh lebih sedikit daripada menghitung dari nol.
    """

    KALIMAT_SELESAI = "Tidak ada lagi kelebihan (excess) yang bisa didorong ke tujuan."

    def __init__(self, model):
        super().__init__(model)
        self.height = {}
        self.excess = {}
        self.push_count = 0
        self.relabel_count = 0

    # ------------------------------------------------------------------ bagian push-relabel
    def _global_relabel(self, source, sink):
        """Label = jarak BFS ke sink di residual graph. Simpul yang tidak bisa ke sink diberi n + jarak ke source."""
        n = self.graph.number_of_nodes()
        tinggi = {x: 2 * n for x in self.graph.nodes()}
        for awal, dasar in [(sink, 0), (source, n)]:
            if awal == source:
                tinggi[source] = n
            else:
                tinggi[sink] = 0
            queue = deque([awal])
            while queue:
                v = queue.popleft()
                for u in self.residual_neighbors(v):
                    # u -> v harus punya sisa kapasitas supaya u bisa mendorong ke v
                    if tinggi[u] == 2 * n and u not in (source, sink) and self.residual(u, v) > EPS:
                        tinggi[u] = tinggi[v] + 1
                        queue.append(u)
        self.height = tinggi
        self.log_step(
            event_type="GLOBAL_RELABEL",
            state_mutations={"height": {str(k): v for k, v in tinggi.items()}},
            narrative="Label tinggi semua simpul dihitung ulang dari jarak BFS ke tujuan di residual graph.",
        )

    def _saturate_source(self, source, sink, aktif):
        for v in list(self.residual_neighbors(source)):
            r = self.residual(source, v)
            if r > EPS:
                self.push_along(source, v, r)
                self.excess[v] += r
                self.excess[source] -= r
                if v != sink and v not in aktif:
                    aktif.append(v)

    def _discharge_all(self, source, sink, aktif):
        n = self.graph.number_of_nodes()
        while aktif:
            u = aktif.popleft()
            while self.excess[u] > EPS:
                didorong = False
                for v in self.residual_neighbors(u):
                    r = self.residual(u, v)
                    if r > EPS and self.height[u] == self.height[v] + 1:
                        d = min(self.excess[u], r)
                        self.push_along(u, v, d)
                        self.excess[u] -= d
                        self.excess[v] += d
                        self.push_count += 1
                        self.log_step(
                            event_type="PUSH",
                            state_mutations={"from": u, "to": v, "amount": d, "excess_from": self.excess[u],
                                             "height_from": self.height[u]},
                            narrative=(
                                f"Dorong {angka(d)} skr/jam dari node {u} ke node {v} lewat "
                                f"{self.edge_text(u, v)}, "
                                f"sisa kelebihan di node {u} = {angka(self.excess[u])} skr/jam."
                            ),
                        )
                        if v not in (source, sink) and v not in aktif:
                            aktif.append(v)
                        didorong = True
                        if self.excess[u] <= EPS:
                            break
                if not didorong:
                    lama = self.height[u]
                    calon = [self.height[v] for v in self.residual_neighbors(u) if self.residual(u, v) > EPS]
                    self.height[u] = 1 + min(calon) if calon else 2 * n
                    self.relabel_count += 1
                    self.log_step(
                        event_type="RELABEL",
                        state_mutations={"node": u, "old_height": lama, "new_height": self.height[u]},
                        narrative=f"Node {u} tidak bisa mendorong lagi, labelnya naik dari {lama} jadi {self.height[u]}.",
                    )
        # sisa excess yang tidak sampai ke sink sudah kembali ke source, max flow = aliran masuk sink
        self.max_flow = self.excess[sink]

    # ------------------------------------------------------------------ kontrak BaseGraphAlgorithm
    def run(self, source_node: int, sink_node: int):
        self.source, self.sink = source_node, sink_node
        self.flow = {(u, v): 0.0 for u, v in self.graph.edges()}
        self.excess = {x: 0.0 for x in self.graph.nodes()}
        self.max_flow = 0.0
        self.augmenting_paths = []
        self.push_count = self.relabel_count = 0
        self.log_step(
            event_type="INITIALIZATION",
            state_mutations={"source": source_node, "sink": sink_node, "max_flow": 0.0,
                             "total_edges": self.graph.number_of_edges()},
            narrative=(
                f"Semua aliran diset 0. Busur yang keluar dari {self.label(source_node)} langsung diisi penuh "
                f"(preflow), lalu kelebihan di tiap simpul didorong ke arah {self.label(sink_node)}."
            ),
        )
        aktif = deque()
        self._global_relabel(source_node, sink_node)
        self._saturate_source(source_node, sink_node, aktif)
        self._discharge_all(source_node, sink_node, aktif)
        return self._finish(source_node, sink_node)

    def handle_dynamic_event(self, event_data: dict):
        source, sink = event_data["start"], event_data["goal"]
        if self.source != source or self.sink != sink or not self.flow:
            return super().handle_dynamic_event(event_data)
        (u, v), old_cap, new_cap = self.apply_capacity_event(event_data)
        self.flow.setdefault((u, v), 0.0)
        lebih = self.flow[(u, v)] - new_cap
        aktif = deque()
        if lebih > EPS:
            # kurangi aliran (u, v): u kelebihan aliran, v kekurangan aliran
            self.flow[(u, v)] = new_cap
            self.excess[u] += lebih
            self.excess[v] -= lebih
            # kekurangan di v ditutup dengan mengurangi aliran di jalur v -> (u, sink, atau source)
            sisa = lebih
            while sisa > EPS and v not in (source, sink):
                p = self._jalur_aliran(v, {u, sink, source})
                jumlah = min([sisa] + [self.flow[(a, b)] for a, b in zip(p[:-1], p[1:])])
                for a, b in zip(p[:-1], p[1:]):
                    self.flow[(a, b)] -= jumlah
                self.excess[v] += jumlah
                self.excess[p[-1]] -= jumlah
                sisa -= jumlah
            if u not in (source, sink) and self.excess[u] > EPS:
                aktif.append(u)
            self.log_step(
                event_type="FLOW_REPAIRED",
                state_mutations={"target_edge": [u, v], "excess_moved": lebih, "sink_inflow": self.excess[sink]},
                narrative=(
                    f"Aliran lama di {self.edge_text(u, v)} melebihi kapasitas baru sebesar {angka(lebih)} "
                    f"skr/jam. Kelebihan itu jadi excess di node {u} yang akan dicarikan jalan lain."
                ),
            )
        else:
            self.log_step(
                event_type="FLOW_KEPT",
                state_mutations={"target_edge": [u, v], "sink_inflow": self.excess[sink]},
                narrative=(
                    f"Aliran lama di {self.edge_text(u, v)} masih muat, aliran "
                    f"{angka(self.excess[sink])} skr/jam dipertahankan."
                ),
            )
        self._global_relabel(source, sink)
        self._saturate_source(source, sink, aktif)
        self._discharge_all(source, sink, aktif)
        return self._finish(source, sink)

    def _jalur_aliran(self, dari, tujuan):
        """BFS di edge beraliran positif dari simpul dari sampai menyentuh salah satu simpul tujuan."""
        parent = {dari: None}
        queue = deque([dari])
        akhir = None
        while queue and akhir is None:
            a = queue.popleft()
            for b in self.graph.successors(a):
                if b not in parent and self.flow.get((a, b), 0.0) > EPS:
                    parent[b] = a
                    if b in tujuan:
                        akhir = b
                        break
                    queue.append(b)
        path = [akhir]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        return path[::-1]


AlgorithmRegistry.register("push_relabel", PushRelabel)
AlgorithmRegistry.register_alias("maxflow", "push_relabel")
