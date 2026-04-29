# Rutas de Costo Mínimo con Arista Obligatoria

## Descripción del enfoque

Se modela una **red logística de distribución de paquetes** como un grafo
dirigido ponderado. Cada nodo es un centro de distribución y cada arista es
una ruta de transporte con un costo en minutos de tránsito.

El problema central consiste en encontrar el camino de costo mínimo entre un
origen `o` y un destino `d` que **obligatoriamente** pase por la arista
`(u → v)` — representando, por ejemplo, un punto de control aduanal o un hub
de alta prioridad.

### Algoritmo

Se descompone el problema en dos corridas de **Dijkstra**:

```
Ruta final = ruta_min(o → u) ++ arista(u,v) ++ ruta_min(v → d)
```

El principio de optimalidad garantiza que, si la ruta global pasa por `(u,v)`,
los tramos anterior y posterior son mínimos por separado. La arista obligatoria
siempre aparece en la posición exacta de la unión.

**Complejidad:** O((V + E) log V) × 2 corridas de Dijkstra.

---

## Estructura del proyecto

```
rutas-grafo/
├── main.py                  # Punto de entrada (CLI)
├── src/
│   ├── graph.py             # Estructura de datos: grafo dirigido ponderado
│   ├── solver.py            # Lógica principal: Dijkstra + arista obligatoria
│   ├── loader.py            # Carga el grafo desde JSON
│   └── generate_dataset.py  # Genera el dataset sintético
├── tests/
│   └── test_solver.py       # Suite de pruebas
├── data/                    # Generado automáticamente
│   ├── graph.json
│   └── test_cases.json
└── docs/
    └── memo.md
```

---

## Cómo generar los datos

```bash
python main.py --gen
```

O directamente:

```bash
python -m src.generate_dataset
```

Esto crea `data/graph.json` (11 nodos, 19 aristas) y `data/test_cases.json`
(6 casos de prueba).

---

## Cómo correr la solución

### Todos los casos de prueba

```bash
python main.py
```

### Un caso específico

```bash
python main.py --case TC01
python main.py --case TC02
```

### Suite de pruebas (requiere pytest)

```bash
python -m pytest tests/test_solver.py -v
```

---

## Formato de entradas y salidas

### Entrada (graph.json)

```json
{
  "nodes": [{"id": "CDMX", "name": "Ciudad de México"}],
  "edges": [{"source": "CDMX", "target": "QRO", "weight": 3, "label": "Autopista 57"}]
}
```

### Entrada del solver (Python API)

```python
result = find_min_cost_route_with_mandatory_edge(
    graph,
    origin="CDMX",
    destination="TIJ",
    mandatory_u="QRO",
    mandatory_v="HUB"
)
```

### Salida (RouteResult)

| Campo                | Tipo    | Descripción                                      |
|----------------------|---------|--------------------------------------------------|
| `found`              | bool    | True si existe solución válida                   |
| `path`               | list    | Lista de nodos en el camino                      |
| `total_cost`         | float   | Costo total de la ruta                           |
| `reason`             | str     | Explicación del fallo si `found=False`           |
| `mandatory_edge_present()` | bool | Verificación de que la arista aparece en la ruta |

---

## Supuestos y limitaciones

- **Sin pesos negativos.** El algoritmo usa Dijkstra; pesos negativos requieren
  Bellman-Ford.
- **La arista obligatoria debe existir** en el grafo (validación explícita).
- **Primer peso mínimo gana** si hay múltiples aristas entre el mismo par de
  nodos.
- **No garantiza unicidad.** Si hay empate de costos, se devuelve uno de los
  caminos óptimos (el que Dijkstra encuentre primero).
- **Grafo en memoria.** No hay persistencia entre ejecuciones más allá del JSON.
- **Ciclos permitidos.** El grafo puede tener ciclos; Dijkstra los maneja
  correctamente con pesos ≥ 0.

---

## Casos de prueba incluidos

| ID   | Tipo           | Descripción breve                                    | Resultado esperado |
|------|----------------|------------------------------------------------------|--------------------|
| TC01 | Válido         | CDMX→TIJ con arista obligatoria QRO→HUB             | Costo=11, ruta encontrada |
| TC02 | Sin solución   | CDMX→CAN con arista QRO→HUB (HUB no llega a CAN)    | No encontrado      |
| TC03 | Borde (peso 0) | CDMX→MTY con arista HUB→QRO (peso 0, ciclo)         | Costo=7, ruta con ciclo válida |
| TC04 | Borde (aislado)| CDMX→ISO, la arista obligatoria es CDMX→ISO          | Costo=1, ruta directa |
| TC05 | Sin solución   | Arista obligatoria GDL→CAN no existe en el grafo     | Error claro        |
| TC06 | Borde (o==u)   | Origen coincide con u de la arista obligatoria       | Costo=5, sin tramo previo |

### Por qué el dataset valida la lógica

- **TC01** prueba el flujo completo: dos Dijkstra, reconstrucción y validación.
- **TC02** prueba que el solver detecta correctamente sub-grafos desconectados.
- **TC03** prueba robustez ante peso 0 y ciclos; verifica que Dijkstra no entra
  en bucle infinito.
- **TC04** prueba el caso degenerado donde origen, u, v y destino colapsan.
- **TC05** prueba la validación previa de que la arista existe antes de correr
  el algoritmo.
- **TC06** prueba que el tramo `o→u` de longitud cero se maneja correctamente.

---

## Explicación del algoritmo

```
1. Validar que origen, destino, u, v existen en el grafo.
2. Validar que la arista (u,v) existe en el grafo.
3. Dijkstra(origen) → distancias desde origen a todos los nodos.
   - Si dist[u] == ∞ → no hay camino de origen a u → sin solución.
4. Dijkstra(v) → distancias desde v a todos los nodos.
   - Si dist[destino] == ∞ (y v ≠ destino) → sin solución.
5. Costo total = dist_origen[u] + peso(u,v) + dist_v[destino]
6. Reconstruir camino completo concatenando los dos caminos óptimos.
7. Verificar que (u,v) aparece en la posición de unión.
```

---

## Decision log

| Alternativa considerada             | Por qué se descartó / eligió                                       |
|-------------------------------------|--------------------------------------------------------------------|
| BFS sin pesos                       | No minimiza costo, solo número de saltos.                          |
| Bellman-Ford                        | Soporta pesos negativos pero es O(VE); innecesario aquí.           |
| A* con heurística geográfica        | Requiere coordenadas; el dataset es abstracto.                     |
| Forzar paso por u→v con penalización| Difícil de garantizar; la descomposición en 2 Dijkstra es exacta.  |
| **2× Dijkstra (elegido)**           | Simple, correcto, O((V+E) log V), fácil de verificar y explicar.  |
