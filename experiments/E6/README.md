# E6 — Evaluación de la corrección del contenido de las respuestas FAQ

Ejecuta el procedimiento que el Capítulo 7 de la tesis deja especificado y que
el trabajo todavía no había ejecutado. Cierra el único riesgo de validez que la
auditoría de 2.ª instancia dejó abierto.

## Qué mide

El Capítulo 5 mide que el clasificador acierta la intención (92,7 %) y que el
sistema responde rápido (1,47 s). **No mide si la respuesta es correcta.** Y la
Sección 4.4.3 declara por qué eso importa: el nodo que arma el contexto de FAQ
existe, pero su salida nunca llega al prompt. El prompt de sistema son 1032
caracteres que definen identidad, tarea y formato de salida — ninguna política
de la tienda.

O sea que las respuestas de tipo FAQ salen del conocimiento general del modelo
sobre e-commerce, no de las 23 entradas de TechStore. Este experimento mide
cuánto se parecen unas a otras.

## Muestra

45 interacciones clasificadas como FAQ por el modelo, de la corrida del corpus
(`data_source='measured'`, ventana 2026-08-12 23:00 a 00:00). Todas con
respuesta entregada; 235 caracteres de media.

## Rúbrica (tres niveles, como declara el Capítulo 7)

| | |
|---|---|
| **A** | Consistente con la política: coincide con la base de conocimiento |
| **B** | Genérica pero no contradictoria: cierta para cualquier tienda, no afirmada por la base |
| **C** | Contradice la política vigente |

La frontera A/B es lo que el experimento mide. Una respuesta plausible que la
tienda no sostiene es B, no A.

## Procedimiento

1. `python preparar_e6.py` — genera un HTML por evaluador. Misma muestra, orden
   distinto (semilla propia), salida propia. Sólo 1 de 45 posiciones coincide.
2. Cada evaluador abre **su** archivo, lo completa sin consultar al otro, y
   descarga su CSV a `resultados/`.
3. `python analizar_e6.py resultados/e6_maximo_muguruza.csv resultados/e6_joaquin_maya.csv`

## Control de validez

Se registra el tiempo por ítem. Si la mediana baja de 8 s, la evaluación se
declara inválida y el análisis **no se reporta**. Es el mismo control forense
que invalidó la primera ronda del etiquetado de intenciones (Sección 3.5.3) y
corresponde aplicarlo acá por la misma razón.

## Archivos

| | |
|---|---|
| `faq_respuestas.csv` | las 45 interacciones, exportadas de la base |
| `preparar_e6.py` | genera los dos instrumentos |
| `etiquetar_e6_*.html` | un instrumento por evaluador |
| `analizar_e6.py` | κ de Cohen, distribución, desacuerdos caso por caso |
