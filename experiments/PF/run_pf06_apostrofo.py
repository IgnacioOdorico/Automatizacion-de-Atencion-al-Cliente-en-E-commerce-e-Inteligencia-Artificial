# -*- coding: utf-8 -*-
"""PF-06 y PC-06 — un apóstrofo en el dato del cliente, antes y después de parametrizar.

Los nodos de base de datos armaban la sentencia insertando el valor recibido dentro
del texto de la consulta (defecto D-9). Un valor legítimo con un apóstrofo —un
apellido O'Brien, un reclamo en inglés con una contracción— rompía la sentencia:
la ejecución terminaba ahí, el cliente no recibía respuesta y no quedaba registro.
`parametrizar_consultas.py` pasó las diez consultas a marcadores de posición.

Esta prueba deja constancia de las dos cosas:

  control  la sentencia anterior, con el mismo valor, no es válida. Se ejecuta el
           texto que n8n producía, dentro de una transacción que se revierte.
  PF-06    Flujo 1: una orden con «Mar O'Brien, S.A.» y un número de orden ya
           registrado. Con la sentencia parametrizada el apóstrofo llega como dato
           y la orden la rechaza la restricción de unicidad —el mismo mecanismo de
           PF-05—, no un error de sintaxis. No escribe ninguna fila: por eso la
           prueba usa un número duplicado y no altera los totales del Capítulo 5.
  PC-06    Flujo 2: un reclamo en inglés con dos contracciones y dos comas, de
           punta a punta. Se verifica que el mensaje quede íntegro en el ticket y
           en la interacción, y que el cliente reciba la respuesta.

Uso (con los contenedores arriba):
    python run_pf06_apostrofo.py
Salida: resultados/pf06_<fecha>.txt
"""
import io
import os
import sys
import json
import time
import subprocess
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
WH_ORDEN = 'http://localhost:5678/webhook/orden-nueva'
WH_CHAT = 'http://localhost:5678/webhook/whatsapp-business'
MAILPIT = 'http://localhost:8025/api/v1/messages?limit=50'
WF1 = 'xICbeLNSWYt89Zxg'   # Flujo 1 activo (15 nodos, con la rama de alerta)
WF2 = 'GyT06kIZgB5Kmw4P'   # Flujo 2 activo (WhatsApp + Telegram)

NOMBRE = "Mar O'Brien, S.A."
ORDEN_DUPLICADA = 'ORD-DEMO-01'
RECLAMO = ("I haven't received my order yet, and it's been two weeks. "
           "I'd like a refund, please.")

# el texto que producía el nodo Registrar Orden antes de parametrizar, con este nombre
VIEJA = """INSERT INTO orders (order_number, customer_name, customer_email, customer_phone,
  product_id, quantity, total_amount, status, received_at, raw_payload)
SELECT
  'ORD-APOS-CONTROL',
  '%s',
  'apostrofo@example.com',
  '5492610000000',
  p.id, 1, p.price * 1, 'pending', NOW(), '{}'::jsonb
FROM products p
WHERE p.sku = 'PROD-001';""" % NOMBRE


def sql(consulta, esperar_error=False):
    out = subprocess.run(['docker', 'exec', '-i', 'tesis_postgres', 'psql', '-U', 'n8n_user',
                          '-d', 'ecommerce_tesis', '-At', '-F', '\x1f'],
                         input=consulta.encode('utf-8'), capture_output=True)
    if esperar_error:
        return out.returncode, out.stderr.decode('utf-8', 'replace').strip()
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    return [f.split('\x1f') for f in out.stdout.decode('utf-8').strip().splitlines() if f]


def correos():
    with urllib.request.urlopen(MAILPIT, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))['messages']


def postear(url, cuerpo):
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode('utf-8'),
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def ultima_ejecucion(wf):
    return sql("SELECT coalesce(max(id),0) FROM execution_entity WHERE \"workflowId\" = '%s';" % wf)[0][0]


def ejecuciones_desde(wf, desde):
    filas = sql("SELECT e.id, e.status, "
                "  (d.data LIKE '%%syntax error%%'), (d.data LIKE '%%duplicate key%%') "
                "FROM execution_entity e JOIN execution_data d ON d.\"executionId\" = e.id "
                "WHERE e.\"workflowId\" = '%s' AND e.id > %s ORDER BY e.id;" % (wf, desde))
    return filas


def main():
    sello = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    L = ['PF-06 y PC-06 — apóstrofo en el dato del cliente · %s'
         % datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ'),
         'commit: %s · Flujo 1 %s · Flujo 2 %s' % (commit, WF1, WF2), '']

    # ------------------------------------------------ control: la sentencia anterior
    codigo, error = sql('BEGIN;\n' + VIEJA + '\nROLLBACK;', esperar_error=True)
    # psql no devuelve código de error por una sentencia fallida: se mira lo que informó
    rechazada = codigo != 0 or error.startswith('ERROR:')
    L += ['control · la sentencia que armaba el nodo antes de parametrizar, con el nombre «%s»' % NOMBRE,
          '  resultado: %s' % ('RECHAZADA por PostgreSQL' if rechazada else 'ACEPTADA (inesperado)'),
          '  %s' % (error.splitlines()[0] if error else ''),
          '  (se ejecutó dentro de una transacción revertida: no escribió nada)', '']

    # ------------------------------------------------ PF-06: Flujo 1
    antes = sql("SELECT COUNT(*) FROM orders;")[0][0]
    ult1 = ultima_ejecucion(WF1)
    status, resp = postear(WH_ORDEN, {'order_number': ORDEN_DUPLICADA, 'customer_name': NOMBRE,
                                      'customer_email': 'apostrofo@example.com',
                                      'customer_phone': '5492610000000',
                                      'product_sku': 'PROD-001', 'quantity': 1})
    time.sleep(6)
    ej1 = ejecuciones_desde(WF1, ult1)
    despues = sql("SELECT COUNT(*) FROM orders;")[0][0]
    L += ['PF-06 · Flujo 1 — orden con «%s» y número ya registrado (%s)' % (NOMBRE, ORDEN_DUPLICADA),
          '  esperado: la sentencia es válida y la rechaza la restricción de unicidad, no la sintaxis',
          '  HTTP %d · cuerpo: %s' % (status, resp[:120] or "''")]
    for eid, est, sintaxis, unicidad in ej1:
        L.append('  ejecución %s · %s · error de sintaxis: %s · violación de unicidad: %s'
                 % (eid, est, 'sí' if sintaxis == 't' else 'no', 'sí' if unicidad == 't' else 'no'))
    L += ['  órdenes en la tabla: %s antes, %s después' % (antes, despues), '']

    # ------------------------------------------------ PC-06: Flujo 2
    uid = 'PF06-%s549261999006@whatsapp.sim' % datetime.now().strftime('%Y%m%d%H%M%S')
    vistos = {m['ID'] for m in correos()}
    ult2 = ultima_ejecucion(WF2)
    status, resp = postear(WH_CHAT, {'user_id': uid, 'name': 'Prueba PF-06', 'message': RECLAMO})
    time.sleep(8)
    ej2 = ejecuciones_desde(WF2, ult2)
    fila = sql("SELECT i.id, i.intent, i.is_urgent, replace(i.message, E'\\n', ' '), "
               "replace(i.ai_response, E'\\n', ' ') FROM interactions i WHERE i.user_id = '%s';" % uid)
    ticket = sql("SELECT id, priority, replace(subject, E'\\n', ' ') FROM tickets WHERE user_id = '%s';" % uid)
    nuevos = [m for m in correos() if m['ID'] not in vistos]
    L += ['PC-06 · Flujo 2 — reclamo en inglés con dos contracciones y dos comas',
          '  mensaje: %s' % RECLAMO,
          '  esperado: se clasifica, se crea el ticket con el texto íntegro y el cliente recibe respuesta',
          '  HTTP %d · cuerpo: %s' % (status, resp[:120] or "''")]
    for e in ej2:
        L.append('  ejecución %s · %s · error de sintaxis: %s' % (e[0], e[1], 'sí' if e[2] == 't' else 'no'))
    if fila:
        iid, intent, urg, mensaje, respuesta = fila[0]
        L += ['  interacción %s · intent=%s · is_urgent=%s' % (iid, intent, urg),
              '  mensaje registrado: %s' % mensaje,
              '  texto íntegro: %s' % ('sí' if mensaje == RECLAMO else 'NO'),
              '  respuesta: %s' % respuesta]
    else:
        L.append('  interacción: NO REGISTRADA')
    for t in ticket:
        L += ['  ticket %s · prioridad %s' % (t[0], t[1]),
              '  asunto registrado: %s' % t[2],
              '  texto íntegro: %s' % ('sí' if t[2] == RECLAMO else 'NO')]
    if not ticket:
        L.append('  ticket: (ninguno)')
    L.append('  correo de respuesta en Mailpit: %s'
             % ('; '.join('«%s»' % m.get('Subject', '') for m in nuevos) or '(ninguno)'))

    salida = os.path.join(BASE, 'resultados', 'pf06_%s.txt' % sello)
    io.open(salida, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('\n'.join(L))
    print('\nguardado en', salida)


if __name__ == '__main__':
    main()
