"""
solver.py
---------
Implementa la búsqueda de la ruta de costo mínimo entre un origen (o) y un
destino (d) que pase obligatoriamente por la arista (u → v).

Enfoque:
    Descomponer el problema en dos sub-problemas de Dijkstra independientes:
        1. Ruta mínima de  o → u
        2. Ruta mínima de  v → d

    La ruta final es:  o →...→ u → v →...→ d
    con costo total = cost(o→u) + weight(u,v) + cost(v→d)

    De esta forma garantizamos que la arista (u,v) aparece exactamente en la
    ruta y el resto de los tramos son óptimos por el principio de optimalidad.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional

from src.graph import DirectedWeightedGraph


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    """Encapsula el resultado de una búsqueda de ruta con arista obligatoria."""
    found: bool
    origin: str
    destination: str
    mandatory_edge: tuple[str, str]
    path: list[str] = field(default_factory=list)
    total_cost: float = float("inf")
    reason: str = ""

    def mandatory_edge_present(self) -> bool:
        """Verifica que la arista obligatoria aparezca en la ruta devuelta."""
        u, v = self.mandatory_edge
        for i in range(len(self.path) - 1):
            if self.path[i] == u and self.path[i + 1] == v:
                return True
        return False

    def summary(self) -> str:
        if not self.found:
            return (
                f"❌  Sin solución: {self.reason}\n"
                f"   Origen={self.origin}  Destino={self.destination}  "
                f"Arista obligatoria={self.mandatory_edge}"
            )
        arrow = " → ".join(self.path)
        edge_ok = "✅" if self.mandatory_edge_present() else "⚠️  ARISTA FALTANTE"
        return (
            f"✅  Ruta encontrada\n"
            f"   Camino   : {arrow}\n"
            f"   Costo    : {self.total_cost}\n"
            f"   Arista {self.mandatory_edge[0]}→{self.mandatory_edge[1]} presente: {edge_ok}"
        )


# ---------------------------------------------------------------------------
# Dijkstra interno
# ---------------------------------------------------------------------------

def _dijkstra(
    graph: DirectedWeightedGraph,
    start: str,
) -> tuple[dict[str, float], dict[str, Optional[str]]]:
    """
    Dijkstra estándar desde `start`.
    Retorna:
        dist : distancia mínima desde start a cada nodo alcanzable.
        prev : nodo anterior en el camino óptimo (para reconstrucción).
    """
    dist: dict[str, float] = {node: float("inf") for node in graph.nodes()}
    prev: dict[str, Optional[str]] = {node: None for node in graph.nodes()}

    if start not in dist:
        return dist, prev

    dist[start] = 0.0
    # heap: (costo_acumulado, nodo)
    heap: list[tuple[float, str]] = [(0.0, start)]

    while heap:
        current_cost, current_node = heapq.heappop(heap)

        # Si ya encontramos un camino mejor, ignorar
        if current_cost > dist[current_node]:
            continue

        for (neighbor, weight, _label) in graph.neighbors(current_node):
            new_cost = current_cost + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = current_node
                heapq.heappush(heap, (new_cost, neighbor))

    return dist, prev


def _reconstruct_path(
    prev: dict[str, Optional[str]], start: str, end: str
) -> list[str]:
    """Reconstruye el camino desde start hasta end usando el dict prev."""
    path: list[str] = []
    current: Optional[str] = end
    while current is not None:
        path.append(current)
        current = prev.get(current)
        if current == start:
            path.append(start)
            break
    path.reverse()
    # Verificar que realmente empieza en start
    if not path or path[0] != start:
        return []
    return path


# ---------------------------------------------------------------------------
# Solver principal
# ---------------------------------------------------------------------------

def find_min_cost_route_with_mandatory_edge(
    graph: DirectedWeightedGraph,
    origin: str,
    destination: str,
    mandatory_u: str,
    mandatory_v: str,
) -> RouteResult:
    """
    Encuentra la ruta de costo mínimo de `origin` a `destination`
    que pase obligatoriamente por la arista (mandatory_u → mandatory_v).

    Parámetros
    ----------
    graph        : Grafo dirigido ponderado.
    origin       : Nodo de inicio.
    destination  : Nodo de llegada.
    mandatory_u  : Nodo fuente de la arista obligatoria.
    mandatory_v  : Nodo destino de la arista obligatoria.

    Retorna
    -------
    RouteResult  : Objeto con ruta, costo y metadatos de validación.
    """
    edge = (mandatory_u, mandatory_v)

    # --- Validaciones previas -------------------------------------------
    for node, label in [(origin, "origen"), (destination, "destino"),
                        (mandatory_u, "u"), (mandatory_v, "v")]:
        if node not in graph.adjacency:
            return RouteResult(
                found=False, origin=origin, destination=destination,
                mandatory_edge=edge,
                reason=f"El nodo '{node}' ({label}) no existe en el grafo."
            )

    if not graph.has_edge(mandatory_u, mandatory_v):
        return RouteResult(
            found=False, origin=origin, destination=destination,
            mandatory_edge=edge,
            reason=f"La arista obligatoria {mandatory_u}→{mandatory_v} no existe en el grafo."
        )

    # Obtener el peso de la arista obligatoria (tomamos el mínimo si hay varias)
    mandatory_weight = min(
        w for (tgt, w, _) in graph.neighbors(mandatory_u) if tgt == mandatory_v
    )

    # --- Sub-problema 1: o → u -------------------------------------------
    dist_from_origin, prev_from_origin = _dijkstra(graph, origin)
    cost_o_to_u = dist_from_origin[mandatory_u]

    if cost_o_to_u == float("inf"):
        return RouteResult(
            found=False, origin=origin, destination=destination,
            mandatory_edge=edge,
            reason=f"No existe camino de '{origin}' a '{mandatory_u}'."
        )

    # --- Sub-problema 2: v → d -------------------------------------------
    dist_from_v, prev_from_v = _dijkstra(graph, mandatory_v)
    cost_v_to_d = dist_from_v[destination]

    if cost_v_to_d == float("inf"):
        # Caso especial: v == d (la arista llega directamente al destino)
        if mandatory_v == destination:
            cost_v_to_d = 0.0
        else:
            return RouteResult(
                found=False, origin=origin, destination=destination,
                mandatory_edge=edge,
                reason=f"No existe camino de '{mandatory_v}' a '{destination}'."
            )

    # --- Reconstruir caminos --------------------------------------------
    path_o_to_u = _reconstruct_path(prev_from_origin, origin, mandatory_u)
    path_v_to_d = (
        [mandatory_v]
        if mandatory_v == destination
        else _reconstruct_path(prev_from_v, mandatory_v, destination)
    )

    if not path_o_to_u or not path_v_to_d:
        return RouteResult(
            found=False, origin=origin, destination=destination,
            mandatory_edge=edge,
            reason="Fallo en la reconstrucción del camino (grafo inconsistente)."
        )

    # Caso especial: origin == mandatory_u
    if origin == mandatory_u:
        path_o_to_u = [origin]

    full_path = path_o_to_u + path_v_to_d  # u ya está en path_o_to_u[-1]; v abre path_v_to_d
    total_cost = cost_o_to_u + mandatory_weight + cost_v_to_d

    return RouteResult(
        found=True,
        origin=origin,
        destination=destination,
        mandatory_edge=edge,
        path=full_path,
        total_cost=round(total_cost, 4),
    )
