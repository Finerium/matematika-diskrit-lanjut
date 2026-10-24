from algorithms.maxflow.ford_fulkerson import EPS, FordFulkerson
from algorithms.registry import AlgorithmRegistry


class FordFulkersonDFS(FordFulkerson):
    """Ford-Fulkerson versi asli (1956): augmenting path dicari dengan DFS, jadi jalurnya belum tentu terpendek.

    Pembanding sederhana kedua di samping Edmonds-Karp. Semua bagian lain (aliran, min cut, narasi, event)
    sama dengan kelas induknya, yang diganti hanya cara mencari jalur.
    """

    def _cari_jalur(self, source, sink, parent) -> bool:
        visited = {source}
        stack = [source]
        while stack:
            u = stack.pop()
            for v in self.residual_neighbors(u):
                if v not in visited and self.residual(u, v) > EPS:
                    visited.add(v)
                    parent[v] = u
                    if v == sink:
                        return True
                    stack.append(v)
        return False


AlgorithmRegistry.register("ford_fulkerson_dfs", FordFulkersonDFS)
AlgorithmRegistry.register_alias("ff_dfs", "ford_fulkerson_dfs")
