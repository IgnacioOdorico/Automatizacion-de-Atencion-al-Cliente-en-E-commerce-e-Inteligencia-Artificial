# -*- coding: utf-8 -*-
"""B-02 de la auditoría del 18/09: la versión del workflow sobre la que corrió PF-06.

La cabecera de la evidencia de PF-06 y PC-06 cita el commit b64099b, anterior a que los
workflows parametrizados se versionaran: la prueba corrió contra la instancia ya modificada
unas horas antes del commit 4e748a6. Este guion lee del historial del motor de flujos qué
versión de cada workflow estaba publicada al momento de cada ejecución de la prueba y lo
agrega al archivo de evidencia como nota fechada, sin tocar lo que la prueba registró.
"""
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(BASE, 'resultados', 'pf06_2026-09-17_15-23-44.txt')
EJECUCIONES = {'4085': 'PF-06 · Flujo 1', '4086': 'PC-06 · Flujo 2'}


def sql(q):
    out = subprocess.run(['docker', 'exec', '-i', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d',
                          'ecommerce_tesis', '-At', '-F', '|'], input=q.encode('utf-8'), capture_output=True)
    if out.returncode != 0:
        sys.exit(out.stderr.decode('utf-8', 'replace'))
    return [f.split('|') for f in out.stdout.decode('utf-8').strip().splitlines() if f]


filas = sql("""
SELECT e.id, e."workflowId", e."startedAt",
       (SELECT h."versionId" FROM workflow_history h
         WHERE h."workflowId" = e."workflowId" AND h."createdAt" <= e."startedAt"
         ORDER BY h."createdAt" DESC LIMIT 1),
       (SELECT h."createdAt" FROM workflow_history h
         WHERE h."workflowId" = e."workflowId" AND h."createdAt" <= e."startedAt"
         ORDER BY h."createdAt" DESC LIMIT 1),
       (SELECT (n->'parameters'->'options'->>'queryReplacement' IS NOT NULL)
          FROM workflow_history h CROSS JOIN LATERAL jsonb_array_elements(h.nodes::jsonb) n
         WHERE h."workflowId" = e."workflowId" AND h."createdAt" <= e."startedAt"
           AND n->>'name' IN ('Registrar Orden', 'Crear Ticket')
         ORDER BY h."createdAt" DESC LIMIT 1)
FROM execution_entity e WHERE e.id IN (%s) ORDER BY e.id;""" % ','.join(EJECUCIONES))
assert len(filas) == 2, filas
nota = ['', '---', 'Nota agregada el 18/09/2026 (auditoría de 4.ª instancia, B-02). La cabecera cita el commit',
        'b64099b porque la prueba corrió antes de versionar los workflows parametrizados (commit 4e748a6).',
        'La versión publicada del workflow sobre la que corrió cada ejecución, según el historial del motor:']
for eid, wf, inicio, version, creada, param in filas:
    nota.append('  %s · ejecución %s · workflow %s · versionId %s (publicada %s) · consultas parametrizadas: %s'
                % (EJECUCIONES[eid], eid, wf, version, creada, 'sí' if param == 't' else 'NO'))
texto = io.open(EVID, encoding='utf-8').read()
assert 'Nota agregada el 18/09/2026' not in texto, 'la nota ya está'
io.open(EVID, 'a', encoding='utf-8').write('\n'.join(nota) + '\n')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print('\n'.join(nota))
