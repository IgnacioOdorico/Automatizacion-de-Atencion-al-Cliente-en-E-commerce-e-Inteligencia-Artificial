# -*- coding: utf-8 -*-
"""Dictamen del 14/09, obligatorias 8, 9 y 10: conclusiones, factor 780× y concurrencia.

  - Concurrencia (§3.5.2, §4.6.2, §5.1.3, Tabla 5.3, Tabla 6.1, §6.2, §6.4,
    §7.1): la ausencia de sobreventa la sostiene el CHECK (stock >= 0) del
    esquema, no el flujo; las 49 órdenes perdidas son ejecuciones con error
    respondidas con HTTP 200; sesgo de supervivencia; concurrencia efectiva;
    seis rondas en dos ejecuciones del guion.
  - Factor 780× (§5.3, §5.4, §6.1): no es una cota, los sesgos van en
    direcciones opuestas; significación práctica en tiempo absoluto.
  - §5.1.4: coeficiente de variación frente a la correlación con el orden.
  - §5.3 y Tabla 5.11: «se sostiene» en lugar de «confirmada», con alcances.
  - §6.1, §6.3: alcance de la reducción, n8n y código, validez estructural
    frente a semántica, escala de madurez como marco propio (§2.1.1).
  - §5.4.1: sin bis ni ter, y dos limitaciones nuevas.

NO es idempotente: aborta si §5.1.3 ya menciona el CHECK (stock >= 0).
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
if k.pars('La prueba de concurrencia (E1.b) arroja dos resultados que conviene leer juntos'):
    sys.exit('ERROR: este guion ya se aplicó.')

# ============================================================ concurrencia
k.reemplazo('sino verificar la integridad transaccional del sistema bajo concurrencia, condición de diseño crítica',
            'sino verificar que el sistema no produzca sobreventa bajo concurrencia, condición de diseño crítica')
k.reescribir('El segundo ensayo (E1.b) evalúa una propiedad distinta y no trivial',
    'El segundo ensayo (E1.b) evalúa una propiedad distinta y no trivial: que el descuento de stock no produzca '
    'sobreventa bajo concurrencia. Se disparan 20 solicitudes HTTP casi simultáneas contra un producto cuyo stock '
    'inicial se fija deliberadamente en 5 unidades, y el ensayo se repite durante seis rondas, en dos ejecuciones del '
    'guion de tres rondas cada una, totalizando 120 órdenes. El criterio de falla está definido de antemano y es '
    'binario: si en alguna ronda el sistema confirma más de 5 órdenes, existe sobreventa. La segunda ejecución '
    'incorporó al guion el conteo de las órdenes que quedan pendientes y de las ejecuciones terminadas en error.')
k.reescribir('La prueba de concurrencia (E1.b) arroja dos resultados que conviene reportar por separado',
    'La prueba de concurrencia (E1.b) arroja dos resultados que conviene leer juntos, porque el segundo explica el '
    'primero. El primero es que no hubo sobreventa: en las seis rondas, contra un stock inicial de 5 unidades y con 20 '
    'solicitudes disparadas en una ventana de entre 0,4 y 23 milisegundos, el sistema confirmó exactamente 5 órdenes, y '
    'ningún producto quedó con stock negativo. Ese resultado no se debe a que el flujo sea atómico. El Flujo 1 lee el '
    'stock y lo descuenta en dos sentencias separadas, sin bloqueo entre ambas (Tabla 4.5, nodos 3 y 5), de modo que '
    'dos ejecuciones concurrentes pueden leer el mismo stock disponible. Lo que impide la sobreventa es la restricción '
    'CHECK (stock >= 0) del esquema (Anexo A): cuando el descuento dejaría el stock en negativo, la base rechaza la '
    'sentencia.')
p = k.reescribir('El segundo resultado matiza al primero',
    'El segundo resultado es la contracara del primero. De las 120 órdenes, 49 (el 40,8 %) quedaron registradas en '
    'estado pendiente, sin marca de processed_at. Cada una se corresponde con una ejecución del motor de flujos '
    'terminada en error: en la segunda ejecución del guion, el conteo de ejecuciones con error creció en cada ronda '
    'exactamente en la cantidad de órdenes que quedaron pendientes. El orden de llegada es consistente con que sean las '
    'que pasaron la verificación de stock y chocaron contra la restricción al descontarlo: en cada ronda aparecen '
    'después de las cinco confirmadas y antes de las rechazadas por falta de stock. El detalle de cada ejecución ya no '
    'se conserva, de modo que esa causa se presenta como la más probable y no como verificada. Lo que sí está '
    'verificado es la consecuencia: el webhook respondió HTTP 200 a las 120 solicitudes, con el cuerpo vacío en las 49 '
    'fallidas, y ninguna orden pasó a estado de error ni generó aviso. El emisor recibió, por lo tanto, la confirmación '
    'de recepción de pedidos que el sistema nunca procesó ni notificó. Es una pérdida silenciosa, y en un sistema de '
    'órdenes eso constituye una falla de confiabilidad, no una limitación de capacidad.')
k.insertar_despues(p, p,
    'Dos precisiones acotan las demás cifras del ensayo. La primera es que las latencias bajo concurrencia —MTTD de '
    '0,092 s y extremo a extremo de 0,192 s, frente a 0,009 s y 0,063 s en régimen secuencial— se calculan sobre las 71 '
    'órdenes que terminaron y excluyen justamente las que fallaron: tienen un sesgo de supervivencia y no describen el '
    'tiempo de las solicitudes que el sistema no completó. La segunda es que la concurrencia efectiva fue menor que la '
    'nominal: aunque las 20 solicitudes de cada ronda se dispararon en pocos milisegundos, el motor las registró en la '
    'base a lo largo de 84 a 132 milisegundos, de modo que no llegaron las 20 a la vez a la sentencia de descuento. Aun '
    'así, la condición de carrera se manifestó en las seis rondas, que corresponden a dos ejecuciones del guion de tres '
    'rondas cada una. La corrección de fondo —descontar el stock con una sentencia condicionada o con bloqueo, y '
    'registrar como error la orden cuya ejecución falla— se plantea en el Capítulo 7.')
t53 = k.tabla(['Métrica', 'Resultado'])
for rotulo, texto in [
        ('E1.b — Rondas × solicitudes simultáneas', '6 × 20 = 120 órdenes (dos ejecuciones del guion de 3 rondas)'),
        ('E1.b — Productos con stock negativo', '0: la restricción CHECK (stock >= 0) rechaza el descuento que lo produciría'),
        ('E1.b — Órdenes sin procesar bajo concurrencia',
         '49 de 120 (40,8 %): ejecuciones terminadas en error, respondidas con HTTP 200 y sin aviso'),
        ('E1.b — MTTD medio bajo concurrencia', '0,092 s (±0,025 s; máx. 0,157 s), sobre las 71 órdenes procesadas'),
        ('E1.b — MTTR medio bajo concurrencia',
         '0,100 s (derivado: end-to-end − MTTD; el desvío no es derivable de las cifras publicadas), sobre las 71 '
         'órdenes procesadas'),
        ('E1.b — End-to-end medio bajo concurrencia', '0,192 s (±0,024 s; máx. 0,260 s), sobre las 71 órdenes procesadas'),
        ("Total de órdenes con data_source = 'measured'",
         '174 (50 de E1.a, 120 de E1.b, 3 órdenes de verificación —ORD-DEMO-01, ORD-DEMO-02 y ORD-VERIF-D4— y 1 de la '
         'verificación de la alerta de stock bajo, ORD-AUDIT-ALERT)')]:
    k.celda(t53, k.fila(t53, rotulo), 1, texto)
t61 = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
f = k.fila(t61, 'OE1')
assert 'seguro pero no elástico' in t61.rows[f].cells[2].text
k.celda(t61, f, 2,
    'MTTD: 0,009 s / MTTR: 0,054 s / Total: 0,063 s (n = 50, corrida E1.a). 50/50 órdenes procesadas sin errores. Bajo '
    'concurrencia (E1.b, 120 órdenes) no hubo sobreventa, porque la restricción CHECK (stock >= 0) del esquema rechazó '
    'los descuentos que la habrían producido; pero 49 de 120 órdenes (40,8 %) quedaron sin procesar, con respuesta HTTP '
    '200 y sin aviso, lo que constituye una falla de confiabilidad (Sección 5.1.3). El objetivo se da por cumplido en '
    'régimen secuencial y no en régimen concurrente.')
k.reemplazo('bajo concurrencia el pipeline conserva la integridad transaccional pero pierde el 40,8 % de las órdenes',
            'bajo concurrencia la restricción del esquema impide la sobreventa, pero el pipeline pierde sin aviso el '
            '40,8 % de las órdenes')
k.reemplazo('(vi) bajo concurrencia el sistema pierde el 40,8 % de las órdenes sin perder integridad, de modo que las '
            'cifras de desempeño valen para régimen secuencial; y (vii) el Flujo 2 depende de un proveedor externo de '
            'inferencia, lo que introduce a la vez un punto único de falla y la transferencia internacional de datos '
            'analizada en la Sección 2.6.',
            '(vi) bajo concurrencia el sistema pierde sin aviso el 40,8 % de las órdenes —la integridad del stock la '
            'sostiene la restricción del esquema, no el flujo—, de modo que las cifras de desempeño valen para régimen '
            'secuencial; (vii) el Flujo 2 depende de un proveedor externo de inferencia, lo que introduce a la vez un '
            'punto único de falla y la transferencia internacional de datos analizada en la Sección 2.6; (viii) la '
            'exactitud se midió con la temperatura por defecto del proveedor y sobre un alias de modelo que puede '
            'cambiar de versión, y depende de reglas y ejemplos escritos por el mismo equipo que construyó el corpus; y '
            '(ix) ninguno de los dos flujos advierte sus propias fallas: una orden con un producto inexistente, una '
            'orden perdida bajo concurrencia o una etiqueta fuera del vocabulario admitido terminan sin error visible '
            'para el emisor y sin aviso al operador.')
p = k.par('Control de admisión y encolado de solicitudes:')
etq = 'Control de admisión y encolado, descuento de stock sin condición de carrera y registro de las ejecuciones fallidas:'
k.reescribir(p,
    etq + ' la prueba de concurrencia de la Sección 5.1.3 mostró que la ausencia de sobreventa depende de la restricción '
    'del esquema y que el 40,8 % de las órdenes se pierde sin aviso. Un despliegue productivo debería descontar el stock '
    'en una única sentencia condicionada (UPDATE ... WHERE stock >= cantidad) o con bloqueo de fila, derivar a la rama '
    'sin stock la orden cuyo descuento no prospera, marcar como error y notificar toda ejecución que falle, e '
    'interponer una cola de mensajes entre el webhook y el pipeline, de modo que las solicitudes se encolen en lugar de '
    'descartarse, con métricas de profundidad de cola y de reintentos.',
    etiqueta=etq if p.runs[0].bold else None)

# ============================================================ §5.1.4
k.reemplazo('El coeficiente de variación fue del 16,6 %, dispersión baja que indica que el procedimiento se ejecutó de '
            'manera estable a lo largo de la serie.',
            'El coeficiente de variación fue del 16,6 %, una dispersión moderada que no debe leerse como estabilidad: '
            'como se detalla más abajo, los tiempos descienden a lo largo de la serie por efecto de aprendizaje, y '
            'parte de esa dispersión es tendencia y no ruido.')
k.reemplazo('En consecuencia, la media de 49,13 s subestima el tiempo que emplearía un operador no entrenado, y el '
            'baseline debe leerse como un piso y no como un valor central.',
            'En consecuencia, la media de 49,13 s subestima el tiempo que emplearía un operador no entrenado: respecto '
            'de ese operador, el baseline es un piso. Esto no convierte al factor de mejora en una cota, porque el '
            'término automatizado tiene un sesgo en la dirección contraria (Sección 5.4).')

# ============================================================ §5.2.2 y §5.3
k.reemplazo('Este valor confirma H2a (TMR < 10 s) con amplio margen.',
            'Este valor sostiene H2a (TMR < 10 s) con amplio margen, también por categoría: la media más alta es de 1,54 s.')
k.reescribir('Las tres hipótesis fueron confirmadas por los datos experimentales. En particular:',
    'Las tres hipótesis se sostienen con los criterios fijados en la Sección 1.4.2, con alcances que conviene precisar '
    'en cada caso:')
k.reemplazo('• H1 se confirma en sus dos términos.', '• H1 se sostiene en sus dos términos.')
k.reemplazo('La Sección 5.4 precisa por qué el factor debe leerse como una cota superior.',
            'El límite inferior de ese intervalo, 686×, supera holgadamente el orden de magnitud que fija el criterio. '
            'La Sección 5.4 precisa por qué el factor se lee como una diferencia de casi tres órdenes de magnitud bajo '
            'las condiciones declaradas, y no como una cota.')
k.reescribir('• H2a se confirma con amplio margen',
    '• H2a se sostiene con amplio margen: el TMR del corpus (1,47 s) representa el 14,7 % del umbral de 10 s, y ninguna '
    'de las cuatro categorías supera 1,54 s de media (Tabla 5.5); el del canal Telegram real (3,07 s), medido con el '
    'prompt reducido, representa el 30,7 %.')
k.reescribir('• H2b se confirma con un accuracy global',
    '• H2b se sostiene con la regla fijada: la exactitud de 92,7 % (139/150) tiene un intervalo de confianza de Wilson '
    'al 95 % de [87,3 %; 95,9 %], con el límite inferior por encima del umbral del 85 %, y el diseño factorial la '
    'reproduce en 93,3 % por mayoría de tres repeticiones, con un límite inferior de 88,2 %. El procedimiento de '
    'cálculo se detalla en el Anexo J. El resultado vale para la configuración vigente del prompt: sin sus reglas y sus '
    'ejemplos, la exactitud cae a 78,7 % con la base de conocimiento y a 74,0 % sin ella, con límites inferiores por '
    'debajo del umbral (Sección 5.2.4).')
k.reemplazo('Sobre la confirmación de H2b corresponde una precisión metodológica adicional.',
            'Sobre el contraste de H2b cabe una precisión metodológica adicional.')
t511 = k.tabla(['Hipótesis', 'Criterio', 'Resultado obtenido', 'Veredicto'])
assert len(t511.rows) == 4
k.celda(t511, 1, 0, 'H1: Reducción de al menos un orden de magnitud respecto del proceso manual')
k.celda(t511, 1, 1, 'Límite inferior del IC 95 % del factor de reducción ≥ 10×; end-to-end < 30 s como criterio operativo')
k.celda(t511, 1, 3, 'SE SOSTIENE (régimen secuencial)')
k.celda(t511, 2, 0, 'H2a: TMR < 10 s en cada categoría')
k.celda(t511, 2, 1, 'TMR promedio < 10 s en cada una de las cuatro categorías')
k.celda(t511, 2, 2, '1,47 s en total; entre 1,28 s y 1,54 s por categoría (Tabla 5.5)')
k.celda(t511, 2, 3, 'SE SOSTIENE')
k.celda(t511, 3, 0, 'H2b: Exactitud (accuracy) de clasificación ≥ 85 %')
k.celda(t511, 3, 1, 'Límite inferior del IC 95 % de Wilson ≥ 85 %')
k.celda(t511, 3, 2,
    '92,7 % (139/150) en la corrida del corpus, IC 95 % [87,3 %; 95,9 %]; 93,3 % por mayoría de tres repeticiones en el '
    'diseño factorial, IC 95 % [88,2 %; 96,3 %]. En ambos casos el límite inferior supera el umbral. Sin reglas ni '
    'ejemplos: 78,7 % y 74,0 %, con límites inferiores de 71,4 % y 66,4 % (Sección 5.2.4).')
k.celda(t511, 3, 3, 'SE SOSTIENE con la configuración vigente; no se sostiene sin reglas ni ejemplos')

# ============================================================ §5.4 — factor 780×
k.reemplazo('Los resultados confirman la premisa central del trabajo: la automatización reduce de manera sustancial los '
            'tiempos operativos del ciclo post-venta.',
            'Para el procesamiento de órdenes, los resultados sostienen la premisa central del trabajo: la automatización '
            'reduce de manera sustancial el tiempo operativo.')
k.reemplazo('Segundo, el factor debe leerse como una cota superior y no como el valor esperable en un despliegue '
            'productivo: el término automatizado proviene de un entorno de laboratorio en el que la notificación se '
            'entrega a un capturador SMTP alojado en el mismo host, sin tránsito de correo real ni latencia de servicios '
            'de terceros, mientras que el término manual se midió sobre un operador que ya conocía el procedimiento y '
            'trabajaba con una plantilla fija, dos decisiones deliberadamente conservadoras que reducen el numerador.',
            'Segundo, el factor no es una cota en ningún sentido, porque los sesgos conocidos de sus dos términos operan '
            'en direcciones opuestas. El término automatizado proviene de un entorno de laboratorio en el que la '
            'notificación se entrega a un capturador SMTP alojado en el mismo host, sin tránsito de correo real ni '
            'latencia de servicios de terceros: ese sesgo achica el denominador y agranda el factor. El término manual se '
            'midió sobre un operador que ya conocía el procedimiento y trabajaba con una plantilla fija, dos decisiones '
            'deliberadamente conservadoras que achican el numerador y con él el factor; y la correlación negativa entre '
            'el orden de ejecución y el tiempo empleado (Sección 5.1.4) indica que un operador no entrenado tardaría '
            'más. Como no hay forma de establecer cuál de los dos sesgos pesa más, el factor se lee como una diferencia '
            'de casi tres órdenes de magnitud bajo las condiciones declaradas, y no como una cota ni como el valor '
            'esperable en un despliegue productivo.')
k.reemplazo('En atención al cliente, el chatbot responde en 1,47 s en promedio sobre el corpus evaluado',
            'La significación práctica de la reducción se aprecia mejor en tiempo absoluto que en el factor: automatizar '
            'ahorra unos 49 segundos de trabajo por orden, es decir unos 41 minutos cada 50 órdenes, que es el volumen de '
            'la corrida medida. Frente a la latencia de detección de un proceso manual ese ahorro es la parte menor: con '
            'el escenario declarado en la Sección 5.1.4, de una revisión de la bandeja cada quince minutos, la espera '
            'media sería de 7,5 minutos, de modo que para el cliente la ganancia principal estaría en eliminar la espera '
            'y no en acelerar el procesamiento. En atención al cliente, el chatbot responde en 1,47 s en promedio sobre '
            'el corpus evaluado')

# ============================================================ §5.4.1
for viejo, nuevo in [('(d) Ausencia de grupo de control', '(g) Ausencia de grupo de control'),
                     ('(c-bis) Ventana temporal de la corrida', '(f) Ventana temporal de la corrida'),
                     ('(b) Entorno de prueba local:', '(d) Entorno de prueba local:'),
                     ('(a-ter) Corrección del contenido', '(c) Corrección del contenido'),
                     ('(a-bis) Desempeño por subcategoría:', '(b) Desempeño por subcategoría:')]:
    k.reemplazo(viejo, nuevo)
k.reemplazo('La Sección 5.2.4 aporta evidencia de que esa frontera es justamente la más sensible al contenido del prompt.',
            'La Sección 5.2.4 muestra que esa frontera es la más sensible a las reglas y los ejemplos del prompt.')
p = k.par('(c) Tamaño del conjunto de prueba:')
etq = '(e) Tamaño y origen del conjunto de prueba:'
k.reescribir(p,
    etq + ' el conjunto de 150 mensajes cubre los escenarios más comunes pero no la variabilidad completa de un entorno '
    'real. La exactitud del 92,7 % podría variar con mensajes de otro dominio o redactados por clientes reales, y con '
    'reglas y ejemplos escritos por otras personas: el modelo no fue entrenado ni ajustado para este dominio, de modo '
    'que su desempeño depende del prompt y del corpus sobre los que se midió.', etiqueta=etq)
modelo = k.par('(f) Ventana temporal de la corrida')
p = k.insertar_despues('(g) Ausencia de grupo de control', modelo,
    '(h) Pérdida silenciosa de interacciones: cuando el modelo devuelve una categoría fuera del vocabulario admitido, '
    'el mensaje sigue la rama por defecto del flujo, el cliente recibe una respuesta sin que se genere ticket y la '
    'restricción de integridad de la tabla de interacciones rechaza el registro, sin que nada lo advierta. No ocurrió '
    'con el prompt vigente en 450 clasificaciones, pero sí dos veces sin reglas ni ejemplos (Sección 5.2.4). El mismo '
    'patrón aparece en el Flujo 1: las órdenes perdidas bajo concurrencia y las rechazadas por un producto inexistente o '
    'un número de orden duplicado reciben HTTP 200 sin cuerpo (Secciones 5.1.1 y 5.1.3).',
    etiqueta='(h) Pérdida silenciosa de interacciones:')
k.insertar_despues(p, modelo,
    '(i) Variabilidad y versión del modelo: la temperatura no se fijó, de modo que rige el valor por defecto de la API, '
    'que es 1, y el modelo se invoca por un alias que el proveedor puede asociar a otra versión. El diseño factorial '
    'acota la primera fuente de variación —la exactitud de la configuración vigente varió entre 92,7 % y 93,3 % en tres '
    'repeticiones— pero no la segunda: una réplica futura podría correr sobre otra versión del modelo sin que el sistema '
    'lo registre.',
    etiqueta='(i) Variabilidad y versión del modelo:')

# ============================================================ §6.1
k.reescribir('Los resultados demuestran que la automatización reduce los tiempos de forma sustancial',
    'Para el procesamiento de órdenes, los resultados muestran una reducción sustancial: el costo marginal de procesar '
    'una orden en el pipeline (0,063 s end-to-end; n = 50) es aproximadamente 780 veces menor que el del procesamiento '
    'manual, cronometrado en 49,13 s por orden sobre diez órdenes (Sección 3.5.5) y validado de forma independiente '
    'contra las marcas temporales de la base, que arrojan 51,28 s para la misma magnitud. La Sección 5.4 explica por '
    'qué ese factor se lee como una diferencia de casi tres órdenes de magnitud bajo las condiciones del laboratorio y '
    'no como una cota: los sesgos conocidos de sus dos términos operan en direcciones opuestas. La reducción vale en '
    'régimen secuencial; bajo concurrencia, el 40,8 % de las órdenes se perdió sin aviso (Sección 5.1.3). La atención '
    'conversacional no se compara contra un proceso manual, porque no se midió uno: el chatbot respondió en 1,47 s en '
    'promedio sobre el corpus evaluado y clasificó con una exactitud del 92,7 %, que el diseño factorial atribuye a las '
    'reglas y los ejemplos del prompt. La disponibilidad ininterrumpida es una propiedad esperable de la arquitectura '
    '—el sistema no depende de un operador humano para responder— pero no fue medida: no se ejecutó ensayo de '
    'disponibilidad ni se observó el servicio durante una ventana prolongada, de modo que no se la reporta como '
    'resultado. Las tres hipótesis de trabajo se sostienen con los criterios fijados, con los alcances que precisa la '
    'Sección 5.3: H1 en régimen secuencial y como comparación de costos marginales, H2a en los dos canales medidos, y '
    'H2b con la configuración vigente del prompt y no sin sus reglas y ejemplos.')

# ============================================================ §6.3
k.reemplazo('permitió implementar ambos flujos sin escribir código de aplicación. Esto reduce la barrera técnica de '
            'adopción para empresas sin equipos de desarrollo dedicados.',
            'permitió implementar ambos flujos con una cantidad acotada de código: la orquestación se definió '
            'visualmente, pero el Flujo 2 requiere cinco nodos Function con JavaScript, y los dos flujos incluyen '
            'sentencias SQL escritas a mano en sus nodos de base de datos. Que esto reduzca la barrera técnica de '
            'adopción para empresas sin equipos de desarrollo dedicados es plausible, pero no fue medido: el trabajo no '
            'evaluó la puesta en marcha ni el mantenimiento por parte de personal no técnico. La plataforma, además, no '
            'protege por sí sola de las fallas silenciosas: la pérdida de órdenes bajo concurrencia (Sección 5.1.3) y la '
            'de registros ante una etiqueta inválida (Sección 5.2.4) ocurrieron sin que el motor de flujos las '
            'advirtiera, y detectarlas exigió instrumentación propia.')
# el bloque A dejó entero en negrita el párrafo «Sobre la efectividad…»: la negrita vuelve a la etiqueta
etq = 'Sobre la efectividad de GPT-4o-mini en atención al cliente:'
p = k.par(etq)
assert p.runs[0].bold and p.runs[0].text.startswith(etq) and len(p.runs[0].text) > 200
k.reescribir(p, p.text, etiqueta=etq)
k.reescribir('Sobre las métricas MTTD/MTTR/TMR:',
    'Sobre las métricas MTTD, MTTR y TMR: su adaptación del dominio ITIL al ciclo post-venta de e-commerce tiene validez '
    'estructural pero no semántica, y conviene separar ambas cosas. Es estructuralmente válida porque cada métrica se '
    'operacionaliza como la diferencia entre dos marcas temporales observables, registradas automáticamente en '
    'PostgreSQL, que permiten calcularla y visualizarla sin intervención manual. No lo es semánticamente, porque el '
    'nombre promete más que el instrumento: como se discute a continuación, un MTTD de 0,009 segundos no mide la '
    'detección de nada.', etiqueta='Sobre las métricas MTTD, MTTR y TMR:')
k.reemplazo('La primera es la escala de madurez de proceso de van der Aalst (2016), donde la automatización es un nivel '
            'intermedio entre la documentación y la gobernanza:',
            'La primera es la escala de madurez de proceso que la Sección 2.1.1 propone como marco analítico propio, en '
            'la que la automatización es un nivel intermedio entre la documentación y la gobernanza:')
k.reemplazo('En la literatura de gestión de procesos (Business Process Management, BPM), la automatización constituye uno '
            'de los cuatro niveles de madurez de proceso, junto con la documentación, la optimización y la gobernanza '
            '(van der Aalst, 2016).',
            'Para situar lo que un sistema de automatización alcanza, este trabajo ordena la madurez de un proceso en '
            'cuatro niveles: documentación, automatización, optimización y gobernanza. La escala es un marco analítico '
            'propio, que el Capítulo 6 usa para ordenar la discusión, y no una clasificación tomada de la literatura de '
            'gestión de procesos (Business Process Management, BPM).')
k.eliminar('van der Aalst, W. M. P. (2016).')

k.guardar()
