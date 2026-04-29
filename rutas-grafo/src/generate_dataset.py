"""
generate_dataset.py
-------------------
Genera el dataset sintético para validar la solución de rutas con arista
obligatoria en un grafo dirigido ponderado.

Caso de negocio: Red logística de distribución de paquetes
-----------------------------------------------------------
Una empresa de mensajería opera centros de distribución (nodos) conectados por
rutas de transporte (aristas dirigidas). Cada arista tiene un costo en minutos
de tiempo de tránsito. Se necesita planificar envíos que DEBEN pasar por un
punto de control o enlace obligatorio (ej. aduana, hub de alta capacidad).

El dataset incluye:
    • Un caso con solución válida.
    • Un caso sin solución (nodo destino no alcanzable desde la arista obligatoria).
    • Tres casos borde: peso cero, ciclo, empate de rutas, nodo aislado.
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Definición del grafo principal de la red logística
# ---------------------------------------------------------------------------

MAIN_GRAPH = {
    "description": (
        "Red logística de distribución con 10 centros (nodos) y rutas "
        "dirigidas con costos en minutos de tránsito."
    ),
    "nodes": [
        {"id": "CDMX", "name": "Ciudad de México (Hub Central)"},
        {"id": "GDL",  "name": "Guadalajara"},
        {"id": "MTY",  "name": "Monterrey"},
        {"id": "PUE",  "name": "Puebla"},
        {"id": "QRO",  "name": "Querétaro"},
        {"id": "VER",  "name": "Veracruz"},
        {"id": "OAX",  "name": "Oaxaca"},
        {"id": "CAN",  "name": "Cancún"},
        {"id": "TIJ",  "name": "Tijuana"},
        {"id": "HUB",  "name": "Hub Aduanal Norte"},
        {"id": "ISO",  "name": "Nodo Aislado (sin conexiones de salida)"},
    ],
    "edges": [
        # Rutas principales
        {"source": "CDMX", "target": "QRO",  "weight": 3,  "label": "Autopista 57"},
        {"source": "CDMX", "target": "PUE",  "weight": 2,  "label": "Autopista 150"},
        {"source": "CDMX", "target": "VER",  "weight": 6,  "label": "Autopista 150D"},
        {"source": "QRO",  "target": "GDL",  "weight": 4,  "label": "Autopista 90"},
        {"source": "QRO",  "target": "MTY",  "weight": 5,  "label": "Autopista 57N"},
        {"source": "QRO",  "target": "HUB",  "weight": 1,  "label": "Enlace HUB"},
        {"source": "GDL",  "target": "TIJ",  "weight": 8,  "label": "Autopista 15"},
        {"source": "GDL",  "target": "MTY",  "weight": 6,  "label": "Autopista 45"},
        {"source": "HUB",  "target": "MTY",  "weight": 2,  "label": "Corredor Norte"},
        {"source": "HUB",  "target": "TIJ",  "weight": 7,  "label": "Corredor Noroeste"},
        {"source": "MTY",  "target": "TIJ",  "weight": 10, "label": "Autopista 40"},
        {"source": "PUE",  "target": "OAX",  "weight": 3,  "label": "Autopista 135"},
        {"source": "PUE",  "target": "VER",  "weight": 4,  "label": "Autopista 140"},
        {"source": "VER",  "target": "OAX",  "weight": 5,  "label": "Autopista 185"},
        {"source": "VER",  "target": "CAN",  "weight": 9,  "label": "Autopista 180"},
        {"source": "OAX",  "target": "CAN",  "weight": 7,  "label": "Autopista 190"},
        # Ruta con peso 0 (shuttle gratuito dentro del hub, caso borde)
        {"source": "HUB",  "target": "QRO",  "weight": 0,  "label": "Shuttle interno"},
        # Arista que crea ciclo: QRO→HUB→QRO
        # (ya existe QRO→HUB arriba; agregamos HUB→QRO con peso 0)
        # Nodo aislado: ISO tiene aristas de entrada pero ninguna de salida
        {"source": "CDMX", "target": "ISO",  "weight": 1,  "label": "Ruta sin salida"},
        # Ruta alternativa que crea empate: CDMX→QRO→HUB→MTY vs CDMX→QRO→MTY
        # CDMX→QRO(3) + QRO→HUB(1) + HUB→MTY(2) = 6
        # CDMX→QRO(3) + QRO→MTY(5)               = 8  → HUB gana (no empate real)
        # Agregamos ruta directa para crear empate CDMX→MTY total=8 vs la anterior=6
        {"source": "CDMX", "target": "MTY",  "weight": 6,  "label": "Vuelo directo CDMX-MTY"},
    ]
}

# ---------------------------------------------------------------------------
# Casos de prueba
# ---------------------------------------------------------------------------

TEST_CASES = [
    # -----------------------------------------------------------------------
    # CASO 1 — Solución válida
    # -----------------------------------------------------------------------
    {
        "id": "TC01",
        "description": (
            "Caso válido. Envío de CDMX a TIJ que DEBE pasar por el hub aduanal "
            "(arista QRO→HUB). La ruta óptima es CDMX→QRO→HUB→MTY→TIJ "
            "o CDMX→QRO→HUB→TIJ. Se espera solución con la arista obligatoria."
        ),
        "origin": "CDMX",
        "destination": "TIJ",
        "mandatory_edge": {"u": "QRO", "v": "HUB"},
        "expected": {
            "found": True,
            "mandatory_edge_in_path": True,
            "notes": "Costo óptimo = 3(CDMX→QRO) + 1(QRO→HUB) + 7(HUB→TIJ) = 11"
        }
    },

    # -----------------------------------------------------------------------
    # CASO 2 — Sin solución: destino no alcanzable desde v
    # -----------------------------------------------------------------------
    {
        "id": "TC02",
        "description": (
            "Sin solución. Se pide ir de CDMX a CAN pasando por la arista "
            "QRO→HUB. Desde HUB no existe ningún camino hacia CAN "
            "(HUB solo conecta a MTY y TIJ). Se espera 'no encontrado'."
        ),
        "origin": "CDMX",
        "destination": "CAN",
        "mandatory_edge": {"u": "QRO", "v": "HUB"},
        "expected": {
            "found": False,
            "notes": "HUB no tiene rutas hacia CAN; el único camino a CAN pasa por VER u OAX."
        }
    },

    # -----------------------------------------------------------------------
    # CASO 3 — Caso borde: arista con peso 0 (shuttle gratuito)
    # -----------------------------------------------------------------------
    {
        "id": "TC03",
        "description": (
            "Caso borde: arista obligatoria con peso 0 (HUB→QRO shuttle interno). "
            "Ruta CDMX→QRO→HUB→QRO→MTY. Válida aunque incluya el ciclo QRO→HUB→QRO."
        ),
        "origin": "CDMX",
        "destination": "MTY",
        "mandatory_edge": {"u": "HUB", "v": "QRO"},
        "expected": {
            "found": True,
            "mandatory_edge_in_path": True,
            "notes": (
                "Peso 0 en la arista obligatoria. "
                "Costo = 3+1+0+1+2 = 7: CDMX→QRO→HUB→QRO→HUB→MTY (Dijkstra elige QRO→HUB→MTY=3 sobre QRO→MTY=5)"
            )
        }
    },

    # -----------------------------------------------------------------------
    # CASO 4 — Caso borde: nodo aislado como destino
    # -----------------------------------------------------------------------
    {
        "id": "TC04",
        "description": (
            "Caso borde: destino ISO es un nodo sin aristas de salida. "
            "La arista obligatoria es CDMX→ISO. El destino ya es ISO, "
            "por lo que desde ISO→ISO el costo adicional es 0. Solución válida."
        ),
        "origin": "CDMX",
        "destination": "ISO",
        "mandatory_edge": {"u": "CDMX", "v": "ISO"},
        "expected": {
            "found": True,
            "mandatory_edge_in_path": True,
            "notes": "Origen→destino en un solo salto usando la arista obligatoria. Costo = 1."
        }
    },

    # -----------------------------------------------------------------------
    # CASO 5 — Sin solución: arista obligatoria no existe en el grafo
    # -----------------------------------------------------------------------
    {
        "id": "TC05",
        "description": (
            "Sin solución. La arista obligatoria GDL→CAN no existe en el grafo. "
            "Se espera error claro indicando que la arista no está en el grafo."
        ),
        "origin": "CDMX",
        "destination": "CAN",
        "mandatory_edge": {"u": "GDL", "v": "CAN"},
        "expected": {
            "found": False,
            "notes": "La arista (GDL, CAN) no existe en el dataset."
        }
    },

    # -----------------------------------------------------------------------
    # CASO 6 — Caso borde: origen == u de la arista obligatoria
    # -----------------------------------------------------------------------
    {
        "id": "TC06",
        "description": (
            "Caso borde: el nodo origen coincide con u (CDMX→PUE). "
            "No se necesita tramo previo a la arista obligatoria."
        ),
        "origin": "CDMX",
        "destination": "OAX",
        "mandatory_edge": {"u": "CDMX", "v": "PUE"},
        "expected": {
            "found": True,
            "mandatory_edge_in_path": True,
            "notes": "Costo = 0(origin=u) + 2(CDMX→PUE) + 3(PUE→OAX) = 5."
        }
    },
]

# ---------------------------------------------------------------------------
# Guardar JSON
# ---------------------------------------------------------------------------

def generate(output_dir: str = "data") -> None:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    graph_file = path / "graph.json"
    tests_file = path / "test_cases.json"

    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(MAIN_GRAPH, f, ensure_ascii=False, indent=2)

    with open(tests_file, "w", encoding="utf-8") as f:
        json.dump(TEST_CASES, f, ensure_ascii=False, indent=2)

    print(f"✅ Dataset generado en '{output_dir}/'")
    print(f"   • {graph_file}  ({len(MAIN_GRAPH['nodes'])} nodos, {len(MAIN_GRAPH['edges'])} aristas)")
    print(f"   • {tests_file}  ({len(TEST_CASES)} casos de prueba)")


if __name__ == "__main__":
    generate()
