# -*- coding: utf-8 -*-
"""E8 — Ejecuciones con error: qué etiqueta devolvió el modelo y por qué no se registró.

Recorre la evidencia de todos los bloques (incluidos los intentos inválidos) y,
para cada ejecución que no terminó en éxito, lee de n8n la copia de datos de esa
ejecución y extrae:
  - el user_id enviado (identifica el mensaje del corpus),
  - la salida del nodo de inferencia (la etiqueta que devolvió el modelo),
  - la causa del error.

Clasifica cada caso como:
  fuera_de_vocabulario  la etiqueta no es FAQ, ESTADO_PEDIDO, RECLAMO ni GENERAL
                        y el INSERT falló por interactions_intent_check;
  otro                  cualquier otra causa (esa sí invalida el bloque).

Escribe resultados/e8_fuera_de_vocabulario.csv. Conviene correrlo apenas
termina cada bloque: n8n poda las ejecuciones viejas.
"""
import sys
import io
import os
import csv
import json
import glob
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
RES = os.path.join(BASE, 'resultados')
CLASES = {'FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL'}


def datos_ejecucion(eid):
    out = subprocess.run(['docker', 'exec', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d', 'ecommerce_tesis',
                          '-At', '-c', 'SELECT data FROM execution_data WHERE "executionId" = %d;' % int(eid)],
                         capture_output=True)
    txt = out.stdout.decode('utf-8', 'replace').strip()
    return json.loads(txt) if txt else None


def main():
    with io.open(os.path.join(RAIZ, 'experiments', 'E2', 'resultados', 'e2_corrida2_clasificaciones.csv'),
                 encoding='utf-8-sig') as f:
        ref = list(csv.DictReader(f))
    id_de_usr = {r['user_id'].strip(): r['id'] for r in ref}
    gt = {r['id']: r['intent_humano'].strip() for r in ref}
    with io.open(os.path.join(RAIZ, 'experiments', 'E2', 'corpus_intents.csv'), encoding='utf-8') as f:
        mensaje = {r['id']: r['mensaje'] for r in csv.DictReader(f)}

    salida = []
    for man in sorted(glob.glob(os.path.join(RES, 'e8_manifiesto_C*_R*.json'))):
        m = json.load(io.open(man, encoding='utf-8-sig'))
        ev_ruta = os.path.join(RES, 'e8_evidencia_%s.csv' % m['bloque'])
        with io.open(ev_ruta, encoding='utf-8-sig') as f:
            ev = list(csv.DictReader(f))
        for e in ev:
            if e['estado'] == 'success':
                continue
            arr = datos_ejecucion(e['execution_id'])
            if arr is None:
                salida.append({'bloque': m['bloque'], 'id': '', 'etiqueta': '', 'execution_id': e['execution_id'],
                               'clase': 'otro', 'referencia': '', 'mensaje': '', 'causa': 'ejecución podada: sin datos'})
                continue
            usuarios = sorted({x for x in arr if isinstance(x, str) and x.startswith(m['prefijo_user_id'])})
            crudo = usuarios[0][len(m['prefijo_user_id']):].replace('@whatsapp.sim', '') if usuarios else ''
            cid = id_de_usr.get(crudo, '')
            etiqueta = ''
            for x in arr:
                if isinstance(x, str) and '"intent"' in x:
                    try:
                        etiqueta = json.loads(x[x.index('{'): x.rindex('}') + 1]).get('intent', '')
                    except Exception:
                        pass
                    break
            restriccion = [x for x in arr if isinstance(x, str) and 'violates check constraint' in x]
            otras = [x for x in arr if isinstance(x, str) and ('violates' in x or 'Error' in x)]
            causa = (restriccion or otras or [''])[0][:160]
            oov = etiqueta not in CLASES and etiqueta != '' and 'interactions_intent_check' in causa
            salida.append({'bloque': m['bloque'], 'id': cid, 'etiqueta': etiqueta, 'execution_id': e['execution_id'],
                           'clase': 'fuera_de_vocabulario' if oov else 'otro', 'referencia': gt.get(cid, ''),
                           'mensaje': mensaje.get(cid, ''), 'causa': causa})
    campos = ['bloque', 'id', 'etiqueta', 'execution_id', 'clase', 'referencia', 'mensaje', 'causa']
    with io.open(os.path.join(RES, 'e8_fuera_de_vocabulario.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, campos)
        w.writeheader()
        w.writerows(salida)
    for s in salida:
        print('%-10s mensaje %-4s «%s» (%s) referencia %s · %s' % (s['bloque'], s['id'], s['etiqueta'], s['clase'],
                                                                   s['referencia'], s['mensaje'][:60]))
    print('%d ejecuciones con error; %d fuera de vocabulario' % (len(salida), sum(s['clase'] == 'fuera_de_vocabulario' for s in salida)))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
