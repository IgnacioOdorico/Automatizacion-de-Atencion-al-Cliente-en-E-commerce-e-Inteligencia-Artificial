# E6 — Contenido de las respuestas de tipo FAQ

Datos y guiones de las Secciones 3.5.7 y 5.2.5 de la tesis, y de su Anexo K.

## Qué mide

El Capítulo 5 mide que el clasificador acierta la intención y que el sistema
responde rápido. **No mide si lo que responde es correcto.** Este experimento
intenta acotar esa dimensión.

Las 45 respuestas evaluadas se generaron con la configuración principal del
Flujo 2, cuyo prompt **inyecta** las 23 entradas de la base de conocimiento
(Sección 4.4.3; ablación en `experiments/E7`). La pregunta no es si el modelo
conoce la política de la tienda, sino si **se atiene a la base que recibe**.

## Muestra

45 interacciones clasificadas como FAQ en la corrida del corpus
(`data_source='measured'`), todas con respuesta entregada; 235 caracteres de
media. Exportadas a `faq_respuestas.csv`.

## Vía 1 — Evaluación por jueces

Dos evaluadores ajenos al equipo (Máximo Muguruza y Joaquín Maya) juzgaron cada
respuesta contra las 23 entradas, con una rúbrica de tres niveles:

| | |
|---|---|
| **A** | Consistente con la política |
| **B** | Genérica pero no contradictoria |
| **C** | Contradice la política vigente |

Cada uno con su propio instrumento (`etiquetar_e6_*.html`, generado por
`preparar_e6.py`) y la muestra en un orden aleatorio distinto. El instrumento
registra el tiempo por respuesta: una corrida con mediana menor a 8 s se declara
inválida y no entra en ningún cálculo.

**Resultado** (`python analizar_rondas_e6.py` → `resultados/rondas_e6.txt`):

| Corrida | Fecha | Mediana | Validez |
|---|---|---|---|
| Máximo 1 | 2026-09-11 | 10,0 s | válida |
| Joaquín 1 | 2026-09-11 | 4,0 s | inválida |
| Joaquín 2 | 2026-09-11 | 5,0 s | inválida |
| Joaquín 3 | 2026-09-14 | 8,8 s | válida |
| Máximo 2 | 2026-09-14 | 9,2 s | válida |
| Joaquín 4 | 2026-09-14 | 6,3 s | inválida |

| Comparación entre corridas válidas | Coinciden | κ de Cohen |
|---|---|---|
| Máximo 1 × Joaquín 3 | 27 de 45 | 0,167 (leve) |
| Joaquín 3 × Máximo 2 | 31 de 45 | 0,358 (aceptable) |
| Máximo 1 × Máximo 2 (consigo mismo) | 30 de 45 | 0,318 |

Ningún acuerdo llega a moderado (0,41). **No se reporta ninguna proporción de
respuestas correctas.** La causa es estructural: los niveles no son excluyentes.
Una respuesta que copia una entrada y le agrega un dato inventado cabe en A y en
C; una política genérica inventada cabe en B y en C. El diagnóstico caso por caso
de la primera comparación está en `resultados/v1/diagnostico_v1.md`. La propuesta
de instrumento corregido quedó como línea futura en la Sección 7.2 de la tesis.

## Vía 2 — Verificación automática de datos concretos

`verificar_datos_e6.py` extrae de cada respuesta los **datos concretos** (una
cifra o un rango seguido de una unidad: días, días hábiles, horas, horas hábiles,
meses, semanas, años, cuotas, minutos, %) y comprueba si cada uno figura en
alguna entrada de la base con la misma unidad y las mismas cifras. Si no figura
pero sus cifras ya estaban en el mensaje del cliente, se clasifica como eco.

```
python verificar_datos_e6.py --pruebas   # pruebas de la regla
python verificar_datos_e6.py             # → resultados/verificacion_datos.{txt,csv}
```

**Resultado:** 18 de las 45 respuestas afirman al menos un dato concreto (21 en
total): 18 respaldados, 1 eco y 2 no respaldados. **2 de las 18 respuestas**
(11,1 %; IC 95 % de Wilson 3,1 % a 32,8 %) afirman un dato ausente de la base:

- 326, «cual es el horario de atencion?» → «de lunes a viernes de 9 a 18 hs».
- 337, «cuanto demora el reintegro de una devolucion?» → «entre 5 y 10 días hábiles».

**Límites declarados:** no alcanza a afirmaciones sin cifra, y no controla el
contexto (la respuesta 352 usa un plazo de 24 horas hábiles que la base tiene,
pero para otra cosa, y figura como respaldado). Es una **cota inferior** de lo que
las respuestas agregan. La regla se fijó con conocimiento del corpus; por eso se
publica con sus pruebas.

## Archivos

| | |
|---|---|
| `faq_respuestas.csv` | las 45 respuestas evaluadas |
| `preparar_e6.py`, `etiquetar_e6_*.html` | instrumento de la evaluación por jueces |
| `analizar_e6.py` | análisis de un par de corridas (tiempos, κ, desacuerdos) |
| `analizar_rondas_e6.py` | las seis corridas: validez, κ entre evaluadores y consigo mismo |
| `verificar_datos_e6.py` | verificación automática, con `--pruebas` |
| `resultados/v1/` | primera ronda: corridas, descartadas, análisis y diagnóstico |
| `resultados/ronda2/` | segunda ronda: corridas y análisis |
| `resultados/rondas_e6.txt` | salida de `analizar_rondas_e6.py` |
| `resultados/verificacion_datos.{txt,csv}` | salida de `verificar_datos_e6.py` (el CSV es la Tabla K.1) |
