from typing import Any, Dict, List, Tuple
import networkx as nx


class SpatialGraphModel:
    """Wrapper untuk NetworkX DiGraph yang menyediakan abstraksi operasi spasial."""

    def __init__(self, nx_graph: nx.DiGraph = None):
        self._graph = nx_graph if nx_graph is not None else nx.DiGraph()

    @property
    def nx_graph(self) -> nx.DiGraph:
        """Mengembalikan objek asli NetworkX DiGraph."""
        return self._graph

    def add_spatial_node(self, node_id: int, label: str = "", pos: Tuple[float, float] = (0.0, 0.0)):
        """Menambahkan node dengan metadata spasial dan label."""
        self._graph.add_node(node_id, label=label, pos=tuple(pos))

    def add_weighted_edge(self, u: int, v: int, weight: float, capacity: float = None, label: str = ""):
        """Menambahkan edge searah dengan bobot (dan kapasitas untuk max flow bila ada)."""
        attrs = {"weight": weight}
        if capacity is not None:
            attrs["capacity"] = float(capacity)
        if label:
            attrs["label"] = label
        self._graph.add_edge(u, v, **attrs)

    def update_edge_capacity(self, u: int, v: int, new_capacity: float) -> float:
        """Mengubah kapasitas edge dan mengembalikan kapasitas lama."""
        if not self._graph.has_edge(u, v):
            raise KeyError(f"Edge ({u}, {v}) tidak ditemukan dalam graf.")
        old_capacity = self._graph[u][v].get("capacity", 0.0)
        self._graph[u][v]["capacity"] = float(new_capacity)
        return old_capacity

    def get_edge_label(self, u: int, v: int) -> str:
        """Nama ruas (label edge) untuk narasi log, kalau ada."""
        label = self._graph[u][v].get("label", "")
        return f"{label} ({u} -> {v})" if label else f"Edge {u} -> {v}"

    def update_edge_weight(self, u: int, v: int, new_weight: float) -> float:
        """Mengubah bobot edge dan mengembalikan bobot lama (old weight)."""
        if not self._graph.has_edge(u, v):
            raise KeyError(f"Edge ({u}, {v}) tidak ditemukan dalam graf.")
        
        old_weight = self._graph[u][v].get("weight", 1.0)
        self._graph[u][v]["weight"] = new_weight
        return old_weight

    def get_node_label(self, node_id: int) -> str:
        """Helper membumi untuk mendapatkan nama tempat dari label node."""
        data = self._graph.nodes.get(node_id, {})
        label = data.get("label", "")
        return f"{node_id} ({label})" if label else f"Node_{node_id}"

    def get_positions(self) -> Dict[int, Tuple[float, float]]:
        """Mengambil seluruh koordinat spasial node dari atribut 'pos'."""
        return nx.get_node_attributes(self._graph, "pos")

    def get_topology_dict(self) -> Dict[str, Any]:
        """Ekstraksi struktur topologi awal untuk keperluan logging/JSON export."""
        return {
            "nodes": [
                {
                    "id": n,
                    "label": d.get("label", ""),
                    "pos": list(d.get("pos", [0, 0])),
                }
                for n, d in self._graph.nodes(data=True)
            ],
            "edges": [
                {"from": u, "to": v, "weight": d.get("weight", 1.0),
                 **({"capacity": d["capacity"]} if "capacity" in d else {}),
                 **({"label": d["label"]} if d.get("label") else {})}
                for u, v, d in self._graph.edges(data=True)
            ],
        }