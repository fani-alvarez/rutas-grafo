"""
loader.py
---------
Carga un grafo desde el formato JSON producido por generate_dataset.py.
"""

import json
from pathlib import Path
from src.graph import DirectedWeightedGraph


def load_graph_from_json(path: str | Path) -> DirectedWeightedGraph:
    """Lee un archivo graph.json y retorna un DirectedWeightedGraph."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    graph = DirectedWeightedGraph()

    # Registrar todos los nodos (incluso los aislados)
    for node in data.get("nodes", []):
        graph.add_node(node["id"])

    # Agregar aristas
    for edge in data.get("edges", []):
        graph.add_edge(
            source=edge["source"],
            target=edge["target"],
            weight=edge["weight"],
            label=edge.get("label"),
        )

    return graph
