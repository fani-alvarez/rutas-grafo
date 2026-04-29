"""
graph.py
--------
Estructura de datos para un grafo dirigido ponderado y operaciones básicas.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Edge:
    """Arista dirigida con peso."""
    source: str
    target: str
    weight: float
    label: Optional[str] = None  # etiqueta opcional (ej. nombre de ruta)

    def __repr__(self) -> str:
        return f"Edge({self.source!r} -> {self.target!r}, w={self.weight})"


@dataclass
class DirectedWeightedGraph:
    """
    Grafo dirigido ponderado representado como lista de adyacencia.

    Estructura interna:
        adjacency: dict[nodo, list[(vecino, peso, label)]]
    """
    adjacency: dict[str, list[tuple[str, float, Optional[str]]]] = field(
        default_factory=dict
    )
    _edge_set: set[tuple[str, str]] = field(default_factory=set, repr=False)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def add_node(self, node: str) -> None:
        """Registra un nodo aunque no tenga aristas salientes."""
        if node not in self.adjacency:
            self.adjacency[node] = []

    def add_edge(self, source: str, target: str, weight: float,
                 label: Optional[str] = None) -> None:
        """
        Agrega una arista dirigida source→target con el peso dado.
        Permite múltiples aristas entre el mismo par de nodos (multigrafo).
        """
        if weight < 0:
            raise ValueError(
                f"Peso negativo no soportado: {source}→{target} w={weight}. "
                "El algoritmo usa Dijkstra."
            )
        self.add_node(source)
        self.add_node(target)
        self.adjacency[source].append((target, weight, label))
        self._edge_set.add((source, target))

    def has_edge(self, u: str, v: str) -> bool:
        return (u, v) in self._edge_set

    def nodes(self) -> list[str]:
        return list(self.adjacency.keys())

    def edges(self) -> list[Edge]:
        result = []
        for src, neighbors in self.adjacency.items():
            for (tgt, w, lbl) in neighbors:
                result.append(Edge(src, tgt, w, lbl))
        return result

    def neighbors(self, node: str) -> list[tuple[str, float, Optional[str]]]:
        return self.adjacency.get(node, [])

    def __repr__(self) -> str:
        n = len(self.adjacency)
        e = sum(len(v) for v in self.adjacency.values())
        return f"DirectedWeightedGraph(nodes={n}, edges={e})"
