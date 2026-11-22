"""Визуализация графовой модели корпоративных данных."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch

from build_company_graph import get_graph


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    graph = get_graph()
    colors = {
        "company": "skyblue",
        "city": "lightgreen",
        "industry": "orange",
    }
    node_colors = [
        colors.get(data["node_type"], "lightgray")
        for _, data in graph.nodes(data=True)
    ]
    labels = {
        node: data["label"] for node, data in graph.nodes(data=True)
    }
    positions = nx.spring_layout(graph, seed=42)

    output_dir = ROOT / "analytics" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "company_graph.png"

    fig, ax = plt.subplots(figsize=(13, 9))
    nx.draw_networkx(
        graph,
        pos=positions,
        labels=labels,
        node_color=node_colors,
        node_size=1900,
        font_size=8,
        edge_color="gray",
        width=1.5,
        ax=ax,
    )
    ax.set_title("Граф корпоративной системы")
    ax.axis("off")
    ax.legend(
        handles=[
            Patch(facecolor=color, label=kind)
            for kind, color in colors.items()
        ],
        loc="upper right",
    )
    fig.tight_layout()
    fig.savefig(output_file, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("Граф сохранен:", output_file.relative_to(ROOT))


if __name__ == "__main__":
    main()
