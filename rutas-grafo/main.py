"""
main.py
-------
Punto de entrada principal. Ejecuta todos los casos de prueba del dataset y
muestra un resumen formateado con evidencia de validación de la arista
obligatoria.

Uso:
    python main.py                    # corre todos los casos de prueba
    python main.py --case TC01        # corre solo un caso específico
    python main.py --gen              # regenera el dataset y sale
"""

import argparse
import json
import sys
from pathlib import Path

# Asegurar que el root esté en el path (útil si se corre desde otro directorio)
sys.path.insert(0, str(Path(__file__).parent))

from src.generate_dataset import generate
from src.loader import load_graph_from_json
from src.solver import find_min_cost_route_with_mandatory_edge

DATA_DIR = Path("data")
GRAPH_FILE = DATA_DIR / "graph.json"
TESTS_FILE = DATA_DIR / "test_cases.json"

SEP = "─" * 60


def ensure_data():
    """Genera el dataset si no existe."""
    if not GRAPH_FILE.exists() or not TESTS_FILE.exists():
        print("📦 Dataset no encontrado. Generando...")
        generate(str(DATA_DIR))
        print()


def run_case(graph, tc: dict) -> dict:
    """Ejecuta un caso de prueba y retorna el resultado enriquecido."""
    me = tc["mandatory_edge"]
    result = find_min_cost_route_with_mandatory_edge(
        graph,
        origin=tc["origin"],
        destination=tc["destination"],
        mandatory_u=me["u"],
        mandatory_v=me["v"],
    )
    return result


def print_case(tc: dict, result) -> None:
    print(f"\n{SEP}")
    print(f"  {tc['id']}  |  {tc['description'][:70]}{'...' if len(tc['description'])>70 else ''}")
    print(SEP)
    print(f"  Origen      : {tc['origin']}")
    print(f"  Destino     : {tc['destination']}")
    print(f"  Arista oblig: {tc['mandatory_edge']['u']} → {tc['mandatory_edge']['v']}")
    print()
    print(result.summary())

    # Evidencia explícita de la arista obligatoria
    if result.found:
        u, v = tc["mandatory_edge"]["u"], tc["mandatory_edge"]["v"]
        present = result.mandatory_edge_present()
        icon = "✅" if present else "❌"
        print(f"\n  Validación arista obligatoria {u}→{v}: {icon}")
        if present:
            idx = next(
                i for i in range(len(result.path) - 1)
                if result.path[i] == u and result.path[i + 1] == v
            )
            print(f"  Aparece en posición {idx}→{idx+1} del camino.")

    # Comparar con expectativa del dataset
    exp = tc.get("expected", {})
    exp_found = exp.get("found")
    status_ok = (exp_found is None) or (result.found == exp_found)
    print(f"\n  Resultado esperado 'found={exp_found}': {'✅ correcto' if status_ok else '❌ INCORRECTO'}")
    if exp.get("notes"):
        print(f"  Nota: {exp['notes']}")


def main():
    parser = argparse.ArgumentParser(description="Rutas con arista obligatoria")
    parser.add_argument("--gen", action="store_true", help="Regenerar dataset y salir")
    parser.add_argument("--case", type=str, default=None, help="ID de caso a correr (ej. TC01)")
    args = parser.parse_args()

    if args.gen:
        generate(str(DATA_DIR))
        return

    ensure_data()
    graph = load_graph_from_json(GRAPH_FILE)

    with open(TESTS_FILE, encoding="utf-8") as f:
        test_cases = json.load(f)

    if args.case:
        test_cases = [tc for tc in test_cases if tc["id"] == args.case]
        if not test_cases:
            print(f"❌ Caso '{args.case}' no encontrado.")
            sys.exit(1)

    print(f"\n{'═'*60}")
    print("  RUTAS DE COSTO MÍNIMO CON ARISTA OBLIGATORIA")
    print(f"  Red logística — {len(graph.nodes())} nodos, "
          f"{sum(len(v) for v in graph.adjacency.values())} aristas")
    print(f"{'═'*60}")

    results = []
    for tc in test_cases:
        result = run_case(graph, tc)
        print_case(tc, result)
        results.append(result)

    # Resumen final
    print(f"\n{SEP}")
    total = len(results)
    found_count = sum(1 for r in results if r.found)
    valid_edges = sum(1 for r in results if r.found and r.mandatory_edge_present())
    print(f"  RESUMEN: {total} casos ejecutados")
    print(f"  Con solución   : {found_count}")
    print(f"  Sin solución   : {total - found_count}")
    print(f"  Arista validada: {valid_edges}/{found_count} casos con solución")
    print(SEP)


if __name__ == "__main__":
    main()
