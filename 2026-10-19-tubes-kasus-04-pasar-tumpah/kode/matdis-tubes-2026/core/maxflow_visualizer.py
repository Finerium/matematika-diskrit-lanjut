import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

NAVY, ORANYE, MERAH, ABU = "#1F4295", "#DB623C", "#C0392B", "#9AA5B8"


class MaxFlowSnapshotVisualizer:
    """Simpan gambar kondisi aliran (f/c tiap edge) dan min cut ke file PNG, tanpa jendela GUI."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.pos = nx.get_node_attributes(graph, "pos") or nx.spring_layout(graph, seed=1)

    def save(self, path, title, flow, min_cut_edges, max_flow, highlighted_edge=None):
        fig, ax = plt.subplots(figsize=(13, 8.2), dpi=150)
        fig.patch.set_facecolor("#F4F8FE")
        ax.set_facecolor("#F4F8FE")
        cut = set(map(tuple, min_cut_edges))
        lebar = []
        warna = []
        for u, v in self.graph.edges():
            c = self.graph[u][v].get("capacity", 0.0)
            f = flow.get((u, v), 0.0)
            lebar.append(1.2 + 5.0 * (f / c if c > 0 else 0))
            if (u, v) in cut and c > 0:
                warna.append(MERAH)
            elif c == 0:
                warna.append(ABU)
            elif f > 1e-9:
                warna.append(NAVY)
            else:
                warna.append(ABU)
        nx.draw_networkx_edges(self.graph, self.pos, ax=ax, width=lebar, edge_color=warna, arrows=True,
                               arrowsize=16, connectionstyle="arc3,rad=0.04", node_size=900)
        if highlighted_edge:
            nx.draw_networkx_edges(self.graph, self.pos, ax=ax, edgelist=[tuple(highlighted_edge)], width=2.5,
                                   edge_color=ORANYE, style="dashed", arrows=True, arrowsize=18, node_size=900)
        warna_node = [ORANYE if d.get("label", "").startswith(("S ", "T ")) else NAVY
                      for _, d in self.graph.nodes(data=True)]
        nx.draw_networkx_nodes(self.graph, self.pos, ax=ax, node_size=900, node_color=warna_node,
                               edgecolors="white", linewidths=2)
        nx.draw_networkx_labels(self.graph, self.pos, ax=ax, font_color="white", font_weight="bold", font_size=9,
                                labels={n: d.get("label", str(n)).split(" ")[0] for n, d in self.graph.nodes(data=True)})
        label_edge = {}
        for u, v in self.graph.edges():
            c = self.graph[u][v].get("capacity", 0.0)
            f = flow.get((u, v), 0.0)
            label_edge[(u, v)] = f"{f:,.0f}/{c:,.0f}".replace(",", ".")
        nx.draw_networkx_edge_labels(self.graph, self.pos, ax=ax, edge_labels=label_edge, font_size=7.5,
                                     font_color="#1B2A4A", rotate=False,
                                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        nilai = f"{max_flow:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
        ax.set_title(f"{title}\nMax flow = {nilai} skr/jam", fontsize=12, fontweight="bold", color="#1B2A4A", loc="left")
        legenda = [Line2D([0], [0], color=NAVY, lw=3, label="dialiri (tebal = aliran/kapasitas)"),
                   Line2D([0], [0], color=MERAH, lw=3, label="edge min cut (bottleneck)"),
                   Line2D([0], [0], color=ABU, lw=2, label="tidak dialiri / ditutup")]
        if highlighted_edge:
            legenda.append(Line2D([0], [0], color=ORANYE, lw=2.5, ls="--", label="edge yang berubah di event ini"))
        ax.legend(handles=legenda, loc="lower left", fontsize=8.5, frameon=False)
        ax.text(0.99, 0.01, "label edge = aliran / kapasitas (skr/jam)", transform=ax.transAxes, ha="right",
                fontsize=8, color="#55607A")
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return path
