"""
generate_dataset.py
-------------------
Script para generar un dataset sintético que permite validar un algoritmo
de rutas en grafos dirigidos ponderados, bajo la restricción de incluir
una arista obligatoria en la solución.

Caso de negocio:
----------------
Se modela una red logística de distribución de paquetes donde:
- Los nodos representan centros de distribución.
- Las aristas representan rutas dirigidas con un costo (tiempo en minutos).

Objetivo:
Encontrar rutas óptimas entre un origen y destino que incluyan
forzosamente una arista específica (ej. paso por aduana o hub estratégico).

El dataset incluye:
- Casos con solución válida.
- Casos sin solución.
- Casos borde (edge cases) para robustez del algoritmo.
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Definición del grafo principal
# ---------------------------------------------------------------------------

# Grafo dirigido ponderado que modela la red logística
MAIN_GRAPH = {
    "description": (
        "Red logística de distribución con centros (nodos) y rutas "
        "dirigidas con costos en minutos."
    ),

    # Lista de nodos (centros de distribución)
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
        {"id": "ISO",  "name": "Nodo Aislado (sin salidas)"},
    ],

    # Lista de aristas dirigidas con pesos (costos)
    "edges": [
        # -------------------------
        # Rutas principales
        # -------------------------
        {"source": "CDMX", "target": "QRO", "weight": 3, "label": "Autopista 57"},
        {"source": "CDMX", "target": "PUE", "weight": 2, "label": "Autopista 150"},
        {"source": "CDMX", "target": "VER", "weight": 6, "label": "Autopista 150D"},

        {"source": "QRO", "target": "GDL", "weight": 4, "label": "Autopista 90"},
        {"source": "QRO", "target": "MTY", "weight": 5, "label": "Autopista 57N"},
        {"source": "QRO", "target": "HUB", "weight": 1, "label": "Enlace HUB"},

        {"source": "GDL", "target": "TIJ", "weight": 8, "label": "Autopista 15"},
        {"source": "GDL", "target": "MTY", "weight": 6, "label": "Autopista 45"},

        {"source": "HUB", "target": "MTY", "weight": 2, "label": "Corredor Norte"},
        {"source": "HUB", "target": "TIJ", "weight": 7, "label": "Corredor Noroeste"},

        {"source": "MTY", "target": "TIJ", "weight": 10, "label": "Autopista 40"},

        {"source": "PUE", "target": "OAX", "weight": 3, "label": "Autopista 135"},
        {"source": "PUE", "target": "VER", "weight": 4, "label": "Autopista 140"},

        {"source": "VER", "target": "OAX", "weight": 5, "label": "Autopista 185"},
        {"source": "VER", "target": "CAN", "weight": 9, "label": "Autopista 180"},

        {"source": "OAX", "target": "CAN", "weight": 7, "label": "Autopista 190"},

        # -------------------------
        # Casos borde
        # -------------------------

        # Arista con peso 0 (ej. transporte interno sin costo)
        {"source": "HUB", "target": "QRO", "weight": 0, "label": "Shuttle interno"},

        # Nodo aislado (solo tiene entrada, no salida)
        {"source": "CDMX", "target": "ISO", "weight": 1, "label": "Ruta sin salida"},

        # Ruta directa que compite con rutas indirectas
        {"source": "CDMX", "target": "MTY", "weight": 6, "label": "Vuelo directo"},
    ]
}

# ---------------------------------------------------------------------------
# Definición de casos de prueba
# ---------------------------------------------------------------------------

# Casos diseñados para validar el algoritmo en distintos escenarios
TEST_CASES = [

    # Caso normal: solución válida
    {
        "id": "TC01",
        "description": "Ruta válida que debe pasar por QRO→HUB",
        "origin": "CDMX",
        "destination": "TIJ",
        "mandatory_edge": {"u": "QRO", "v": "HUB"},
        "expected": {
            "found": True,
            "mandatory_edge_in_path": True
        }
    },

    # Caso sin solución: destino no alcanzable
    {
        "id": "TC02",
        "description": "No existe camino desde HUB hacia CAN",
        "origin": "CDMX",
        "destination": "CAN",
        "mandatory_edge": {"u": "QRO", "v": "HUB"},
        "expected": {"found": False}
    },

    # Caso borde: peso cero
    {
        "id": "TC03",
        "description": "Arista obligatoria con peso 0",
        "origin": "CDMX",
        "destination": "MTY",
        "mandatory_edge": {"u": "HUB", "v": "QRO"},
        "expected": {"found": True}
    },

    # Caso borde: nodo aislado
    {
        "id": "TC04",
        "description": "Destino sin salidas",
        "origin": "CDMX",
        "destination": "ISO",
        "mandatory_edge": {"u": "CDMX", "v": "ISO"},
        "expected": {"found": True}
    },

    # Caso inválido: arista no existe
    {
        "id": "TC05",
        "description": "Arista obligatoria inexistente",
        "origin": "CDMX",
        "destination": "CAN",
        "mandatory_edge": {"u": "GDL", "v": "CAN"},
        "expected": {"found": False}
    },

    # Caso borde: origen coincide con inicio de arista obligatoria
    {
        "id": "TC06",
        "description": "Origen = u de la arista obligatoria",
        "origin": "CDMX",
        "destination": "OAX",
        "mandatory_edge": {"u": "CDMX", "v": "PUE"},
        "expected": {"found": True}
    },
]

# ---------------------------------------------------------------------------
# Función para guardar el dataset en archivos JSON
# ---------------------------------------------------------------------------

def generate(output_dir: str = "data") -> None:
    """
    Genera y guarda el dataset en formato JSON.

    Parámetros:
        output_dir (str): carpeta donde se guardarán los archivos.
    """

    path = Path(output_dir)

    # Crea la carpeta si no existe
    path.mkdir(parents=True, exist_ok=True)

    graph_file = path / "graph.json"
    tests_file = path / "test_cases.json"

    # Guardar grafo
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(MAIN_GRAPH, f, ensure_ascii=False, indent=2)

    # Guardar casos de prueba
    with open(tests_file, "w", encoding="utf-8") as f:
        json.dump(TEST_CASES, f, ensure_ascii=False, indent=2)

    # Logs informativos
    print(f"Dataset generado en '{output_dir}/'")
    print(f"{len(MAIN_GRAPH['nodes'])} nodos y {len(MAIN_GRAPH['edges'])} aristas")
    print(f"{len(TEST_CASES)} casos de prueba")

# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate()
