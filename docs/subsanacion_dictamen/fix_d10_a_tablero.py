# -*- coding: utf-8 -*-
"""A-01 de la auditoría del 17/09: el tablero del Flujo 1 y lo que la Figura 7 muestra.

La §4.5 afirmaba que dos paneles no filtran por procedencia y el epígrafe concluía que
el primer punto de la serie diaria correspondía a las órdenes de carga inicial. Las
vistas que estaban aplicadas al capturar eran las de experiments/E5/vistas_measured.sql,
que sí filtran; el panel muestra el recuento de órdenes medidas a esa fecha, y la serie
tiene un solo punto en la ventana visible. Se corrige la §4.5, el epígrafe y el listado,
se transcribe en el Anexo A la definición efectivamente aplicada —que el esquema
versionado incorporó (init_simple.sql)— y se actualiza la recomendación de la §7.2, que
pedía lo que ya está hecho.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)

# ------------------------------------------------------------------ §4.5
k.reescribir(
    'Se configuraron dos dashboards en Grafana',
    'Se configuraron dos dashboards en Grafana con conexión directa a PostgreSQL, uno por cada flujo: '
    '“Pipeline Post-Venta — Overview” (6 paneles) y “Chatbot Multicanal — Métricas” (7 paneles). Los paneles se '
    'alimentan de las vistas de métricas y, en los casos en que se requiere una agregación específica del panel, de '
    'una consulta directa sobre las tablas base. Doce de los trece paneles se restringen a los registros medidos '
    '(data_source = \'measured\'). Siete lo heredan de la vista que consumen: dos del tablero del Flujo 1 —«Órdenes '
    'totales», que consume v_metrics_summary, y «Órdenes procesadas por día», que consume v_daily_order_summary— y '
    'cinco del tablero del Flujo 2, que consumen v_chatbot_corpus, la cual acota además la población a la ventana '
    'temporal de la corrida evaluada. Los otros cinco lo aplican mediante una cláusula explícita en la consulta del '
    'propio panel: los tres indicadores de tiempo y la distribución de estados del Flujo 1, y el de tickets abiertos '
    'del Flujo 2, que repite esa ventana. El panel de exactitud es un valor constante, según indica la Tabla 4.8. '
    'Las figuras de los tableros se capturaron el 19 de agosto de 2026. Las cinco vistas de métricas llevaban '
    'entonces la restricción por procedencia, aplicada sobre la base en uso con el guion '
    'experiments/E5/vistas_measured.sql; esa es la definición que transcribe el Anexo A y la que el esquema '
    'versionado incorporó después, de modo que la separación entre los registros medidos y los de carga inicial es '
    'hoy una propiedad del esquema y no una convención de cada tablero. Ninguna cifra del Capítulo 5 proviene de '
    'esas vistas: las métricas reportadas se calculan con consultas propias sobre las corridas identificadas por su '
    'prefijo de número de orden, según se detalla en la Sección 3.5.1.')

# ------------------------------------------------------------------ Figura 7
CAP = ('Figura 7: Dashboard “Pipeline Post-Venta” en Grafana, alimentado desde las vistas de PostgreSQL con los '
       'datos medidos del Flujo 1, capturado el 19 de agosto de 2026. Sus seis paneles se restringen a los '
       'registros medidos (Sección 4.5). El total de 173 órdenes es el de esa fecha; la Tabla 5.3 informa 174 '
       'porque incorpora ORD-AUDIT-ALERT, generada el 26 de agosto al verificar la alerta de stock bajo. La serie '
       'diaria tiene un único punto dentro de la ventana visible, las 171 órdenes del 10 de agosto: la línea entra '
       'por el borde izquierdo porque interpola desde las dos órdenes de demostración del 2 de julio, anteriores a '
       'esa ventana, de modo que los valores intermedios que la línea dibuja no corresponden a ninguna corrida.')
k.reescribir('Figura 7:', CAP)
DESC7 = CAP[len('Figura 7: '):].split('. Sus seis paneles')[0] + '.'
tablas = [t for t in d.tables if [c.text.strip() for c in t.rows[0].cells][:3] == ['Figura', 'Descripción', 'Sección']]
assert len(tablas) == 2, len(tablas)      # el listado del frontispicio y el del Anexo F
for t in tablas:
    k.celda(t, k.fila(t, 'Figura 7'), 1, DESC7)

# ------------------------------------------------------------------ Anexo A: las vistas aplicadas
p = [x for x in d.paragraphs if 'CREATE OR REPLACE VIEW v_order_processing_time' in x.text]
assert len(p) == 1
texto = p[0].text
CAMBIOS = (
    ("""FROM orders o
WHERE o.processed_at IS NOT NULL;""",
     """FROM orders o
WHERE o.processed_at IS NOT NULL
  AND o.data_source = 'measured';"""),
    ("""                                AS avg_mttr_seg
FROM orders
GROUP BY DATE(received_at)""",
     """                                AS avg_mttr_seg
FROM orders
WHERE data_source = 'measured'
GROUP BY DATE(received_at)"""),
    ("""FROM interactions i
WHERE i.responded_at IS NOT NULL;""",
     """FROM interactions i
WHERE i.responded_at IS NOT NULL
  AND i.data_source = 'measured';"""),
    ("""    COUNT(*) FILTER (WHERE is_urgent)                   AS urgentes
FROM interactions
GROUP BY DATE(received_at)""",
     """    COUNT(*) FILTER (WHERE is_urgent)                   AS urgentes
FROM interactions
WHERE data_source = 'measured'
GROUP BY DATE(received_at)"""),
    ("""    (SELECT COUNT(*) FROM orders)                       AS total_orders,
    (SELECT COUNT(*) FROM orders WHERE status = 'confirmed')
                                                        AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders WHERE processed_at IS NOT NULL)        AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders WHERE notified_at IS NOT NULL)         AS avg_mttr_seg,
    (SELECT COUNT(*) FROM interactions)                 AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions WHERE responded_at IS NOT NULL)  AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets)                      AS total_tickets,
    (SELECT COUNT(*) FROM tickets WHERE status = 'resolved')
                                                        AS tickets_resolved;""",
     """    (SELECT COUNT(*) FROM orders
      WHERE data_source = 'measured')                   AS total_orders,
    (SELECT COUNT(*) FROM orders
      WHERE data_source = 'measured' AND status = 'confirmed')
                                                        AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders
      WHERE data_source = 'measured' AND processed_at IS NOT NULL)
                                                        AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders
      WHERE data_source = 'measured' AND notified_at IS NOT NULL)
                                                        AS avg_mttr_seg,
    (SELECT COUNT(*) FROM interactions
      WHERE data_source = 'measured')                   AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions
      WHERE data_source = 'measured' AND responded_at IS NOT NULL)
                                                        AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets
      WHERE data_source = 'measured')                   AS total_tickets,
    (SELECT COUNT(*) FROM tickets
      WHERE data_source = 'measured' AND status = 'resolved')
                                                        AS tickets_resolved;"""),
    ("""--  VISTAS — MÉTRICAS PARA LA TESIS""",
     """--  VISTAS — MÉTRICAS PARA LA TESIS
--  Las cinco restringen por data_source = 'measured': dejan fuera el seed
--  ('synthetic') y el baseline manual ('e4_manual'). Es la definición con la
--  que se capturaron las figuras (experiments/E5/vistas_measured.sql)."""),
)
for viejo, nuevo in CAMBIOS:
    assert texto.count(viejo) == 1, viejo[:60]
    texto = texto.replace(viejo, nuevo)
k.reescribir(p[0], texto)

# ------------------------------------------------------------------ §3.5.1 y §7.2
k.reemplazo('No todas las vistas de métricas aplican el filtro; la Sección 4.5 detalla qué paneles de los tableros '
            'lo aplican y cuáles no.',
            'Las vistas de métricas aplican el mismo filtro en su definición (Anexo A); la Sección 4.5 detalla cómo '
            'lo aplica cada panel de los tableros.')
k.reescribir(
    'Homogeneizar el filtro de procedencia en las vistas de métricas:',
    'Extender el filtro de procedencia a lo que no lo tiene: las cinco vistas de métricas restringen por '
    'data_source (Anexo A), pero la separación entre lo medido y lo precargado depende todavía de que cada corrida '
    'escriba el valor correcto y de que las consultas que no usan las vistas repitan la cláusula. Una tabla de '
    'corridas, con su identificador propio y su ventana temporal, y una clave foránea desde cada registro a esa '
    'tabla, harían del aislamiento de cada experimento una propiedad del esquema y permitirían reconstruir '
    'cualquier corrida sin depender de prefijos en el número de orden ni de rangos de identificadores.')

k.guardar()
