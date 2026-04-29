"""
graph.py
--------
Estructura de datos para un grafo dirigido ponderado y operaciones básicas.
"""

# Permite usar anotaciones de tipos modernas sin problemas de orden de definición
from __future__ import annotations

# Decorador para crear clases tipo "estructura de datos" automáticamente
from dataclasses import dataclass, field

# Tipos opcionales (pueden ser None)
from typing import Optional


# ---------------------------------------------------------------------------
# Clase Edge (Arista)
# ---------------------------------------------------------------------------
@dataclass
class Edge:
    """Representa una arista dirigida con peso."""
    
    # Nodo de origen
    source: str
    
    # Nodo de destino
    target: str
    
    # Peso de la arista (ej. costo, distancia, tiempo)
    weight: float
    
    # Etiqueta opcional (ej. nombre de la ruta)
    label: Optional[str] = None

    def __repr__(self) -> str:
        """
        Representación legible de la arista.
        Útil para debugging o impresión.
        """
        return f"Edge({self.source!r} -> {self.target!r}, w={self.weight})"


# ---------------------------------------------------------------------------
# Clase DirectedWeightedGraph (Grafo)
# ---------------------------------------------------------------------------
@dataclass
class DirectedWeightedGraph:
    """
    Grafo dirigido ponderado representado como lista de adyacencia.

    Estructura interna:
        adjacency: dict[nodo, list[(vecino, peso, label)]]

    Ejemplo:
        {
            "A": [("B", 5, None), ("C", 3, "ruta1")],
            "B": [("C", 2, None)]
        }
    """

    # Diccionario de adyacencia:
    # cada nodo apunta a una lista de (vecino, peso, etiqueta)
    adjacency: dict[str, list[tuple[str, float, Optional[str]]]] = field(
        default_factory=dict
    )

    # Conjunto auxiliar para verificar existencia de aristas rápidamente
    # (no se imprime en repr para mantenerlo limpio)
    _edge_set: set[tuple[str, str]] = field(default_factory=set, repr=False)

    # ------------------------------------------------------------------
    # Construcción del grafo
    # ------------------------------------------------------------------

    def add_node(self, node: str) -> None:
        """
        Agrega un nodo al grafo.
        Se asegura de que exista aunque no tenga aristas salientes.
        """
        if node not in self.adjacency:
            self.adjacency[node] = []

    def add_edge(self, source: str, target: str, weight: float,
                 label: Optional[str] = None) -> None:
        """
        Agrega una arista dirigida source → target.

        Parámetros:
            source: nodo origen
            target: nodo destino
            weight: peso de la arista (no negativo)
            label: etiqueta opcional

        Nota:
            - Permite múltiples aristas entre los mismos nodos (multigrafo)
            - No permite pesos negativos porque se asume uso de Dijkstra
        """
        if weight < 0:
            raise ValueError(
                f"Peso negativo no soportado: {source}→{target} w={weight}. "
                "El algoritmo usa Dijkstra."
            )

        # Asegura que los nodos existan
        self.add_node(source)
        self.add_node(target)

        # Agrega la arista a la lista de adyacencia
        self.adjacency[source].append((target, weight, label))

        # Registra la arista en el conjunto para consultas rápidas
        self._edge_set.add((source, target))

    def has_edge(self, u: str, v: str) -> bool:
        """
        Verifica si existe una arista de u a v.
        Complejidad O(1) gracias al set.
        """
        return (u, v) in self._edge_set

    def nodes(self) -> list[str]:
        """
        Devuelve la lista de nodos del grafo.
        """
        return list(self.adjacency.keys())

    def edges(self) -> list[Edge]:
        """
        Devuelve todas las aristas del grafo como objetos Edge.
        """
        result = []
        for src, neighbors in self.adjacency.items():
            for (tgt, w, lbl) in neighbors:
                result.append(Edge(src, tgt, w, lbl))
        return result

    def neighbors(self, node: str) -> list[tuple[str, float, Optional[str]]]:
        """
        Devuelve los vecinos de un nodo en formato:
        [(vecino, peso, etiqueta), ...]
        
        Si el nodo no existe, devuelve lista vacía.
        """
        return self.adjacency.get(node, [])

    def __repr__(self) -> str:
        """
        Representación resumida del grafo:
        número de nodos y número de aristas.
        """
        n = len(self.adjacency)
        e = sum(len(v) for v in self.adjacency.values())
        return f"DirectedWeightedGraph(nodes={n}, edges={e})"
