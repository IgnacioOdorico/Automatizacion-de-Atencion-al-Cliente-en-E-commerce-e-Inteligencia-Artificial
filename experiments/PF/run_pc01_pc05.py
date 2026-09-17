# -*- coding: utf-8 -*-
"""PC-01 a PC-05 — pruebas funcionales del Flujo 2, con evidencia.

Envía los cinco mensajes de la Tabla 3.5 al webhook del canal simulado del
workflow activo y deja constancia, para cada uno, de lo que la prueba espera
verificar: la respuesta HTTP, cómo terminó la ejecución en n8n, la fila escrita
en interactions (intención, urgencia, pedido asociado, TMR), el ticket creado y
el correo de respuesta capturado por Mailpit.

La Tabla 3.5 citaba el pedido ORD-001, que no existe en la carga inicial; PC-02
usa ORD-HIST-001, un pedido de la carga inicial con estado conocido (delivered).

Las interacciones se registran con el prefijo PC-<fecha>- en user_id, de modo que
no se mezclan con la corrida del corpus ni con el diseño factorial.

Uso (con los contenedores arriba):
    python run_pc01_pc05.py
Salida: resultados/pc01_pc05_<fecha>.txt
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
WEBHOOK = 'http://localhost:5678/webhook/whatsapp-business'
MAILPIT = 'http://localhost:8025/api/v1/messages?limit=50'
WF = 'GyT06kIZgB5Kmw4P'   # Flujo 2 activo: WhatsApp + Telegram
NOMBRE = 'Prueba PC'

PRUEBAS = [
    ('PC-01', '¿Cuáles son los métodos de pago?', 'Respuesta de FAQ + intent=FAQ'),
    ('PC-02', '¿Dónde está mi pedido ORD-HIST-001?', 'Consulta a orders + respuesta con estado'),
    ('PC-03', 'Quiero hacer un reclamo, el producto llegó roto', 'Ticket creado + intent=RECLAMO'),
    ('PC-04', 'URGENTE: el pedido nunca llegó y necesito solución YA',
     'Ticket creado + is_urgent=true + respuesta al cliente por el canal de origen'),
    ('PC-05', '¿Tienen tiendas físicas?', 'Respuesta de IA + intent=GENERAL'),
]


def sql(consulta):
    out = subprocess.run(['docker', 'exec', '-i', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d', 'ecommerce_tesis',
                          '-At', '-F', '\x1f'], input=consulta.encode('utf-8'), capture_output=True)
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    return [f.split('\x1f') for f in out.stdout.decode('utf-8').strip().splitlines() if f]


def correos():
    with urllib.request.urlopen(MAILPIT, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))['messages']


def main():
    sello = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    prefijo = 'PC-%s-' % datetime.now().strftime('%Y%m%d%H%M')
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    lineas = ['PC-01 a PC-05 — %s' % datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ'),
              'commit: %s · workflow %s · prefijo %s' % (commit, WF, prefijo), '']
    for i, (pid, mensaje, esperado) in enumerate(PRUEBAS, 1):
        # el canal simulado entrega la respuesta por SMTP a user_id: tiene que ser una dirección, como en E8
        uid = '%s549261999000%d@whatsapp.sim' % (prefijo, i)
        ultima = sql("SELECT coalesce(max(id),0) FROM execution_entity WHERE \"workflowId\" = '%s';" % WF)[0][0]
        vistos = {m['ID'] for m in correos()}
        cuerpo = json.dumps({'user_id': uid, 'name': NOMBRE, 'message': mensaje}).encode('utf-8')
        req = urllib.request.Request(WEBHOOK, data=cuerpo, headers={'Content-Type': 'application/json; charset=utf-8'})
        with urllib.request.urlopen(req, timeout=90) as r:
            status, resp = r.status, r.read().decode('utf-8', 'replace')
        time.sleep(6)
        ej = sql("SELECT id, status FROM execution_entity WHERE \"workflowId\" = '%s' AND id > %s ORDER BY id;"
                 % (WF, ultima))
        fila = sql("SELECT i.id, i.intent, i.is_urgent, coalesce(o.order_number || ' (' || o.status || ')', '—'), "
                   "round(EXTRACT(epoch FROM i.responded_at - i.received_at)::numeric, 2), replace(i.ai_response, E'\\n', ' ') "
                   "FROM interactions i LEFT JOIN orders o ON o.id = i.order_id "
                   "WHERE i.user_id = '%s' ORDER BY i.id;" % uid)
        # Crear Ticket no completa interaction_id: el ticket se busca por user_id
        ticket = sql("SELECT id, priority, status FROM tickets WHERE user_id = '%s';" % uid)
        nuevos = [m for m in correos() if m['ID'] not in vistos]
        lineas.append('%s · mensaje: %s' % (pid, mensaje))
        lineas.append('  esperado: %s' % esperado)
        lineas.append('  HTTP %d · cuerpo: %s' % (status, resp[:160] or "''"))
        lineas.append('  ejecución n8n: %s' % ('; '.join('%s %s' % tuple(e) for e in ej) or '(ninguna)'))
        if fila:
            iid, intent, urg, pedido, tmr, respuesta = fila[0]
            lineas.append('  interacción %s · intent=%s · is_urgent=%s · pedido asociado: %s · TMR %s s'
                          % (iid, intent, urg, pedido, tmr))
            lineas.append('  respuesta: %s' % respuesta.replace('\n', ' '))
        else:
            lineas.append('  interacción: NO REGISTRADA')
        lineas.append('  ticket: %s' % ('; '.join('id %s, prioridad %s, estado %s' % tuple(t) for t in ticket) or '(ninguno)'))
        lineas.append('  correo de respuesta en Mailpit: %s' % ('; '.join('«%s»' % m.get('Subject', '') for m in nuevos) or '(ninguno)'))
        lineas.append('')
    salida = os.path.join(BASE, 'resultados', 'pc01_pc05_%s.txt' % sello)
    io.open(salida, 'w', encoding='utf-8').write('\n'.join(lineas) + '\n')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('\n'.join(lineas))
    print('guardado en', salida)


def detalle(prefijo):
    """Documenta una corrida ya hecha sin reenviar nada: interacciones con su respuesta completa,
    tickets (se buscan por user_id: Crear Ticket no completa interaction_id) y cuerpo de cada correo."""
    import urllib.request as u
    lineas = ['Detalle de la corrida %s — consultado el %s' % (prefijo, datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')), '']
    inter = sql("SELECT id, user_id, intent, is_urgent, coalesce(order_id::text, '—'), replace(ai_response, E'\\n', ' ') "
                "FROM interactions WHERE user_id LIKE '%s%%' ORDER BY id;" % prefijo)
    tickets = sql("SELECT id, coalesce(interaction_id::text, 'vacío'), user_id, priority, status FROM tickets "
                  "WHERE user_id LIKE '%s%%' ORDER BY id;" % prefijo)
    mensajes = {}
    for m in correos():
        d = json.loads(u.urlopen('http://localhost:8025/api/v1/message/' + m['ID'], timeout=10).read().decode('utf-8'))
        for t in d['To']:
            if t['Address'].startswith(prefijo):
                mensajes[t['Address']] = d['Text']
    for i, (iid, uid, intent, urg, oid, resp) in enumerate(inter, 1):
        lineas.append('PC-0%d · interacción %s · intent=%s · is_urgent=%s · order_id=%s' % (i, iid, intent, urg, oid))
        lineas.append('  respuesta registrada: %s' % resp)
        for t in tickets:
            if t[2] == uid:
                lineas.append('  ticket %s · interaction_id %s · prioridad %s · estado %s' % (t[0], t[1], t[3], t[4]))
        cuerpo = mensajes.get(uid, '(sin correo)').split('\n---\nThis email')[0].strip().replace('\n', ' / ')
        lineas.append('  correo entregado: %s' % cuerpo)
        lineas.append('')
    return lineas


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--detalle':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        print('\n'.join(detalle(sys.argv[2])))
    else:
        main()
