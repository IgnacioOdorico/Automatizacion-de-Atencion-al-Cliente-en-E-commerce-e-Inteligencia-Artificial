# -*- coding: utf-8 -*-
"""E8 — Trazabilidad: qué prompt corrió en cada medición anterior del Flujo 2.

Consulta el historial de versiones y de publicaciones que guarda n8n, las
ventanas temporales de cada población de interacciones y, cuando todavía
existen, las copias del workflow que n8n guarda por ejecución. Escribe todo en
resultados/trazabilidad_versiones.txt, que es la evidencia citada por la tesis.

Las marcas received_at se escriben con new Date().toISOString() y la base está
en UTC; las horas de n8n se muestran en UTC para compararlas directamente.
"""
import sys
import io
import os
import json
import hashlib
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
SALIDA = os.path.join(BASE, 'resultados', 'trazabilidad_versiones.txt')
NODO = 'IA - Motor Decision'


def psql(sql):
    out = subprocess.run(['docker', 'exec', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d', 'ecommerce_tesis',
                          '-P', 'pager=off', '-c', sql], capture_output=True)
    return out.stdout.decode('utf-8', 'replace')


def prompt_git(commit, archivo):
    raw = subprocess.run(['git', '-C', RAIZ, 'show', '%s:%s' % (commit, archivo)], capture_output=True).stdout
    w = json.loads(raw.decode('utf-8'))
    return [n for n in w['nodes'] if n['name'] == NODO][0]['parameters']['messages']['messageValues'][0]['message']


def main():
    lineas = []
    def s(t=''):
        lineas.append(t)

    s('E8 — Trazabilidad de los prompts del Flujo 2 (consultado sobre la base viva de n8n)')
    s('=' * 78)
    s()
    s('1. Versiones guardadas por n8n de los dos workflows del Flujo 2')
    s(psql("""
SELECT w.name AS workflow, h."versionId" AS version, to_char(h."createdAt" AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI') AS creada_utc,
       json_array_length(h.nodes) AS elementos,
       length(p.m) AS caracteres_prompt, left(p.m,1) = '=' AS es_expresion,
       p.m LIKE '%faq_context%' AS inyecta_base, p.m LIKE '%## EJEMPLOS%' AS tiene_ejemplos, md5(p.m) AS md5_prompt
FROM workflow_history h JOIN workflow_entity w ON w.id = h."workflowId"
CROSS JOIN LATERAL (SELECT n->'parameters'->'messages'->'messageValues'->0->>'message' AS m
                    FROM json_array_elements(h.nodes) n WHERE n->>'name' = 'IA - Motor Decision') p
WHERE w.name LIKE 'Flujo 2%%' AND w.name NOT LIKE '%%PRODUC%%'
ORDER BY h."createdAt";"""))
    s('2. Publicaciones (activaciones y desactivaciones)')
    s(psql("""
SELECT w.name AS workflow, ph."versionId" AS version, ph.event AS evento,
       to_char(ph."createdAt" AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI:SS') AS momento_utc
FROM workflow_publish_history ph JOIN workflow_entity w ON w.id = ph."workflowId"
WHERE w.name LIKE 'Flujo 2%%' ORDER BY ph."createdAt";"""))
    s('2b. Qué workflows del Flujo 2 tienen disparador de Telegram y con qué prompt (estado actual)')
    s(psql("""
SELECT w.name AS workflow,
       EXISTS (SELECT 1 FROM json_array_elements(w.nodes::json) n WHERE n->>'type' = 'n8n-nodes-base.telegramTrigger') AS disparador_telegram,
       (SELECT count(*) FROM workflow_publish_history ph WHERE ph."workflowId" = w.id) AS publicaciones,
       (SELECT string_agg(DISTINCT length(n->'parameters'->'messages'->'messageValues'->0->>'message')::text, ',')
          FROM workflow_history h CROSS JOIN LATERAL json_array_elements(h.nodes) n
          WHERE h."workflowId" = w.id AND n->>'name' = 'IA - Motor Decision'
            AND h."createdAt" < '2026-09-01') AS largos_de_prompt_antes_de_septiembre
FROM workflow_entity w WHERE w.name LIKE 'Flujo 2%%' ORDER BY 1;"""))
    s('   Nota: la variante PRODUCCIÓN no guarda historial; su prompt actual tiene 1032 caracteres')
    s('   y nunca fue publicada.')
    s()
    s('3. Ventanas temporales de cada población medida del Flujo 2 (UTC)')
    s(psql("""
SELECT CASE WHEN user_id LIKE 'E7-%%' THEN 'E7 ablacion (11/09)'
            WHEN user_id LIKE 'E8-%%' THEN 'E8'
            WHEN channel = 'telegram' THEN 'Telegram real (25/08)'
            WHEN received_at >= '2026-08-12 23:00' AND received_at < '2026-08-13 00:00' THEN 'Corpus del Capitulo 5 (12/08)'
            ELSE 'otras mediciones' END AS poblacion,
       count(*) AS filas, to_char(min(received_at),'YYYY-MM-DD HH24:MI:SS') AS desde, to_char(max(received_at),'YYYY-MM-DD HH24:MI:SS') AS hasta
FROM interactions WHERE data_source = 'measured' GROUP BY 1 ORDER BY 3;"""))
    s('4. Copias del workflow guardadas por ejecución (solo sobreviven las recientes)')
    s(psql("""
SELECT to_char(min(e."startedAt") AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI') AS desde_utc,
       to_char(max(e."startedAt") AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI') AS hasta_utc,
       count(*) AS ejecuciones, d."workflowVersionId" AS version,
       md5((SELECT n->'parameters'->'messages'->'messageValues'->0->>'message'
            FROM json_array_elements(d."workflowData"::json->'nodes') n WHERE n->>'name' = 'IA - Motor Decision')) AS md5_prompt
FROM execution_entity e JOIN execution_data d ON d."executionId" = e.id
WHERE e."workflowId" = 'GyT06kIZgB5Kmw4P' GROUP BY 4, 5 ORDER BY 1;"""))
    s('5. El prompt medido en el repositorio')
    f_vieja = prompt_git('f297c9e', 'workflows/Flujo 2 — Chatbot Omnicanal IA.json')
    f_nueva = prompt_git('f68da9d', 'workflows/Flujo 2 — Chatbot Omnicanal IA.json')
    for c, p in (('f297c9e (10/08)', f_vieja), ('f68da9d (14/08)', f_nueva)):
        s('   %-18s %d caracteres · empieza con "=": %s · md5 %s' % (c, len(p), p.startswith('='),
                                                                  hashlib.md5(p.encode('utf-8')).hexdigest()))
    s('   En n8n, un parámetro que no empieza con "=" es texto literal: en f297c9e la')
    s('   expresión {{ $json.faq_context }} no se reemplaza. La versión que corrió el 12/08')
    s('   (4e2d3bc4) coincide byte a byte con f68da9d.')
    s()
    s('6. Lectura')
    s('   - El corpus del Capítulo 5 (12/08, 23:45 a 23:53 UTC) corrió 4 minutos después de')
    s('     publicarse la versión 4e2d3bc4: prompt de 6339 caracteres con base, reglas y ejemplos.')
    s('   - Las 45 interacciones de Telegram (25/08, 14:30 a 15:17 UTC) corrieron con el prompt')
    s('     reducido. Solo dos workflows tienen disparador de Telegram y ambos llevan el prompt de')
    s('     1032 caracteres; el único con el prompt principal (4e2d3bc4) no tiene ese disparador.')
    s('     La versión a4a57b19 cubre la segunda mitad (desde su publicación, 15:14 UTC); la que')
    s('     atendió la primera mitad no se conserva. Las respuestas de ambas mitades no reproducen')
    s('     la base, lo que es consistente con el prompt reducido.')
    s('   - E7 (11/09) corrió con la versión a4a57b19, verificado por la copia de cada ejecución.')
    io.open(SALIDA, 'w', encoding='utf-8').write('\n'.join(lineas))
    print('\n'.join(lineas))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
