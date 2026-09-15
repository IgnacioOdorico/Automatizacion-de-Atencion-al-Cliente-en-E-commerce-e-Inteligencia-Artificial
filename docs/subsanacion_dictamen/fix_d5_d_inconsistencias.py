# -*- coding: utf-8 -*-
"""Dictamen del 14/09, obligatoria 11 (cuadro de inconsistencias) y parte de la 5.

  - §4.5: cinco paneles del Flujo 2 heredan de la vista; el de tickets filtra
    con una cláusula propia. §4.6.2: no todas las vistas filtran.
  - Tabla 3.3: «tasa de no escalada», como en §5.2.2.
  - §2.1.3: el MTTR llega hasta el despacho de la notificación (§4.3.3).
  - §2.5: el criterio de inclusión declara la excepción de los preprints.
  - Figura 8: sus cinco órdenes no están en el total de la Tabla 5.3.
  - §5.1.1 y Tabla 5.1: sin «eventos»; PF-04 y PF-05 con la evidencia de
    experiments/PF y el mecanismo real (HTTP 200 sin cuerpo). Tabla 6.1, OE5.
  - Identificadores: PF-01 a PF-05 y PC-01 a PC-05 (C1 a C5 chocaban con las
    condiciones del diseño factorial); sin low_stock_alert.
  - §2.3.2: sin «varios órdenes de magnitud respecto al estándar manual».
  - Anexo E: remite a los guiones versionados de E1 y aclara el stock de
    PROD-005; §4.6.2 también lo aclara.

NO es idempotente: aborta si la Tabla 4.9 ya usa PF-01.
Se ejecuta desde la raíz del repositorio.
"""
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit  # noqa: E402

d = abrir()
k = Kit(d)
pruebas = [t for t in d.tables if [c.text.strip() for c in t.rows[0].cells] == ['#', 'Prueba', 'Entrada', 'Resultado esperado']]
assert len(pruebas) == 2, 'se esperaban las Tablas 4.9 y 4.10'
t49 = [t for t in pruebas if t.rows[1].cells[0].text.strip() in ('F1', 'PF-01')]
t410 = [t for t in pruebas if t.rows[1].cells[0].text.strip() in ('C1', 'PC-01')]
assert len(t49) == 1 and len(t410) == 1
t49, t410 = t49[0], t410[0]
if t49.rows[1].cells[0].text.strip() == 'PF-01':
    sys.exit('ERROR: este guion ya se aplicó.')

# ============================================================ §4.5 y §4.6.2
k.reemplazo('y seis del tablero del Flujo 2 lo heredan de la vista v_chatbot_corpus, que además acota la población a la '
            'ventana temporal de la corrida evaluada.',
            'y seis del tablero del Flujo 2: cinco lo heredan de la vista v_chatbot_corpus, que además acota la población '
            'a la ventana temporal de la corrida evaluada, y el de tickets abiertos aplica una cláusula propia sobre la '
            'misma ventana.')
t48 = k.tabla(['#', 'Panel', 'Tipo', 'Fuente de datos', 'Descripción'])
f = k.fila(t48, '10')
assert t48.rows[f].cells[3].text.strip() == 'tickets'
k.celda(t48, f, 3, 'tickets (filtrada a la ventana de la corrida del corpus)')
k.reemplazo('Las vistas que alimentan los tableros de resultados filtran por ese valor, de modo que ninguna cifra '
            'reportada en el Capítulo 5 mezcla datos medidos con datos sintéticos.',
            'Las cifras del Capítulo 5 se calculan con consultas que filtran por ese valor, de modo que ninguna mezcla '
            'datos medidos con datos sintéticos. No todas las vistas de métricas aplican el filtro; la Sección 4.5 '
            'detalla qué paneles de los tableros lo aplican y cuáles no.')
k.reemplazo('contra un producto cuyo stock inicial se fija deliberadamente en 5 unidades,',
            'contra un producto cuyo stock el guion fija deliberadamente en 5 unidades antes de cada ronda —el catálogo '
            'de la Tabla 4.4 le asigna 4, y el guion lo restaura al terminar—,')

# ============================================================ Tabla 3.3, §2.1.3, §2.3.2, §2.5
t33 = k.tabla(['Dato', 'Fuente', 'Método de recolección'])
f = k.fila(t33, 'Tasa de resolución autónoma')
k.celda(t33, f, 0, 'Tasa de no escalada')
k.celda(t33, f, 2, 'Proporción de interacciones respondidas sin generar un ticket para un operador humano; no mide que '
                   'la respuesta sea correcta (Sección 5.2.2)')
k.reemplazo('hasta que el cliente recibe la notificación de confirmación o rechazo.',
            'hasta que el sistema despacha la notificación de confirmación o rechazo al servidor de correo; no incluye '
            'el tránsito hasta la casilla del cliente (Sección 4.3.3).')
k.reemplazo('Un sistema automatizado con TMR de segundos representa, por tanto, una mejora de varios órdenes de magnitud '
            'respecto al estándar manual.',
            'Un sistema automatizado con un TMR de segundos se ubica, por lo tanto, en el extremo favorable de esa '
            'dimensión. Este trabajo no midió el tiempo de respuesta de una atención manual por chat, de modo que no '
            'cuantifica la mejora respecto de ella.')
k.reemplazo('Se incluyeron trabajos empíricos que reportaran métricas cuantitativas, revisiones sistemáticas y preprints '
            'de laboratorios o conferencias reconocidas; se excluyeron material de divulgación, documentación de producto '
            'y publicaciones sin proceso de revisión.',
            'Se incluyeron trabajos empíricos arbitrados que reportaran métricas cuantitativas y revisiones sistemáticas, '
            'y se excluyeron el material de divulgación y la documentación de producto. Se admitió una excepción '
            'declarada: tres preprints sin revisión por pares —Huang et al. (2023), Luo et al. (2023) y Perez y Ribeiro '
            '(2022)— y la descripción del corpus SNIPS de Coucke et al. (2018), por tratarse de trabajos de referencia en '
            'temas donde la literatura arbitrada es posterior o escasa; la lista de referencias los identifica por su '
            'repositorio. Los reportes de industria y la documentación técnica que se citan en otros capítulos cumplen '
            'una función de contexto o de referencia de herramienta, y no de antecedente.')

# ============================================================ Figura 8 y Tabla 5.3
k.reemplazo('de cincuenta órdenes: confirmaciones de orden y avisos de stock insuficiente, sobre dominios reservados para '
            'documentación (@example.com).',
            'de cincuenta órdenes: confirmaciones de orden y avisos de stock insuficiente, sobre dominios reservados para '
            'documentación (@example.com). Esas cinco órdenes no se conservan en la base '
            'de datos y no integran el total de la Tabla 5.3.')
k.reemplazo('generados por el Flujo 1 durante las pruebas:',
            'generados por el Flujo 1 durante una corrida de verificación de cinco órdenes, distinta de las corridas '
            'medidas:', n=2)

# ============================================================ identificadores y pruebas funcionales
for i in range(1, 6):
    assert t49.rows[i].cells[0].text.strip() == 'F%d' % i
    k.celda(t49, i, 0, 'PF-0%d' % i)
    assert t410.rows[i].cells[0].text.strip() == 'C%d' % i
    k.celda(t410, i, 0, 'PC-0%d' % i)
assert t49.rows[3].cells[3].text.strip() == 'Alerta low_stock_alert registrada'
k.celda(t49, 3, 3, 'Alerta registrada en stock_alerts')
for viejo, nuevo in [('C1, sobre una consulta de tipo frecuente,', 'PC-01, sobre una consulta de tipo frecuente,'),
                     ('C2, sobre estado de pedido,', 'PC-02, sobre estado de pedido,'),
                     ('C3, sobre un reclamo,', 'PC-03, sobre un reclamo,'),
                     ('C4, sobre un reclamo redactado', 'PC-04, sobre un reclamo redactado'),
                     ('C5, sobre una consulta abierta,', 'PC-05, sobre una consulta abierta,')]:
    k.reemplazo(viejo, nuevo)
k.reemplazo('y los artefactos generados (emails, eventos) (ver Tabla 5.1).',
            'y los artefactos generados —correos y alertas de stock— (ver Tabla 5.1).')
t51 = k.tabla(['Prueba', 'Escenario', 'Resultado'])
for fila, texto in [
        ('PF-03', 'PASS — orden confirmada + alerta registrada en stock_alerts'),
        ('PF-04', 'PASS CON RESERVA — la orden no se registra, pero el webhook responde HTTP 200 sin cuerpo y la '
                  'ejecución termina como exitosa: no hay error controlado'),
        ('PF-05', 'PASS CON RESERVA — la restricción de unicidad rechaza la orden duplicada, pero el webhook responde '
                  'HTTP 200 sin cuerpo')]:
    k.celda(t51, k.fila(t51, fila), 2, texto)
k.reescribir('Las cinco pruebas resultaron exitosas (100% de aprobación).',
    'Las tres primeras pruebas se aprobaron sin reservas: el pipeline actualizó las marcas temporales en orders y las '
    'notificaciones se enviaron al destinatario esperado. Las dos pruebas de rechazo cumplen lo esencial —la orden '
    'inválida o duplicada no se registra— pero no el rechazo controlado que fijaba la Tabla 4.9. Se re-ejecutaron el '
    '15 de septiembre para dejar evidencia versionada, que se conserva en experiments/PF junto con el guion, y el '
    'mecanismo de cada una es distinto. En PF-04, la sentencia que registra la orden toma el producto del catálogo por '
    'su SKU; al no encontrarlo no inserta ninguna fila, el flujo se detiene sin llegar a un nodo de respuesta y la '
    'ejecución queda registrada como exitosa. En PF-05, la restricción de unicidad del número de orden rechaza la '
    'inserción y la ejecución termina en error. En los dos casos el webhook responde HTTP 200 con el cuerpo vacío, de '
    'modo que el emisor no puede distinguir un rechazo de una orden atendida: es el mismo patrón que la Sección 5.1.3 '
    'documenta bajo concurrencia.')
t61 = k.tabla(['Obj.', 'Enunciado', 'Resultado', 'Estado'])
f = k.fila(t61, 'OE5')
viejo = t61.rows[f].cells[2].text.strip()
assert viejo.endswith('con datos crudos y manifiesto de ejecución versionados.')
k.celda(t61, f, 2, viejo + ' Las dos pruebas de rechazo del Flujo 1 (PF-04 y PF-05) no registran la orden, como se '
                   'esperaba, pero responden HTTP 200 sin cuerpo en lugar de un error controlado (Sección 5.1.1).')
k.celda(t61, f, 3, 'CUMPLIDO (con dos desvíos documentados)')

# ============================================================ Anexo E
CODIGO = '''# ---------- Levantar el entorno ----------
docker compose up -d
docker compose ps

# ---------- Verificar la base ----------
# El host publica PostgreSQL en 5433 (mapeo 5433:5432) para no colisionar
# con una instalación nativa que ocupe el 5432. Dentro de la red de Docker
# los servicios se ven entre sí como postgres:5432.
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "\\dt"

# ---------- Flujo 1: orden con stock suficiente ----------
curl -X POST http://localhost:5678/webhook/orden-nueva \\
  -H "Content-Type: application/json" \\
  -d '{"order_number":"ORD-TEST-001","customer_name":"Test","customer_email":"test@example.com","customer_phone":"5492615551234","product_sku":"PROD-018","quantity":1}'

# ---------- Flujo 1: rama sin stock ----------
# Se piden más unidades de las disponibles para forzar la rama no_stock.
curl -X POST http://localhost:5678/webhook/orden-nueva \\
  -H "Content-Type: application/json" \\
  -d '{"order_number":"ORD-TEST-002","customer_name":"Test","customer_email":"test@example.com","customer_phone":"5492615551234","product_sku":"PROD-005","quantity":999}'

# ---------- Flujo 2: chatbot ----------
# El path del webhook es whatsapp-business. El nodo normalizador acepta un
# payload plano con los campos from y message.
curl -X POST http://localhost:5678/webhook/whatsapp-business \\
  -H "Content-Type: application/json" \\
  -d '{"from":"5492615551234","message":"¿Cuáles son los métodos de pago?"}'

# ---------- Corridas medidas del Capítulo 5 (PowerShell) ----------
# No se reproducen con fragmentos sueltos: se ejecutan con los guiones
# versionados, que fijan el plan de órdenes por semilla, registran cada
# envío y dejan un manifiesto con el commit y las marcas temporales.
cd experiments\\E1
.\\run_flujo1_carga.ps1          # E1.a: 50 órdenes secuenciales, 2 s entre envíos
.\\run_flujo1_concurrencia.ps1   # E1.b: 20 solicitudes simultáneas por ronda, 3 rondas
.\\run_flujo1_concurrencia.ps1 -Prefijo 'ORD-E1B2'   # segunda ejecución: rondas 4 a 6
# run_flujo1_concurrencia.ps1 fija el stock de PROD-005 en 5 antes de cada
# ronda (el catálogo le asigna 4) y restaura el valor original al terminar.
Get-Content .\\analizar_e1.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis

# Pruebas de rechazo PF-04 y PF-05 (Sección 5.1.1)
cd ..\\PF
.\\run_pf04_pf05.ps1

# ---------- Verificar métricas y la invariante de stock ----------
docker exec -it tesis_postgres psql -U n8n_user -d ecommerce_tesis \\
  -c "SELECT * FROM v_metrics_summary;" \\
  -c "SELECT COUNT(*) AS stock_negativo FROM products WHERE stock < 0;"

# ---------- Ver correos generados ----------
# Abrir http://localhost:8025 en el navegador

# ---------- Ver tableros ----------
# Abrir http://localhost:3000 (usuario admin; contraseña definida en el archivo .env)'''
anexoE = [p for p in d.paragraphs if p.style.name == 'Source Code' and p.text.startswith('# ---------- Levantar el entorno')]
assert len(anexoE) == 1 and 'ORD-CARGA-' in anexoE[0].text
k.reescribir(anexoE[0], CODIGO)

k.guardar()
