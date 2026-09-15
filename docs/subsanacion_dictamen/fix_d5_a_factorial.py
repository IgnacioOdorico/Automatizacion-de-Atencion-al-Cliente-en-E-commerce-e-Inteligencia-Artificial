# -*- coding: utf-8 -*-
"""Dictamen del 14/09, obligatorias 1, 2 y 4: el diseño factorial E8 en la tesis.

  - §2.2.2, §2.5.2 y Tabla 2.1: cuatro configuraciones de prompt, no dos.
  - §3.5.4: métodos estadísticos con su referencia y la regla de H2b.
  - §3.5.6: el protocolo factorial reemplaza al de E7, que confundía factores.
  - §4.4.3: estructura real del prompt (ocho bloques), alias del modelo,
    temperatura e historia de versiones con su evidencia.
  - §4.6 y §5.2.2: Telegram corrió con el prompt reducido.
  - §5.2.4: resultados del factorial (Tabla 5.10 con cuatro condiciones).
  - §5.4, §6.3 y Tabla 6.1 (OE2): la conclusión se invierte.
  - Anexo D: las 23 entradas íntegras. Anexo H: el prompt medido completo,
    cómo se arman C1 a C4, el prompt de E7 y el commit correcto (f68da9d).

NO es idempotente: aborta si §3.5.6 ya tiene el título nuevo.
Se ejecuta desde la raíz del repositorio.
"""
import io
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('3.5.6 Diseño factorial'):
    sys.exit('ERROR: este guion ya se aplicó.')

C1 = io.open('experiments/E8/prompts/C1.txt', encoding='utf-8', newline='').read().replace('\r\n', '\n').rstrip('\n')
E7 = ('# --- START ---\n\nSos un asistente virtual de atención al cliente de "TechStore", un e-commerce argentino de '
      'tecnología.\n\n## IDENTIDAD\n- Nombre: Asistente TechStore\n- Tono: cálido, humano, profesional — como si fuera '
      'una persona real de atención al cliente\n- Idioma: respondé SIEMPRE en el mismo idioma que el cliente. Si escribe '
      'en inglés, respondé en inglés. Si escribe en español, usá español argentino (voseás: vos, tenés, podés)\n- NO sos '
      'un chatbot genérico — representás a TechStore con orgullo\n- Usá el nombre del cliente si está disponible — hace '
      'que la conversación se sienta más personal\n\n## TU TAREA\nAnalizá el mensaje del cliente, clasificá su intención, '
      'y generá una respuesta genuinamente útil y humana.\nRespondé ÚNICAMENTE con un JSON válido. Sin texto antes ni '
      'después del JSON. Sin markdown. Sin ```json```.\n\n## FORMATO DE RESPUESTA (JSON estricto)\n{\n  "intent": "FAQ | '
      'ESTADO_PEDIDO | RECLAMO | GENERAL",\n  "order_id": null,\n  "urgente": false,\n  "respuesta": "texto cálido, claro '
      'y personalizado para el cliente"\n}')
assert len(E7) == 1032, 'el prompt de E7 no tiene 1032 caracteres: %d' % len(E7)
# 6339 caracteres guardados = signo «=» + 6337 de texto + salto de línea final (6338 sin el signo)
assert C1.startswith('=# --- START ---') and len(C1) == 6338, 'C1 inesperado: %d' % len(C1)

# ============================================================ §2.2.2
k.reescribir('Corresponde precisar el régimen de prompting empleado',
    'El régimen de prompting empleado tiene consecuencias sobre la interpretación de los resultados. Brown et al. '
    '(2020) diferencian tres regímenes según la cantidad de ejemplos etiquetados que se incluyen en el prompt: '
    'zero-shot, donde el modelo recibe únicamente la instrucción y la definición de las clases; one-shot, con un '
    'ejemplo; y few-shot, con varios ejemplos de entrada y salida. Liu et al. (2023) sistematizan el conjunto de estas '
    'técnicas. La configuración principal de este trabajo opera en régimen few-shot con recuperación de contexto: su '
    'prompt de sistema incluye reglas de decisión por categoría, siete ejemplos etiquetados de entrada y salida y un '
    'bloque en el que se inyecta la base de conocimiento de la tienda, recuperada de la base de datos en tiempo de '
    'ejecución. El Capítulo 5 la compara con tres variantes que quitan la base de conocimiento, las reglas y los '
    'ejemplos, o ambas cosas; las dos que no tienen ejemplos operan en régimen zero-shot. Los bloques del prompt se '
    'transcriben en el Anexo H y la comparación se reporta en la Sección 5.2.4.')

# ============================================================ §2.5.2 y Tabla 2.1
k.reemplazo('ninguno de los dos valores obtenidos es un dato aislado', 'ninguno de los valores obtenidos es un dato aislado')
k.reemplazo('—del tipo de CLINC150, Banking77 o SNIPS—',
            '—del tipo de CLINC150 (Larson et al., 2019), Banking77 (Casanueva et al., 2020) o SNIPS (Coucke et al., 2018)—')
t21 = k.tabla(['Antecedente', 'Dominio'])
f = k.fila(t21, 'Este trabajo')
k.celda(t21, f, 2, 'Orquestación con n8n y clasificación con LLM; diseño factorial sobre la base de conocimiento y '
                   'las reglas y ejemplos del prompt')
k.celda(t21, f, 3, 'MTTD, MTTR y TMR contra baseline manual medido; exactitud en cuatro configuraciones de prompt, '
                   'con tres repeticiones')

# ============================================================ §3.5.4
k.reemplazo('Para el contraste de la hipótesis sobre precisión de clasificación (H2b) se calcula el intervalo de '
            'confianza del 95% por el método de Wilson, apropiado',
            'Para el contraste de la hipótesis sobre la exactitud de clasificación (H2b) se calcula el intervalo de '
            'confianza del 95 % por el método de Wilson (1927), apropiado')
k.reemplazo('y el acuerdo entre anotadores mediante el coeficiente κ de Cohen.',
            'y el acuerdo entre anotadores mediante el coeficiente κ de Cohen (1960). La regla de decisión sobre H2b '
            'es que el límite inferior de ese intervalo sea igual o mayor que el 85 % (Sección 1.4.2).')
k.reemplazo('se adopta como prueba principal la U de Mann-Whitney, elegida',
            'se adopta como prueba principal la U de Mann-Whitney (Mann y Whitney, 1947), elegida')
k.reemplazo('Se la acompaña de la t de Welch, que no supone', 'Se la acompaña de la t de Welch (1947), que no supone')
k.reemplazo('se calcula por el teorema de Fieller y no por', 'se calcula por el teorema de Fieller (1954) y no por')

# ============================================================ §3.5.6
k.reescribir('3.5.6 Ablación del contexto de la base de conocimiento',
             '3.5.6 Diseño factorial del prompt: base de conocimiento, reglas y ejemplos')
k.reescribir('El prompt de la configuración principal combina tres elementos',
    'El prompt de la configuración principal combina elementos que la literatura trata por separado: reglas de '
    'decisión, ejemplos etiquetados y recuperación de contexto (Sección 2.2.2). Medir el clasificador con todos ellos '
    'no permite atribuir el resultado a ninguno, ni estimar cuánto aporta la base de conocimiento de la tienda, que es '
    'la pieza que una PyME tendría que construir y mantener. Una primera ablación (E7) comparó la configuración '
    'principal con un prompt reducido y atribuyó la diferencia a la base de conocimiento. El diseño no lo permitía, '
    'porque aquel prompt no quitaba solo la base sino cinco de los ocho bloques del prompt: las reglas de '
    'clasificación, la base de conocimiento, las reglas críticas, los ejemplos y el bloque que presenta el mensaje del '
    'cliente con su nombre y su canal. Los factores quedaban confundidos. Se la reemplazó por el diseño factorial que '
    'se describe a continuación (E8); la ablación E7 se conserva en el repositorio como antecedente.')
k.reescribir('Diseño. Se pasa el mismo corpus de 150 mensajes',
    'Diseño. El prompt medido tiene ocho bloques, que se transcriben en el Anexo H. Cuatro están presentes en todas '
    'las condiciones: identidad, tarea, formato de salida y mensaje del cliente. Los otros cuatro definen dos factores. '
    'El factor B es la base de conocimiento; el factor R agrupa las reglas de clasificación, las reglas críticas y los '
    'ejemplos, porque los tres son instrucciones de decisión escritas por el equipo. Al cruzarlos resultan cuatro '
    'condiciones: C1, con base, reglas y ejemplos, que reproduce byte a byte el prompt de la configuración principal; '
    'C2, sin la base; C3, sin las reglas ni los ejemplos; y C4, sin ninguno de los dos factores. Todas corren sobre el '
    'mismo corpus de 150 mensajes, el mismo modelo y las mismas etiquetas de referencia, y el guion que arma el '
    'workflow de cada condición verifica que no cambie nada más que el texto del prompt. Como el nodo del modelo no '
    'fija la temperatura, rige el valor por defecto de la API, que es 1, y un mismo mensaje puede recibir etiquetas '
    'distintas en corridas distintas. Por eso cada condición se ejecuta tres veces, en un orden en que ninguna '
    'condición repite posición dentro de su repetición: doce bloques y 1800 clasificaciones.')
k.reescribir('Criterio de análisis. El diseño es apareado',
    'Criterio de análisis. El diseño, los contrastes y la regla de decisión se fijaron antes de medir y se versionaron '
    'en el repositorio. La medida primaria es la exactitud por mayoría: un mensaje cuenta como acierto si la condición '
    'lo clasificó bien en al menos dos de las tres repeticiones. Se reporta con su intervalo de confianza de Wilson al '
    '95 % (Wilson, 1927), junto con la media, el desvío y el rango de las tres repeticiones y la proporción de mensajes '
    'que recibieron la misma etiqueta en las tres. Como el diseño es apareado, los seis pares de condiciones se '
    'contrastan con la prueba exacta de McNemar sobre los pares discordantes (McNemar, 1947), con el ajuste de Holm '
    '(1979) para comparaciones múltiples y un nivel de significación de 0,05. Se estiman además los efectos principales '
    'de cada factor y su interacción, en puntos porcentuales, y el desglose por clase. Dos controles completan el '
    'análisis: una réplica de la configuración principal frente a la corrida del corpus del 12 de agosto, y un análisis '
    'de sensibilidad que excluye los mensajes del corpus cuya similitud con algún ejemplo del prompt es igual o mayor '
    'que 0,80.')
k.reescribir('Aislamiento de las poblaciones. Las interacciones de la corrida de ablación',
    'Aislamiento y verificación de cada bloque. Las interacciones de cada bloque se registran con un prefijo propio en '
    'el identificador de usuario, que nombra la condición y la repetición, de modo que quedan separadas de la corrida '
    'del corpus de manera permanente y ninguna cifra de la Sección 5.2.3 se ve afectada. Antes de enviar, el guion de '
    'ejecución comprueba que el prompt de la versión activa del workflow sea el de la condición. Después lee, de la '
    'copia del workflow que el motor de flujos guarda con cada ejecución, la huella del prompt con que corrió, y la '
    'exporta como evidencia. Un bloque es válido si recibió 150 respuestas, si todas sus ejecuciones llevan el prompt '
    'de su condición y si las filas registradas más las etiquetas fuera del vocabulario admitido suman 150. Esa última '
    'cláusula es uno de los dos desvíos del protocolo, y ambos se declaran en el repositorio con su fecha: cuando el '
    'modelo devuelve una categoría inexistente, la restricción de integridad de la tabla de interacciones rechaza la '
    'escritura, y la interacción se cuenta como error de clasificación en lugar de invalidar el bloque (Sección 5.2.4). '
    'El otro desvío es una espera de conciliación agregada al guion, porque el webhook responde antes de que la '
    'ejecución termine de escribir.')

# ============================================================ §4.4.3
k.reescribir('El nodo de GPT-4o-mini recibe un prompt de sistema que define',
    'El nodo de GPT-4o-mini recibe un prompt de sistema que define la identidad del asistente, la tarea de '
    'clasificación, las cuatro categorías de intención admitidas —enumeradas dentro del esquema de salida como FAQ, '
    'ESTADO_PEDIDO, RECLAMO y GENERAL— y el formato estricto de la respuesta: un objeto JSON con los campos intent, '
    'order_id, urgente y respuesta. El prompt de la configuración vigente, que es el que produjo el 92,7 % del '
    'Capítulo 5, tiene 6338 caracteres y ocho bloques: identidad y tono del asistente; definición de la tarea; formato '
    'de salida; reglas de clasificación por categoría, entre ellas cuándo un mensaje debe marcarse como urgente; un '
    'bloque rotulado «base de conocimiento», en el que se inyecta el contenido de la tabla faq_responses recuperado en '
    'tiempo de ejecución, con la instrucción de usar exclusivamente esa información para responder consultas '
    'frecuentes; diez reglas críticas, entre ellas la de clasificar como reclamo un mensaje ambiguo entre consulta '
    'frecuente y reclamo; siete ejemplos etiquetados de entrada y salida; y el mensaje del cliente, con su nombre y su '
    'canal. Opera por lo tanto en régimen few-shot y con recuperación de contexto. La cadena que provee ese contexto '
    'son los nodos Buscar FAQ en PostgreSQL y Preparar Contexto FAQ, que sí inciden en la salida del sistema en la '
    'configuración medida. El texto íntegro se transcribe en el Anexo H, junto con las variantes que compara la '
    'Sección 5.2.4.')
k.reescribir('Se eligió GPT-4o-mini por su balance entre costo y capacidad',
    'Se eligió GPT-4o-mini por su balance entre costo y capacidad: para la clasificación de intenciones en un dominio '
    'acotado y la generación de respuestas de soporte no se requiere la potencia completa de GPT-4o. El nodo invoca el '
    'modelo por su alias, gpt-4o-mini, que el proveedor puede asociar a distintas versiones a lo largo del tiempo, y no '
    'fija la temperatura ni ningún otro parámetro de muestreo: rige por lo tanto el valor por defecto de la API, que es '
    '1. La consecuencia es que un mismo mensaje puede recibir etiquetas distintas en corridas distintas. La Sección '
    '5.2.4 la cuantifica sobre tres repeticiones del corpus: con la configuración vigente, el 98,0 % de los mensajes '
    'recibió la misma etiqueta en las tres, y la exactitud de cada repetición varió entre 92,7 % y 93,3 %.')
k.reescribir('Corresponde declarar cómo se llegó a esta precisión',
    'La historia de versiones de este nodo se declara porque una versión anterior de este documento la describió mal, '
    'y el error es instructivo. El corpus del Capítulo 5 corrió el 12 de agosto sobre el workflow de catorce nodos, con '
    'el prompt de 6338 caracteres descripto arriba: el historial de versiones del motor de flujos registra que esa '
    'versión se publicó cuatro minutos antes de la corrida, y su prompt coincide byte a byte con el del commit f68da9d '
    'del repositorio. El 25 de agosto se incorporó el workflow de dieciocho nodos, que suma el canal de Telegram, con '
    'un prompt reducido de 1032 caracteres que no inyecta la base de conocimiento ni contiene reglas ni ejemplos. Con '
    'ese prompt corrieron las 45 interacciones de Telegram de la Sección 5.2.2 y la ablación E7, y ese workflow fue el '
    'vigente hasta el 15 de septiembre, cuando el diseño factorial restituyó en él el prompt de la configuración '
    'principal. Al auditar el workflow para documentar el prompt se había tomado el archivo vigente en ese momento, y '
    'de ahí se concluyó que el clasificador operaba en régimen zero-shot. La auditoría fue correcta en su método y se '
    'aplicó al artefacto equivocado. La regla que de ello se sigue vale más que el caso: una afirmación sobre cómo se '
    'obtuvo una medición debe verificarse contra la versión del artefacto que corrió en la fecha de esa medición, no '
    'contra la versión actual. La reconstrucción, consultada sobre el historial de versiones y de publicaciones del '
    'motor de flujos, se versiona en experiments/E8/resultados/trazabilidad_versiones.txt.')

# ============================================================ §4.6 y §5.2.2
k.reemplazo('que difieren en composición de intenciones, en longitud de los mensajes y en momento de ejecución, y los '
            'tres factores inciden sobre el tiempo de inferencia.',
            'que difieren en composición de intenciones, en longitud de los mensajes, en momento de ejecución y en el '
            'prompt con que corrieron: las de Telegram, con el prompt reducido de 1032 caracteres (Sección 4.4.3). Los '
            'tres primeros factores inciden sobre el tiempo de inferencia; el cuarto apenas, porque en el diseño '
            'factorial prompts de 1154 y de 6338 caracteres produjeron tiempos medios de 1,55 s y 1,57 s (Sección 5.2.4).')
k.reemplazo('—superior al del canal simulado (1,47 s) por la latencia de red real, pero holgadamente por debajo del '
            'umbral de 10 s—, lo que confirma que H2a se sostiene también sobre un canal en producción.',
            '—superior al del canal simulado (1,47 s), diferencia que no se atribuye a la red porque las dos series no '
            'son apareadas (Sección 4.6), pero holgadamente por debajo del umbral de 10 s—, de modo que H2a se sostiene '
            'también sobre un canal real.')
k.reemplazo('incompatible con la métrica de segundos.',
            'incompatible con la métrica de segundos. Las interacciones de Telegram, además, corrieron con el prompt '
            'reducido de 1032 caracteres y no con el de la configuración principal (Sección 4.4.3): la validación del '
            'segundo canal cubre la latencia y el recorrido completo del flujo, no el desempeño de la configuración '
            'medida sobre el corpus.')

# ============================================================ §5.2.4
k.reescribir('5.2.4 Ablación: cuánto aporta la base de conocimiento',
             '5.2.4 Aporte de la base de conocimiento y de las reglas y ejemplos')
k.reescribir('El 92,7 % de la sección anterior se obtuvo con un prompt que inyecta',
    'El 92,7 % de la sección anterior se obtuvo con un prompt que combina la base de conocimiento de la tienda con '
    'reglas de decisión y siete ejemplos etiquetados. Para estimar cuánto aporta cada uno se ejecutó el diseño '
    'factorial de la Sección 3.5.6: cuatro condiciones, tres repeticiones de cada una, sobre el mismo corpus y las '
    'mismas etiquetas de referencia. Los doce bloques resultaron válidos. La exactitud por clase y por condición se '
    'sintetiza en la Tabla 5.10.')
k.reescribir('Tabla 5.10: Exactitud de clasificación por clase, con y sin base de conocimiento.',
             'Tabla 5.10: Exactitud por mayoría de tres repeticiones, por clase y por condición del diseño factorial.')
t510 = k.tabla(['Clase', 'n', 'Con base de conocimiento y ejemplos'])
nuevas = [
    ['Clase (mensajes)', 'C1 · base, reglas y ejemplos', 'C2 · reglas y ejemplos, sin base',
     'C3 · base, sin reglas ni ejemplos', 'C4 · sin base, reglas ni ejemplos'],
    ['FAQ (48)', '45 (93,8 %)', '45 (93,8 %)', '31 (64,6 %)', '19 (39,6 %)'],
    ['ESTADO_PEDIDO (35)', '32 (91,4 %)', '32 (91,4 %)', '31 (88,6 %)', '34 (97,1 %)'],
    ['RECLAMO (42)', '38 (90,5 %)', '39 (92,9 %)', '31 (73,8 %)', '33 (78,6 %)'],
    ['GENERAL (25)', '25 (100 %)', '25 (100 %)', '25 (100 %)', '25 (100 %)'],
    ['Total (150) · IC 95 %', '140 (93,3 %) [88,2 %; 96,3 %]', '141 (94,0 %) [89,0 %; 96,8 %]',
     '118 (78,7 %) [71,4 %; 84,5 %]', '111 (74,0 %) [66,4 %; 80,4 %]'],
]
for c in range(1, 5):
    assert sum(int(nuevas[r][c].split()[0]) for r in range(1, 5)) == int(nuevas[5][c].split()[0]), 'no suma la columna %d' % c
assert len(t510.rows) == 6 and len(t510.columns) == 5
for r, vals in enumerate(nuevas):
    for c, v in enumerate(vals):
        k.celda(t510, r, c, v)
lst = k.tabla(['Tabla', 'Descripción', 'Sección'])
k.celda(lst, k.fila(lst, 'Tabla 5.10'), 1,
        'Exactitud por mayoría de tres repeticiones, por clase y por condición del diseño factorial')

k.reescribir('La exactitud global cae de 92,7 % a 86,0 %',
    'La exactitud por mayoría es de 93,3 % con base, reglas y ejemplos (C1) y de 94,0 % sin la base (C2), y cae a '
    '78,7 % sin las reglas ni los ejemplos (C3) y a 74,0 % sin ninguno de los dos factores (C4). La variabilidad entre '
    'repeticiones es baja: las exactitudes de cada repetición tienen un desvío de 0,4 puntos en C1 y en C2, de 1,3 en '
    'C3 y de 0,7 en C4, y los mensajes que recibieron la misma etiqueta en las tres repeticiones son el 98,0 %, el '
    '98,7 %, el 85,3 % y el 92,0 %, respectivamente. De los seis contrastes por pares, cuatro son significativos tras '
    'el ajuste de Holm, todos con p < 0,001: los que enfrentan una condición con reglas y ejemplos a una sin ellos. Los '
    'otros dos no lo son: C1 frente a C2, con una sola discordancia (p = 1,0), y C3 frente a C4, con 18 y 11 '
    'discordancias (p ajustado = 0,53). El tiempo medio de respuesta apenas varía entre condiciones, de 1,53 s a '
    '1,60 s, aunque el prompt va de 1154 a 6338 caracteres.')
k.reescribir('El desglose por clase es más informativo que el total',
    'En términos del diseño factorial, las reglas y los ejemplos aportan 17,3 puntos porcentuales en promedio: 14,7 con '
    'la base presente y 20,0 sin ella. La base de conocimiento aporta 2,0 puntos en promedio: −0,7 cuando las reglas y '
    'los ejemplos están presentes y +4,7 cuando faltan, y ninguna de las dos diferencias es significativa. La '
    'interacción, de −5,3 puntos, indica que la base solo ayuda algo cuando faltan las reglas y los ejemplos, y que con '
    'ellos presentes no agrega nada a la clasificación. El desglose de la Tabla 5.10 localiza el efecto. La '
    'exhaustividad de FAQ es de 93,8 % en C1 y en C2, y cae a 64,6 % en C3 y a 39,6 % en C4. Los mensajes de FAQ que se '
    'pierden migran a la categoría residual: por repetición, en promedio, 1,3 y 1,0 mensajes de FAQ se clasifican como '
    'GENERAL en C1 y en C2, frente a 17,3 en C3 y 26,3 en C4. RECLAMO sigue el mismo patrón con menor magnitud, y '
    'ESTADO_PEDIDO y GENERAL apenas varían.')
k.reescribir('La interpretación es la siguiente. La categoría FAQ no se define',
    'Este resultado corrige la interpretación que el trabajo había extraído de la ablación E7. La categoría FAQ no se '
    'vuelve decidible porque el modelo conozca la política de la tienda, sino porque tiene una definición operativa: '
    'las reglas de clasificación enumeran los temas que cuentan como consulta frecuente —pagos, envíos, devoluciones, '
    'garantía, facturación— y los ejemplos muestran casos resueltos. Sin esa definición, el modelo deriva a la '
    'categoría residual las consultas que no reconoce como frecuentes, y la base de conocimiento, por sí sola, recupera '
    'solo una parte de ellas. Los 6,7 puntos que E7 atribuyó a la base corresponden en realidad, sobre todo, a los '
    'bloques que aquel prompt quitaba junto con ella. El diseño no separa cuál de los tres bloques del factor R '
    'produce el efecto; la enumeración de temas de las reglas de clasificación es la explicación más directa, pero '
    'queda como hipótesis. Para la clasificación, lo que la tienda tiene que escribir y mantener son las reglas y los '
    'ejemplos. La base conserva su función en la redacción de las respuestas a las consultas frecuentes, que es la que '
    'evalúa la Sección 5.2.5 y no la que mide este experimento.')
k.reescribir('Corresponde una precisión sobre H2b, porque las dos condiciones',
    'Una observación posterior al diseño se consigna sin valor confirmatorio. El prompt reducido de E7, que tampoco '
    'tenía base, reglas ni ejemplos, obtuvo 86,0 % en una única corrida, doce puntos más que C4. Ambos prompts difieren '
    'esencialmente en el bloque que presenta el mensaje del cliente con su nombre y su canal, que E7 no tenía y C4 sí. '
    'Si la diferencia se sostuviera, la forma de presentar el mensaje también incidiría en la clasificación. El '
    'experimento no fue diseñado para establecerlo, las dos mediciones distan cuatro días y E7 es una sola corrida, de '
    'modo que queda como hipótesis por verificar.')
k.reescribir('Los datos crudos de esta corrida',
    'Sobre H2b el resultado es inequívoco con la regla fijada en la Sección 1.4.2. En la configuración vigente (C1) la '
    'exactitud por mayoría es de 93,3 %, con un intervalo de Wilson de [88,2 %; 96,3 %] cuyo límite inferior supera el '
    '85 %. La réplica frente a la corrida del 12 de agosto no muestra diferencia: 92,7 % frente a 93,3 %, con un '
    'mensaje que solo acertó aquella corrida y dos que solo acertó C1 (p exacto = 1,0). El resultado de la Sección '
    '5.2.3 se reproduce, por lo tanto, un mes después y con tres repeticiones. C2 también cumpliría la regla, con un '
    'límite inferior de 89,0 %; C3 y C4 no, con 71,4 % y 66,4 %. Excluir el único mensaje del corpus muy parecido a un '
    'ejemplo del prompt no cambia ninguna conclusión: la exactitud de C1 y de C2 queda igual, y la de C3 y C4 sube '
    'medio punto.')
p = k.insertar_despues('Sobre H2b el resultado es inequívoco', 'Una observación posterior al diseño',
    'El experimento dejó además un hallazgo de robustez que no buscaba. En la condición sin reglas ni ejemplos, el '
    'modelo devolvió dos veces una categoría que no existe, «CAMBIO» y «DEVOLUCION», ante dos mensajes cuya referencia '
    'es RECLAMO. Esos mensajes siguieron la rama por defecto del flujo: el cliente recibió una respuesta, pero no se '
    'generó ticket, y la restricción de integridad de la tabla de interacciones rechazó la escritura del registro. La '
    'ejecución terminó en error sin que nada lo advirtiera, y el caso solo se detectó porque el guion de verificación '
    'concilia los envíos contra las filas escritas. Con el prompt vigente no ocurrió en 450 clasificaciones, pero el '
    'mecanismo existe: la integridad de la base impide registrar una etiqueta inválida y, a la vez, convierte un error '
    'de clasificación en un reclamo sin ticket y sin registro. Se retoma en las Secciones 5.4.1 y 7.1.')
k.insertar_despues(p, p,
    'Los manifiestos de cada bloque, la evidencia por ejecución, los registros de envío, los cuatro prompts y los '
    'guiones de construcción, ejecución y análisis se versionan en el repositorio bajo experiments/E8. La ablación E7, '
    'que este diseño reemplaza, se conserva bajo experiments/E7.')

# ============================================================ §5.4
k.reescribir('El modelo GPT-4o-mini demostró ser adecuado para la clasificación',
    'El modelo GPT-4o-mini resultó adecuado para la clasificación de intenciones en un dominio acotado de cuatro '
    'categorías. El corpus incluye deliberadamente errores ortográficos, abreviaciones y mensajes con varias preguntas, '
    'pero este trabajo no desagrega la exactitud por esos rasgos y no afirma nada específico sobre ellos. El dato '
    'relevante no es el 92,7 % por sí solo sino lo que el diseño factorial de la Sección 5.2.4 permite atribuir: con '
    'reglas de decisión y ejemplos, la exactitud se ubica entre 93 % y 94 %, con o sin la base de conocimiento; sin '
    'ellos, entre 74 % y 79 %. Los 17,3 puntos del efecto de las reglas y los ejemplos son atribuibles al prompt y no a '
    'la muestra, porque las cuatro condiciones corrieron sobre el mismo corpus y las mismas etiquetas, y la diferencia '
    'se repite en cada una de las tres repeticiones. El 74,0 % de la condición sin base, sin reglas y sin ejemplos es '
    'además una referencia documentada del desempeño alcanzable sin ajuste fino y sin contexto, que es la lectura que '
    'la literatura revisada en la Sección 2.5.2 permite anticipar. El margen que la separa de la configuración vigente '
    'mide lo que una PyME gana por escribir y mantener sus reglas y sus ejemplos, no su base de conocimiento.')

# ============================================================ §6.3 y Tabla 6.1
k.reescribir('Sobre la efectividad de GPT-4o-mini en atención al cliente',
    'Sobre la efectividad de GPT-4o-mini en atención al cliente: el modelo alcanzó una exactitud del 92,7 % en la '
    'clasificación de intenciones sin ajuste fino, y el diseño factorial la reprodujo un mes después en 93,3 % por '
    'mayoría de tres repeticiones. El hallazgo más transferible del trabajo para una PyME no es ese número sino lo que '
    'lo produce. Las reglas de decisión y los ejemplos etiquetados del prompt explican 17,3 puntos de exactitud; la '
    'base de conocimiento de la tienda, 2,0 puntos en promedio y ninguno cuando las reglas y los ejemplos están '
    'presentes. La diferencia se concentra en la categoría FAQ, cuya exhaustividad cae de 93,8 % a 39,6 % cuando faltan '
    'ambas cosas, porque sus mensajes pasan a clasificarse como consulta general. Dicho de otro modo, y esta es la '
    'conclusión práctica: para que el sistema clasifique bien, lo que una PyME tiene que escribir y mantener es la '
    'definición operativa de sus categorías —qué temas cuentan como consulta frecuente y qué casos resueltos lo '
    'ilustran—, no su base de preguntas frecuentes. La base sigue siendo la fuente de las respuestas, y la Sección '
    '5.2.5 muestra que, aun con ella inyectada, el modelo completa datos que la base no contiene. Esta conclusión '
    'corrige la que el trabajo había extraído de la ablación E7, cuyo diseño confundía los dos factores (Sección 3.5.6).')
t61 = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
f = k.fila(t61, 'OE2')
k.celda(t61, f, 2,
    'TMR: 1,47 s en el canal simulado vía SMTP local (n = 150) y 3,07 s en el canal Telegram real (n = 45), este último '
    'con el prompt reducido. Exactitud de clasificación con la configuración vigente del prompt: 92,7 % sobre el corpus '
    'etiquetado (IC 95 %: 87,3 % a 95,9 %) y 93,3 % por mayoría de tres repeticiones en el diseño factorial (IC 95 %: '
    '88,2 % a 96,3 %). Sin reglas ni ejemplos la exactitud cae por debajo del umbral (Sección 5.2.4). Dos canales '
    'implementados y validados; Gmail queda como diseño (§7).')
k.celda(t61, f, 3, 'CUMPLIDO (configuración vigente, dos canales)')

# ============================================================ Anexo D
FAQ = [
    ('¿Cuáles son los métodos de pago?', 'Aceptamos tarjeta de crédito, débito, transferencia bancaria y MercadoPago. Todos los pagos son procesados de forma segura.'),
    ('¿Cuánto tarda el envío?', 'Los envíos dentro de Mendoza tardan 1-3 días hábiles. Para el resto del país, entre 3-7 días hábiles. Te notificamos por email cuando tu pedido sea despachado.'),
    ('¿Cómo puedo devolver un producto?', 'Tenés 30 días desde la recepción para iniciar una devolución. Escribinos indicando tu número de pedido y el motivo, y te guiamos en el proceso.'),
    ('¿Tienen garantía los productos?', 'Todos nuestros productos tienen garantía oficial del fabricante. La duración varía según el producto (generalmente 12 meses). Guardá tu comprobante de compra.'),
    ('¿Cómo contacto a soporte?', 'Podés escribirnos por WhatsApp, Telegram o email. Nuestro sistema de IA te asiste 24/7 y, si es necesario, escala tu caso a un agente humano.'),
    ('¿Hacen factura?', 'Sí, emitimos factura electrónica (AFIP) para todas las compras. La factura se envía automáticamente al email registrado en tu pedido.'),
    ('¿Puedo pagar en cuotas?', 'Sí, con tarjetas de crédito Visa, Mastercard y American Express podés pagar en hasta 12 cuotas sin interés en productos seleccionados. Las cuotas disponibles se muestran en el checkout.'),
    ('¿Es seguro pagar con tarjeta en la web?', 'Totalmente. Usamos encriptación SSL y procesamos los pagos a través de MercadoPago, que cumple con los estándares PCI-DSS. Nunca almacenamos los datos de tu tarjeta.'),
    ('¿Hacen envíos a todo el país?', 'Sí, enviamos a todo el territorio argentino. Trabajamos con OCA, Andreani y correo argentino. El costo de envío se calcula en el checkout según tu código postal.'),
    ('¿Puedo hacer el seguimiento de mi envío?', 'Sí. Una vez despachado tu pedido, te enviamos un email con el número de tracking y el enlace directo para seguir el paquete en tiempo real.'),
    ('¿Hacen envíos internacionales?', 'Por el momento solo enviamos dentro de Argentina. Estamos trabajando para expandir a países limítrofes próximamente.'),
    ('¿Qué pasa si no estoy en casa cuando llega el pedido?', 'El transportista deja un aviso y hace un segundo intento al día siguiente. Si tampoco podés recibirlo, el paquete queda disponible para retiro en la sucursal más cercana por 5 días hábiles.'),
    ('¿Cuál es la política de cambios?', 'Podés cambiar un producto dentro de los 30 días de recibido, siempre que esté en su embalaje original y sin uso. Los gastos de envío del cambio corren por nuestra cuenta si el error fue nuestro.'),
    ('¿Cómo inicio una devolución?', 'Escribinos por este chat o al email devoluciones@techstore.com.ar con tu número de pedido y el motivo. Te enviamos una etiqueta prepaga para el retiro en 24hs hábiles.'),
    ('¿Qué cubre la garantía?', 'La garantía cubre defectos de fabricación. NO cubre daños por mal uso, caídas, líquidos o modificaciones no autorizadas. Ante cualquier falla, contactanos y gestionamos el service con el fabricante.'),
    ('¿Cómo hago válida la garantía?', 'Guardá el comprobante de compra (te lo enviamos por email). Si el producto falla, escribinos con foto o video del problema y tu número de pedido. Nos encargamos de todo el proceso de garantía.'),
    ('¿Los productos son originales?', 'Sí, todos nuestros productos son 100% originales con garantía oficial del fabricante. Somos distribuidores autorizados de todas las marcas que comercializamos.'),
    ('¿Tienen stock en físico para retirar?', 'Por el momento somos una tienda 100% online y no contamos con local a la calle. Todos los pedidos se despachan desde nuestro depósito en Mendoza.'),
    ('¿Cómo sé si un producto tiene stock?', 'Si podés agregarlo al carrito, hay stock disponible. Si aparece como "Sin stock", podés anotarte en la lista de espera y te avisamos cuando vuelva a estar disponible.'),
    ('¿Hacen factura A para empresas?', 'Sí, emitimos factura A para responsables inscriptos. Durante el checkout elegís el tipo de comprobante e ingresás el CUIT y razón social de tu empresa.'),
    ('¿Cuándo recibo la factura?', 'La factura electrónica se genera automáticamente al confirmar el pago y te llega por email en minutos. Si no la recibís, revisá la carpeta de spam o escribinos.'),
    ('¿Puedo cancelar un pedido?', 'Podés cancelar sin costo dentro de las 2 horas de realizado, siempre que no haya sido despachado. Después del despacho, el proceso es una devolución normal.'),
    ('¿Cómo recibo el comprobante de compra?', 'Te enviamos un email de confirmación inmediatamente después del pago con todos los detalles del pedido y la factura adjunta.'),
]
tD = k.tabla(['Categoría', 'Pregunta', 'Respuesta (resumen)'])
assert len(tD.rows) == 24
k.celda(tD, 0, 2, 'Respuesta')
for i, (preg, resp) in enumerate(FAQ, start=1):
    assert tD.rows[i].cells[1].text.strip() == preg, 'fila %d: %r' % (i, tD.rows[i].cells[1].text)
    k.celda(tD, i, 2, resp)
k.reescribir('Se transcribe la base de conocimiento completa: las veintitrés entradas',
    'Se transcribe la base de conocimiento completa: las veintitrés entradas de la tabla faq_responses, con su texto '
    'íntegro, en el orden en que las cargan los guiones init_simple.sql y seed_expand.sql del repositorio. En la '
    'configuración principal este contenido se inyecta en el prompt del modelo (Sección 4.4.3): intervino en las '
    'respuestas medidas en el Capítulo 5, y su aporte a la clasificación es el que dimensiona la Sección 5.2.4. Es '
    'también la referencia contra la que se verifican los datos concretos de las respuestas en la Sección 5.2.5.')

# ============================================================ Anexo H
k.reescribir('Se transcriben los dos prompts de sistema que este trabajo midió',
    'Se transcribe el prompt de sistema de la configuración vigente: el que corrió sobre el corpus el 12 de agosto de '
    '2026 y produjo el 92,7 % de la Sección 5.2.3, y la condición C1 del diseño factorial de la Sección 5.2.4. Tiene '
    '6338 caracteres y ocho bloques, y se transcribe íntegro, sin omisiones. Se publica porque de él depende ese '
    'resultado: sin el prompt, la medición de exactitud no es auditable ni reproducible. El texto empieza con el signo '
    '«=», que el motor de flujos interpreta como marca de expresión y que no se cuenta en su longitud: sin él, las '
    'referencias entre llaves dobles se enviarían como texto literal y la base de conocimiento no se inyectaría.')
fuente = [p for p in d.paragraphs if p.style.name == 'Source Code' and p.text.startswith('Sos un asistente virtual')]
assert len(fuente) == 1
k.reescribir(fuente[0], C1)
k.reescribir('El prompt transcripto arriba es el de la CONDICIÓN DE ABLACIÓN',
    'Las expresiones del bloque MENSAJE DEL CLIENTE se sustituyen en tiempo de ejecución por el canal, el nombre y el '
    'texto del mensaje entrante. La del bloque BASE DE CONOCIMIENTO FAQ se sustituye por las veintitrés entradas de la '
    'tabla faq_responses, en el formato «P: <pregunta>» / «R: <respuesta>», tal como las arma el nodo Preparar '
    'Contexto FAQ; su contenido es el del Anexo D.')
k.reescribir('Los tres primeros bloques —identidad, tarea y formato de salida— son idénticos',
    'Las cuatro condiciones del diseño factorial se arman a partir de este texto quitando bloques enteros, sin '
    'modificar ninguno de los que quedan. C1 es el texto completo. C2 omite el bloque BASE DE CONOCIMIENTO FAQ. C3 omite '
    'REGLAS DE CLASIFICACIÓN, REGLAS CRÍTICAS y EJEMPLOS. C4 omite los cuatro, de modo que conserva la marca de inicio, '
    'IDENTIDAD, TU TAREA, FORMATO DE RESPUESTA y MENSAJE DEL CLIENTE. Sus longitudes son 6338, 6150, 1342 y 1154 '
    'caracteres. Los cuatro textos y su huella md5 se versionan en experiments/E8/prompts y en '
    'experiments/E8/condiciones_e8.json, y el guion condiciones_e8.py los reconstruye desde el commit citado al pie y '
    'aborta si C1 no coincide con el prompt medido. El prompt reducido de la ablación E7, que el diseño factorial '
    'reemplaza (Sección 3.5.6), tenía 1032 caracteres y se transcribe a continuación. Contiene la marca de inicio y los '
    'tres primeros bloques del texto anterior, sin el signo de expresión y sin el bloque del mensaje del cliente: el '
    'texto del mensaje le llegaba al modelo solo como mensaje del usuario. Fue también el prompt del workflow de '
    'dieciocho nodos entre el 25 de agosto y el 15 de septiembre, con el que corrieron las interacciones de Telegram de '
    'la Sección 5.2.2.')
fuente = [p for p in d.paragraphs if p.style.name == 'Source Code' and p.text.startswith('## REGLAS DE CLASIFICACIÓN')]
assert len(fuente) == 1
k.reescribir(fuente[0], E7)
k.reescribir('El texto íntegro de este prompt se encuentra en el nodo IA - Motor Decision',
    'El prompt de la configuración vigente se encuentra en el nodo IA - Motor Decision del archivo workflows/Flujo 2 — '
    'Chatbot Omnicanal IA.json, en el commit f68da9d del repositorio, que coincide byte a byte con la versión del '
    'workflow que corrió el 12 de agosto según el historial del motor de flujos; y en el mismo nodo del archivo '
    'workflows/Flujo 2 — Chatbot WhatsApp + Telegram.json en su versión actual. El commit f297c9e, citado en una '
    'versión anterior de este anexo, guarda el mismo texto sin el signo «=» inicial, con el que la base de conocimiento '
    'no se habría inyectado. El prompt reducido de E7 corresponde al mismo nodo de ese último archivo antes del diseño '
    'factorial, y se conserva en experiments/E8/resultados/workflow_publicado_antes_de_E8.json. Todos son verificables '
    'sin ejecutar el sistema.')

k.guardar()
