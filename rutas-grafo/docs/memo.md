# Memo Técnico — Rutas con Arista Obligatoria

**Proyecto:** Red logística de distribución de paquetes  
**Fecha:** Junio 2025  
**Alcance:** Máximo 1 página

---

## Enfoque

El problema se mapea como un grafo dirigido ponderado donde nodos son centros
de distribución y aristas son rutas de transporte con costo en minutos. El
requisito de arista obligatoria representa un punto de control ineludible
(aduanas, hubs de alta capacidad).

La solución descompone el problema en dos sub-problemas independientes de
Dijkstra: ruta mínima de `o → u` y ruta mínima de `v → d`. El costo total
es la suma de ambos tramos más el peso de la arista obligatoria. Este enfoque
es exacto por el principio de optimalidad: si la ruta global es óptima y pasa
por `(u,v)`, entonces sus tramos anterior y posterior también son óptimos.

## Decisiones clave

**Por qué 2× Dijkstra y no una sola corrida con penalización:** Penalizar
todos los caminos que no pasan por `(u,v)` requiere modificar el grafo de
forma compleja y no garantiza exactitud. La descomposición en dos Dijkstra es
algorítmicamente limpia, verificable y fácil de depurar.

**Por qué JSON para el dataset:** Permite reproducibilidad total, es legible
por humanos y separa claramente los datos de la lógica, facilitando cambiar
el grafo sin tocar el código.

**Por qué no se soportan pesos negativos:** El caso de negocio (costos de
tránsito en minutos) no los requiere. Soportarlos implicaría Bellman-Ford
con complejidad O(VE), innecesariamente costoso.

## Limitaciones

- **Grafo en memoria:** El dataset completo debe caber en RAM. Para redes de
  millones de aristas (ej. maps de navegación) se requeriría almacenamiento
  externo y Dijkstra bidireccional o A*.
- **Una sola arista obligatoria:** La solución no generaliza directamente a k
  aristas obligatorias (requeriría programación dinámica o enumeración).
- **Sin pesos negativos:** Si el caso de negocio incluye descuentos o créditos,
  habría que migrar a Bellman-Ford.
- **Unicidad no garantizada:** En empate de costos se devuelve uno de los
  caminos óptimos sin control sobre cuál.

## Mejoras posibles con más tiempo

1. **k aristas obligatorias:** Modelar como problema de camino hamiltoniano
   parcial o usar DP sobre subconjuntos.
2. **Visualización del grafo:** Renderizar el grafo y resaltar la ruta
   encontrada con networkx + matplotlib.
3. **API REST:** Exponer el solver como microservicio para integración con
   sistemas logísticos reales.
4. **Benchmarks de escalabilidad:** Medir el tiempo de respuesta con grafos
   de 10k, 100k y 1M aristas para determinar el límite práctico.
5. **Persistencia:** Reemplazar JSON por una base de datos de grafos (ej.
   Neo4j) para consultas más expresivas y actualización incremental.

---

*La parte más frágil de la implementación es la reconstrucción del camino
mediante el dict `prev` en presencia de ciclos con peso 0: Dijkstra converge
correctamente, pero la reconstrucción puede incluir el ciclo en la ruta
visible (como en TC03). El resultado sigue siendo válido y óptimo, pero
puede sorprender a quienes esperan un camino simple.*
