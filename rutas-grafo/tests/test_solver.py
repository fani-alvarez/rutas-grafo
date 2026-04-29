"""
test_solver.py
--------------
Pruebas reproducibles para la solución de rutas con arista obligatoria.
Cubre casos: válido, sin solución y casos borde.

Ejecutar con:
    python -m pytest tests/test_solver.py -v
"""

import json
import sys
from pathlib import Path

# Asegurar que el root del proyecto esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.generate_dataset import generate, MAIN_GRAPH, TEST_CASES
from src.graph import DirectedWeightedGraph
from src.loader import load_graph_from_json
from src.solver import find_min_cost_route_with_mandatory_edge


# ---------------------------------------------------------------------------
# Fixture: grafo cargado desde el dataset sintético
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def generated_data(tmp_path_factory):
    """Genera el dataset en un directorio temporal para la sesión de tests."""
    data_dir = tmp_path_factory.mktemp("data")
    generate(str(data_dir))
    return data_dir


@pytest.fixture(scope="session")
def graph(generated_data):
    return load_graph_from_json(generated_data / "graph.json")


# ---------------------------------------------------------------------------
# TC01 — Caso válido
# ---------------------------------------------------------------------------

class TestTC01_ValidRoute:
    """Envío CDMX → TIJ con arista obligatoria QRO→HUB."""

    def test_solution_found(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.found, f"Se esperaba solución. Razón: {result.reason}"

    def test_mandatory_edge_in_path(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.mandatory_edge_present(), (
            f"La arista QRO→HUB no aparece en la ruta: {result.path}"
        )

    def test_path_starts_at_origin(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.path[0] == "CDMX"

    def test_path_ends_at_destination(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.path[-1] == "TIJ"

    def test_cost_is_finite_and_positive(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.total_cost < float("inf")
        assert result.total_cost > 0

    def test_optimal_cost(self, graph):
        """Costo esperado: CDMX→QRO(3) + QRO→HUB(1) + HUB→TIJ(7) = 11."""
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.total_cost == pytest.approx(11.0), (
            f"Costo esperado 11, obtenido {result.total_cost}"
        )

    def test_consecutive_edges_in_path_exist_in_graph(self, graph):
        """Cada par consecutivo de nodos en la ruta debe ser una arista válida."""
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="TIJ",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        for i in range(len(result.path) - 1):
            u, v = result.path[i], result.path[i + 1]
            assert graph.has_edge(u, v), f"Arista {u}→{v} en la ruta no existe en el grafo"


# ---------------------------------------------------------------------------
# TC02 — Sin solución: HUB no conecta con CAN
# ---------------------------------------------------------------------------

class TestTC02_NoSolution:
    """Ruta CDMX→CAN con arista obligatoria QRO→HUB: HUB no llega a CAN."""

    def test_no_solution(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert not result.found

    def test_reason_is_non_empty(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.reason, "Se esperaba una razón clara de por qué no hay solución"

    def test_cost_is_infinity(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.total_cost == float("inf")

    def test_path_is_empty(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="QRO", mandatory_v="HUB"
        )
        assert result.path == []


# ---------------------------------------------------------------------------
# TC03 — Caso borde: arista obligatoria con peso 0
# ---------------------------------------------------------------------------

class TestTC03_ZeroWeightMandatoryEdge:
    """Arista obligatoria HUB→QRO tiene peso 0 (shuttle gratuito)."""

    def test_solution_found(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="MTY",
            mandatory_u="HUB", mandatory_v="QRO"
        )
        assert result.found

    def test_mandatory_edge_present(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="MTY",
            mandatory_u="HUB", mandatory_v="QRO"
        )
        assert result.mandatory_edge_present()

    def test_cost_is_correct(self, graph):
        """
        Ruta óptima: CDMX→QRO(3)→HUB(1)→QRO(0)→HUB(1)→MTY(2) = 7
        Dijkstra elige QRO→HUB→MTY(=3) sobre la alternativa directa QRO→MTY(=5).
        """
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="MTY",
            mandatory_u="HUB", mandatory_v="QRO"
        )
        assert result.total_cost == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# TC04 — Caso borde: nodo aislado como destino, arista obligatoria directa
# ---------------------------------------------------------------------------

class TestTC04_IsolatedNodeAsDestination:
    """ISO no tiene aristas salientes; la arista CDMX→ISO es la obligatoria y el destino es ISO."""

    def test_solution_found(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="ISO",
            mandatory_u="CDMX", mandatory_v="ISO"
        )
        assert result.found

    def test_mandatory_edge_present(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="ISO",
            mandatory_u="CDMX", mandatory_v="ISO"
        )
        assert result.mandatory_edge_present()

    def test_cost_equals_edge_weight(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="ISO",
            mandatory_u="CDMX", mandatory_v="ISO"
        )
        assert result.total_cost == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TC05 — Sin solución: arista obligatoria no existe en el grafo
# ---------------------------------------------------------------------------

class TestTC05_MandatoryEdgeNotInGraph:
    """La arista GDL→CAN no existe; se debe reportar error claro."""

    def test_no_solution(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="GDL", mandatory_v="CAN"
        )
        assert not result.found

    def test_reason_mentions_edge(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="CAN",
            mandatory_u="GDL", mandatory_v="CAN"
        )
        assert "GDL" in result.reason or "CAN" in result.reason or "arista" in result.reason.lower()


# ---------------------------------------------------------------------------
# TC06 — Caso borde: origen == u
# ---------------------------------------------------------------------------

class TestTC06_OriginEqualsU:
    """El origen ya es u → no hay tramo previo a la arista obligatoria."""

    def test_solution_found(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="OAX",
            mandatory_u="CDMX", mandatory_v="PUE"
        )
        assert result.found

    def test_mandatory_edge_present(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="OAX",
            mandatory_u="CDMX", mandatory_v="PUE"
        )
        assert result.mandatory_edge_present()

    def test_path_starts_at_origin(self, graph):
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="OAX",
            mandatory_u="CDMX", mandatory_v="PUE"
        )
        assert result.path[0] == "CDMX"

    def test_cost_correct(self, graph):
        """Costo: 2(CDMX→PUE) + 3(PUE→OAX) = 5."""
        result = find_min_cost_route_with_mandatory_edge(
            graph, origin="CDMX", destination="OAX",
            mandatory_u="CDMX", mandatory_v="PUE"
        )
        assert result.total_cost == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Validaciones de estructura del grafo
# ---------------------------------------------------------------------------

class TestGraphStructure:
    def test_all_nodes_registered(self, graph):
        node_ids = {n["id"] for n in MAIN_GRAPH["nodes"]}
        for nid in node_ids:
            assert nid in graph.adjacency, f"Nodo {nid} no encontrado en el grafo cargado"

    def test_edge_count(self, graph):
        total_edges = sum(len(v) for v in graph.adjacency.values())
        assert total_edges == len(MAIN_GRAPH["edges"])

    def test_no_negative_weights(self, graph):
        for edge in graph.edges():
            assert edge.weight >= 0, f"Peso negativo en arista {edge}"

    def test_node_iso_has_no_outgoing_edges(self, graph):
        assert graph.neighbors("ISO") == [], "ISO debe ser nodo sin aristas salientes"
