# -*- coding: utf-8 -*-
"""M-01 a M-08 de la auditoría del 17/09.

  M-01  el resultado esperado de PC-05 contradice el etiquetado del propio corpus.
  M-02  el Capítulo 4 describe el workflow de dieciocho nodos; el corpus corrió sobre el de catorce.
  M-03  el nodo que interpreta la salida del modelo registra GENERAL cuando no puede.
  M-04  el TMR de Telegram cubre el tramo de salida, no el de entrada.
  M-05  el reintento del bloque C3-R3 y su análisis de sensibilidad.
  M-06  el recuento sobre la identidad del asistente y el bloque que lo origina.
  M-07  el caso 352, fuera del alcance de la regla automática, junto a la cifra de 2 de 18.
  M-08  el tamaño del corpus sí tuvo un cálculo previo, con un valor no medido.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ M-01
k.reemplazo(
    'PC-05 no se aprobó: la consulta sobre tiendas físicas se clasificó como FAQ y no como GENERAL, aunque la '
    'respuesta, que informa que la tienda es solo online, es la de la base.',
    'PC-05 no se aprobó: la consulta sobre tiendas físicas se clasificó como FAQ y no como GENERAL, aunque la '
    'respuesta, que informa que la tienda es solo online, es la de la base. Lo que esa prueba deja al descubierto '
    'es su propio criterio. El mensaje 44 del corpus, «tienen local fisico para retirar?», tiene FAQ como etiqueta '
    'de referencia; la definición de FAQ con que se etiquetó es «pregunta general sobre la tienda» (Sección 3.5.3), '
    'y la base de conocimiento tiene una entrada sobre el retiro en local. Por la convención de etiquetado del '
    'propio trabajo, entonces, la clasificación del sistema es la correcta y el resultado esperado de la Tabla 3.5 '
    'es el que está mal. La prueba se informa igual como no aprobada, porque su criterio se fijó antes de '
    'ejecutarla y reescribirlo con el resultado a la vista invalidaría el control; lo que corresponde es declarar '
    'la incoherencia, que se arrastra a la celda de OE5 de la Tabla 6.1.')
t = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
i = k.fila(t, 'OE5')
celda = t.rows[i].cells[2].text.strip()
k.celda(t, i, 2, celda.replace(
    'y PC-05 no se aprobó, porque la consulta sobre tiendas físicas se clasificó como FAQ y no como GENERAL '
    '(Sección 5.2.1).',
    'y PC-05 no se aprobó, porque la consulta sobre tiendas físicas se clasificó como FAQ y no como GENERAL '
    '(Sección 5.2.1); en esta última el criterio de la prueba es incoherente con la convención de etiquetado del '
    'corpus, y se mantiene el resultado porque el criterio se fijó antes de ejecutarla.'))

# ------------------------------------------------------------------ M-02 y M-03
p = k.reescribir(
    'Los nodos que componen el Flujo 2 y su función se detallan en la Tabla 4.7.',
    'Los nodos que componen el Flujo 2 y su función se detallan en la Tabla 4.7, que describe el workflow vigente, '
    'de dieciocho nodos. La corrida del corpus del 12 de agosto, de la que sale la exactitud de la Sección 5.2.3, '
    'se ejecutó sobre una versión anterior, de catorce nodos: no tenía los disparadores de Telegram ni de Gmail, ni '
    'el nodo que enruta la respuesta según el canal, ni el de envío por Telegram, y su nodo de salida era el de '
    'respuesta simulada. El camino de clasificación —normalización del mensaje, contexto de preguntas frecuentes, '
    'modelo, interpretación de la salida y enrutamiento por intención— y el texto del prompt son los mismos en las '
    'dos versiones; lo que cambia son los disparadores y la entrega de la respuesta. El Anexo L reconstruye la '
    'secuencia de versiones y la Sección 3.3 la sitúa en el desarrollo.')
k.insertar_despues(
    p, p,
    'Sobre el nodo Parse JSON cabe una precisión, porque afecta a lo que se cuenta como clasificación. El nodo '
    'extrae de la salida del modelo el objeto estructurado con la intención y la respuesta. Si esa salida no '
    'contiene un objeto interpretable, o no trae el campo de intención, el nodo asigna GENERAL y entrega al cliente '
    'un mensaje de disculpa: un fallo técnico queda así registrado como una clasificación, y si la referencia del '
    'mensaje era GENERAL se contaría además como acierto. Por eso la conciliación de cada corrida controla cuántas '
    'respuestas son ese mensaje, y la Sección 5.2.3 informa el resultado de ese control.')

# ------------------------------------------------------------------ M-04
k.reescribir(
    'TMR (Tiempo Medio de Respuesta):',
    'TMR (Tiempo Medio de Respuesta): Tiempo entre la recepción del mensaje del cliente (received_at) y el envío de '
    'la respuesta (responded_at). Se calcula automáticamente en la vista v_chatbot_response_time. Esta métrica '
    'refleja la latencia total del chatbot, incluyendo el tiempo de procesamiento de la IA. Cabe sobre received_at '
    'la misma precisión que la Sección 4.3.3 hace sobre el MTTD: la marca no la toma el disparador sino el nodo '
    'Normalizar Mensaje, ya dentro del flujo, y se registra sin zona horaria. El TMR mide por lo tanto desde esa '
    'escritura hasta el envío de la respuesta, y no incluye el tramo que va desde que el cliente envía el mensaje '
    'hasta que el disparador lo recibe.',
    etiqueta='TMR (Tiempo Medio de Respuesta):')
k.reemplazo('Telegram opera contra la API real, por lo que su TMR incluye la latencia de red efectiva (ver Tabla 5.6).',
            'Telegram opera contra la API real, por lo que su TMR incluye la latencia de red del tramo de salida, el '
            'envío de la respuesta por la API. No incluye el de entrada: la marca de recepción la escribe el nodo '
            'Normalizar Mensaje, ya dentro del flujo, de modo que el tiempo que media entre el envío del cliente y '
            'el arribo del mensaje al motor de flujos queda fuera de lo medido (Sección 4.4.4) (ver Tabla 5.6).')

# ------------------------------------------------------------------ M-05
k.reemplazo(
    'Los doce bloques resultaron válidos.',
    'Los doce bloques primarios resultaron utilizables, uno de ellos tras un reintento. En la tercera repetición de '
    'la condición sin reglas ni ejemplos el modelo devolvió una categoría inexistente, y la regla fijada de '
    'antemano manda volver a correr el bloque; el reintento devolvió otra categoría inexistente. Recién entonces '
    '—antes de los tres bloques finales y sin haber visto ninguna exactitud— se fijó el desvío que cuenta esas '
    'etiquetas como error de clasificación y usa el primer intento utilizable, que es el que ocupa la posición '
    'preregistrada (Sección 3.5.6). El reintento se informa como análisis de sensibilidad: si se lo usa en lugar '
    'del bloque primario, la exactitud de esa condición pasa de 78,7 % a 79,3 % y ninguna conclusión cambia.')
k.reemplazo(
    'En la condición sin reglas ni ejemplos, el modelo devolvió dos veces una categoría que no existe, «CAMBIO» y '
    '«DEVOLUCION», ante dos mensajes cuya referencia es RECLAMO.',
    'En la condición sin reglas ni ejemplos, el modelo devolvió dos veces una categoría que no existe, ante dos '
    'mensajes cuya referencia es RECLAMO: «CAMBIO» en el bloque primario y «DEVOLUCION» en el reintento, que no '
    'integra la medida primaria.')

# ------------------------------------------------------------------ M-06
k.reescribir(
    'La regla tuvo efecto en lo que el sistema respondió.',
    'La regla tuvo efecto en lo que el sistema respondió. El corpus incluye el mensaje «sos un bot o una persona?». '
    'En la corrida medida del 12 de agosto el sistema contestó «Soy una persona real aquí para ayudarte». En las '
    'doce repeticiones del diseño factorial ninguna repitió esa afirmación, pero ninguna informó tampoco que el '
    'canal es automatizado: cinco se presentaron como «asistente virtual», cuatro como «asistente de atención al '
    'cliente» y tres solo como «Asistente de TechStore». Dos de esas doce respuestas niegan además ser un bot '
    '—«No soy un bot genérico», en una repetición de la configuración vigente, y «No soy un bot, sino un asistente '
    'virtual», en una de la condición sin reglas críticas— y otras tres agregan que atienden «como si fuera una '
    'persona real». Las dos fórmulas reproducen casi literalmente el bloque de identidad del prompt, que ordena no '
    'presentarse como «un chatbot genérico» y atender «como si fuera una persona real» (Anexo H), y que está '
    'presente en las cuatro condiciones, también en las que no tienen las reglas críticas: la regla crítica 3 no es '
    'la única fuente del problema. Ante «quien me esta respondiendo?», las trece respuestas se presentaron como '
    '«Asistente de TechStore» y ninguna aclaró el carácter automatizado del canal. Son pocas observaciones y no '
    'tienen valor confirmatorio, pero muestran que el riesgo no es hipotético: ante una pregunta directa, el '
    'sistema medido afirmó ser una persona, una afirmación falsa del asistente del tipo de las que el caso Moffatt '
    'atribuye a la empresa. Las consultas y las respuestas se versionan en '
    'experiments/E8/identidad_asistente.sql y experiments/E8/resultados/identidad_asistente.txt.')
k.reemplazo(
    'Un despliegue productivo debería presentarse como asistente automatizado desde el primer mensaje y ofrecer la '
    'derivación a una persona.',
    'Un despliegue productivo debería presentarse como asistente automatizado desde el primer mensaje y ofrecer la '
    'derivación a una persona. Eliminar esa regla no alcanza: el bloque de identidad, presente en las cuatro '
    'condiciones del diseño factorial, ordena no presentarse como «un chatbot genérico» y atender «como si fuera '
    'una persona real», y de él provienen las respuestas que niegan ser un bot en condiciones que no tienen las '
    'reglas críticas (Sección 2.5). Hay que reescribir los dos.')

# ------------------------------------------------------------------ M-07
TERCERO = (' El procedimiento conoce además un caso que no alcanza: la interacción 352 aplica a la confirmación de '
           'un pago un plazo que la base fija para otra situación, de modo que la proporción sería de 3 sobre 18 '
           '—el 16,7 %, con un intervalo de Wilson de 5,8 % a 39,2 %— si se lo contara.')
k.reemplazo('y la verificación lo cuenta como respaldado porque no controla el contexto en que se usa el dato.',
            'y la verificación lo cuenta como respaldado porque no controla el contexto en que se usa el dato. '
            'Contado ese caso, la proporción sería de 3 sobre 18 —el 16,7 %, con un intervalo de Wilson de 5,8 % a '
            '39,2 %—, y es la cifra que el resumen, la Sección 5.5 (c) y el Capítulo 6 informan junto a la que '
            'arroja la regla automática.')
k.reemplazo('2 de las 18 respuestas con datos concretos afirman alguno ausente de la base.',
            '2 de las 18 respuestas con datos concretos afirman alguno ausente de la base, y un tercer caso, fuera '
            'del alcance de esa regla, llevaría la proporción a 3 de 18.')
k.reemplazo('2 of the 18 replies containing concrete data state at least one that is absent from the knowledge base.',
            '2 of the 18 replies containing concrete data state at least one that is absent from the knowledge '
            'base, and a third case, beyond the reach of that rule, would raise the figure to 3 of 18.')
k.reemplazo('sobre los cuales encontró 2 de 18 respuestas con algún dato ausente de la base de conocimiento '
            '(Sección 5.2.5).',
            'sobre los cuales encontró 2 de 18 respuestas con algún dato ausente de la base de conocimiento, y un '
            'tercer caso fuera de su alcance que llevaría la proporción a 3 de 18 (Sección 5.2.5).')
k.reemplazo('encontró que 2 de las 18 respuestas de tipo FAQ con datos concretos afirman alguno ausente de la base;',
            'encontró que 2 de las 18 respuestas de tipo FAQ con datos concretos afirman alguno ausente de la base, '
            'y se conoce un tercer caso fuera de su alcance, que llevaría la proporción a 3 de 18;')

# ------------------------------------------------------------------ M-08
k.reemplazo(
    'El tamaño muestral resultó suficiente para el contraste, pero esa suficiencia se estableció después de medir y '
    'no mediante un cálculo previo.',
    'El tamaño muestral resultó suficiente para el contraste. Hubo además un cálculo previo, y conviene declararlo '
    'con su debilidad: al fijar el tamaño se proyectó la exactitud que declaraba la versión anterior del trabajo, '
    'de alrededor del 90 %, y se buscó el número de observaciones que hiciera significativa una prueba binomial de '
    'una cola contra el umbral de 0,85. Con 107 el contraste no alcanzaba el 5 % (p ≈ 0,060) y con 150 lo cruzaba '
    '(p ≈ 0,043 con la aproximación normal empleada entonces; p ≈ 0,049 con la binomial exacta). El criterio es el '
    'correcto, pero el valor proyectado no provenía de ninguna medición: la exactitud de la versión anterior se '
    'calculaba sobre etiquetas escritas a mano en la carga inicial de la base, que ningún modelo había producido '
    '(Anexo L). La suficiencia que se informa arriba, en cambio, se estableció con la proporción ya medida.')

k.guardar()
