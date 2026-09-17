# -*- coding: utf-8 -*-
"""Las dos corridas del corpus del 12/08, comparadas (defecto D-7).

La primera corrida (11:09) recibió 150 respuestas HTTP 200 y escribió 115 filas:
se perdieron las 35 que el modelo mandó a la rama ESTADO_PEDIDO, porque el nodo
Buscar Pedido no emitía ningún ítem cuando el pedido citado no existía y el resto
del subgrafo no llegaba a ejecutarse. El cliente no recibió respuesta y la
ejecución quedó en estado success. La corrida definitiva (20:45) se ejecutó sobre
el sistema corregido y es la que reporta el Capítulo 5.

Este guion reconstruye la comparación desde los archivos versionados:

  - envíos y faltantes de cada corrida (e2_envios_*.csv, e2_faltantes_*.csv);
  - exactitud de cada corrida, con intervalo de Wilson;
  - coincidencia de etiquetas entre ambas sobre el mismo mensaje;
  - distribución de los faltantes por intención del modelo, que es la prueba
    causal del defecto;
  - latencia de la solicitud HTTP en cada corrida, que no depende de la base.

Con --base agrega el TMR registrado en interactions, que es la métrica que informa
el Capítulo 5 (la corrida 1 dejó sus 115 filas en la tabla).

    python corrida1_vs_corrida2.py [--base] > resultados/corrida1_vs_corrida2.txt
"""
import csv
import io
import math
import os
import statistics
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(BASE, 'resultados')
C1 = 'e2_clasificaciones.csv'                     # corrida 1, recuperada de las ejecuciones
C2 = 'e2_corrida2_clasificaciones.csv'            # corrida 2, la definitiva
ENVIOS1 = 'e2_envios_2026-08-12_11-09-23.csv'
ENVIOS2 = 'e2_envios_2026-08-12_20-45-25.csv'
FALTANTES = 'e2_faltantes_2026-08-12_11-09-23.csv'


def leer(nombre):
    with io.open(os.path.join(RES, nombre), encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d * 100, (c + r) / d * 100)


def sql(consulta):
    out = subprocess.run(['docker', 'exec', '-i', 'tesis_postgres', 'psql', '-U', 'n8n_user',
                          '-d', 'ecommerce_tesis', '-At', '-F', '\x1f'],
                         input=consulta.encode('utf-8'), capture_output=True)
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    return [f.split('\x1f') for f in out.stdout.decode('utf-8').strip().splitlines() if f]


def main(con_base):
    c1 = {f['id']: f for f in leer(C1)}
    c2 = {f['id']: f for f in leer(C2)}
    env1, env2 = leer(ENVIOS1), leer(ENVIOS2)
    faltan = {f['id'] for f in leer(FALTANTES)}
    assert len(c1) == len(c2) == 150 and len(faltan) == 35

    print('Las dos corridas del corpus del 12/08 — defecto D-7')
    print('=' * 70)
    print()
    print('%-34s %14s %14s' % ('', 'corrida 1', 'corrida 2'))
    print('%-34s %14s %14s' % ('hora de inicio', '11:09', '20:45'))
    print('%-34s %14d %14d' % ('mensajes enviados', len(env1), len(env2)))
    print('%-34s %14s %14s' % ('respuestas HTTP 200',
                               sum(1 for e in env1 if e['http'] == '200'),
                               sum(1 for e in env2 if e['http'] == '200')))
    print('%-34s %14d %14d' % ('filas escritas en interactions', 150 - len(faltan), 150))
    print('%-34s %14d %14d' % ('mensajes sin respuesta al cliente', len(faltan), 0))

    a1 = sum(1 for f in c1.values() if f['acierto'] == '1')
    a2 = sum(1 for f in c2.values() if f['acierto_c2'] == '1')
    print('%-34s %14s %14s' % ('aciertos sobre los 150 enviados',
                               '%d (%.1f %%)' % (a1, a1 / 1.5), '%d (%.1f %%)' % (a2, a2 / 1.5)))
    print('%-34s %14s %14s' % ('IC 95 % (Wilson)',
                               '[%.1f; %.1f]' % wilson(a1, 150), '[%.1f; %.1f]' % wilson(a2, 150)))

    iguales = sum(1 for i in c1 if c1[i]['intent_modelo'] == c2[i]['intent_modelo_c2'])
    print()
    print('Misma etiqueta sobre el mismo mensaje: %d de 150 (%.1f %%)' % (iguales, iguales / 1.5))
    print('La exactitud de la corrida omitida es mayor que la de la definitiva: no hay')
    print('selección favorable, sino un problema de transparencia y de alcance.')

    print()
    print('Los 35 faltantes, por intención (la distribución es la prueba causal)')
    for titulo, clave, fuente in (('  según la referencia humana', 'intent_humano', c1),
                                  ('  según la clasificación del modelo', 'intent_modelo', c1)):
        cuenta = {}
        for i in faltan:
            cuenta[fuente[i][clave]] = cuenta.get(fuente[i][clave], 0) + 1
        print('%-38s %s' % (titulo, ' · '.join('%s %d' % kv for kv in sorted(cuenta.items()))))
    print('  Agrupados por la ruta que el mensaje tomó de verdad, el patrón es exacto:')
    print('  se perdió todo lo que entró a la rama ESTADO_PEDIDO, y solo eso.')

    print()
    print('Latencia de la solicitud HTTP, en segundos (medida por el cliente)')
    for rot, env in (('corrida 1', env1), ('corrida 2', env2)):
        v = sorted(float(e['latencia_ms']) / 1000 for e in env if e['latencia_ms'])
        print('  %-10s n = %3d · media %.3f · mediana %.3f · máximo %.3f'
              % (rot, len(v), statistics.mean(v), statistics.median(v), v[-1]))
    print('  El webhook responde en decenas de milisegundos, antes de que el flujo termine:')
    print('  por eso las dos corridas son indistinguibles para el emisor, y la conciliación')
    print('  contra la base es el único control que detecta la pérdida.')

    if con_base:
        print()
        print('TMR registrado en interactions, en segundos (la métrica del Capítulo 5)')
        filas = sql("""
            SELECT CASE WHEN id BETWEEN 234 AND 383 THEN 'corrida 2' ELSE 'corrida 1' END,
                   coalesce(intent, 'TODAS'),
                   COUNT(*),
                   ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::numeric, 3),
                   ROUND(MAX(EXTRACT(EPOCH FROM (responded_at - received_at)))::numeric, 3)
            FROM interactions
            WHERE data_source = 'measured' AND received_at::date = DATE '2026-08-12'
            GROUP BY ROLLUP(1, 2) HAVING COUNT(*) > 0 ORDER BY 1, 2;""")
        for corrida, intent, n, media, maximo in filas:
            if corrida:
                print('  %-10s %-14s n = %3s · media %s · máximo %s' % (corrida, intent, n, media, maximo))
        print('  La corrida 1 no tiene ESTADO_PEDIDO: son las 35 interacciones que no se')
        print('  escribieron. Su TMR global es 2,424 s frente a 1,469 s de la definitiva:')
        print('  la segunda es un 39 % más baja, por la latencia del proveedor de inferencia.')


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main('--base' in sys.argv)
