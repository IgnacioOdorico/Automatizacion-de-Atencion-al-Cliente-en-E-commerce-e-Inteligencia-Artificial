# E8 — Factorial 2 × 2: base de conocimiento × reglas y ejemplos

Responde las observaciones obligatorias 1, 2 y 4 del dictamen del 14/09/2026.

## Por qué existe

La ablación E7 comparó el prompt medido el 12/08 con uno reducido y atribuyó la
diferencia a la base de conocimiento. El diseño no lo permite: la condición
reducida no quitó solo la base.

| Bloque del prompt medido | ¿Lo quitó E7? |
|---|---|
| Identidad, tarea, formato de salida | no |
| Reglas de clasificación (incluye la lista de temas de FAQ) | **sí** |
| Base de conocimiento (`{{ $json.faq_context }}`) | **sí** |
| Reglas críticas (incluye «ambiguo entre FAQ y RECLAMO → RECLAMO») | **sí** |
| Siete ejemplos etiquetados | **sí** |
| Mensaje del cliente con nombre y canal | **sí** |

Además quedaron abiertas otras dos cuestiones: no se informaba la temperatura ni la
variabilidad entre corridas, y el workflow que describe el Capítulo 4 corría el
prompt reducido, no el que produjo el 92,7 %.

## Trazabilidad de lo ya medido

`python trazabilidad_e8.py` → `resultados/trazabilidad_versiones.txt`. Consulta el
historial de versiones y publicaciones de n8n:

- **Corpus del Capítulo 5 (12/08):** corrió con la versión `4e2d3bc4`, publicada 4
  minutos antes, con un prompt de 6339 caracteres que incluye base, reglas y
  ejemplos. Coincide byte a byte con el commit `f68da9d`, **no con `f297c9e`**. El
  commit `f297c9e`, citado hasta ahora, guarda el prompt sin el prefijo de expresión
  «=», y en n8n eso es texto literal: la base no se inyectaría.
- **Telegram (25/08):** corrió con el prompt reducido de 1032 caracteres. Los dos
  workflows con disparador de Telegram tienen ese prompt, y el único con el prompt
  principal no tiene ese disparador.
- **E7 (11/09):** corrió con la versión `a4a57b19` (1032 caracteres), según la copia
  del workflow que n8n guarda por cada ejecución.

## Diseño (fijado antes de medir)

El núcleo (identidad, tarea y formato) y el bloque del mensaje del cliente están
presentes en las cuatro condiciones. Varían dos factores:

- **B:** la base de conocimiento.
- **R:** las reglas de clasificación, las reglas críticas y los ejemplos.

| Condición | B | R | Caracteres | md5 del prompt |
|---|---|---|---|---|
| **C1** | sí | sí | 6339 | `c11c2fe1cdd4f5c2eedd7e8f9b013c3c` (el medido el 12/08) |
| **C2** | — | sí | 6151 | `64f3a3ab58dca4c1096e9c4c7f4d3a3c` |
| **C3** | sí | — | 1343 | `ed36a93c8d1eb833168fadf55ba7afbf` |
| **C4** | — | — | 1155 | `32c29bb6f042aac16f1813724c65b474` |

`condiciones_e8.py` arma los cuatro prompts desde el commit `f68da9d` y aborta si
C1 no reproduce el prompt medido. Al armar el workflow de cada condición verifica
que no cambie nada más que el prompt.

- **Corpus y etiquetas:** los 150 mensajes y las etiquetas de referencia del
  Capítulo 5 (`experiments/E2`).
- **Repeticiones:** 3 por condición, 12 bloques y 1800 llamadas.
- **Orden:** ninguna condición repite posición dentro de su repetición.

  | Repetición | Orden de los bloques |
  |---|---|
  | R1 | C1, C2, C4, C3 |
  | R2 | C2, C3, C1, C4 |
  | R3 | C3, C4, C2, C1 |

- **Parámetros constantes:**
  - Modelo gpt-4o-mini.
  - Temperatura no fijada en el nodo, por lo que rige el valor por defecto de la API de
    OpenAI (1). Verificado en el código del nodo: `temperature` no se envía si no se
    configura.
  - Nombre del cliente «Anotador E2», el mismo del 12/08.
  - Un segundo entre envíos.
  - Endpoint `/webhook/whatsapp-business`.
- **Aislamiento:** user_id `E8-<condición>-R<repetición>-<id>@whatsapp.sim`. Las
  pruebas previas llevan el prefijo `E8-PRUEBA-` y no entran al análisis.

## Verificación de cada bloque (`run_e8.ps1`)

1. **Antes de enviar:** el md5 del prompt de la versión activa del workflow tiene que
   ser el de la condición.
2. **Después de enviar:** cada ejecución registrada en n8n guarda una copia del
   workflow. Se exporta el md5 del prompt de cada una a
   `resultados/e8_evidencia_<bloque>.csv`.
3. **Criterio de validez:** el bloque es válido solo si cumple las tres condiciones.
   - Recibió 150 respuestas HTTP 200.
   - Escribió 150 filas.
   - Todas las ejecuciones llevan el prompt de su condición.

   Si un bloque es inválido, la corrida se detiene.

## Análisis pre-registrado (`analizar_e8.py`)

- **Medida primaria: exactitud por mayoría.** Un mensaje cuenta como acierto si
  acertó en al menos 2 de las 3 repeticiones. Se reporta con IC 95 % de Wilson.
- **Variabilidad:** media, desvío y rango de las 3 repeticiones por condición, y
  proporción de mensajes con la misma etiqueta en las 3.
- **Contrastes:** McNemar exacto sobre la corrección por mayoría para los 6 pares,
  con ajuste de Holm y alfa 0,05.
- **Efectos:** efecto principal de B, efecto principal de R, interacción y efectos
  simples, en puntos porcentuales.
- **Por clase:** exhaustividad por clase y migración FAQ → GENERAL.
- **H2b, sobre C1:** se sostiene si el **límite inferior del IC 95 % de Wilson** de la
  exactitud por mayoría es ≥ 85 %.
- **Sensibilidad:** se excluyen los mensajes con similitud ≥ 0,80 con algún
  ejemplo del prompt. Hoy es uno: «cuanto sale el envio a cordoba?», frente al ejemplo
  «cuánto tarda el envío a córdoba?».
- **Réplica:** C1 frente a la corrida del 12/08.
- **Secundario:** TMR por condición.

**Lo que no se hace:**
- No se descarta un bloque válido.
- No se cambia la medida primaria ni el ajuste de Holm.
- Un bloque inválido se vuelve a correr y se informan los dos.

## Independencia entre prompt y corpus

Las reglas y los ejemplos están en el prompt desde el 22/04/2026 (commit `ebbd17c`).
El corpus se congeló el 10/08/2026 (commit `77a5a04`), 110 días después.

La similitud máxima entre un ejemplo y un mensaje del corpus es 0,89, en el par de
Córdoba. La siguiente es 0,66. El análisis de sensibilidad excluye ese mensaje.

## Límites

- El experimento corre sobre el workflow vigente, de 18 nodos. La corrida del 12/08
  usó el de 14. El prompt y el camino de clasificación son los mismos; cambian los
  disparadores y el enrutamiento de salida.
- El alias gpt-4o-mini puede apuntar a otra versión del modelo que la del 12/08.
- Con temperatura 1, las diferencias chicas entre condiciones pueden no sostenerse.
  Para eso están las repeticiones.

## Procedimiento

```
python condiciones_e8.py --pruebas
python condiciones_e8.py construir
python analizar_e8.py --pruebas
powershell -File run_e8_todo.ps1        # 12 bloques; deja C1 como configuración vigente
python analizar_e8.py > resultados/analisis_e8.txt
python trazabilidad_e8.py
```
