# -*- coding: utf-8 -*-
"""E8 — Exactitud media por repetición, con su intervalo. ANÁLISIS AGREGADO, NO PRE-REGISTRADO.

Se agrega el 16/09/2026 a pedido del dictamen del 15/09: la medida primaria de
analizar_e8.py es la exactitud por mayoría de tres repeticiones, que describe un
clasificador por votación, mientras que el sistema desplegado hace una sola
llamada por mensaje. La exactitud media por repetición estima el desempeño de
esa llamada única. No reemplaza a la medida primaria ni cambia ninguna regla de
decisión del análisis pre-registrado.

Intervalo. Las tres repeticiones de un mensaje no son independientes, de modo
que el intervalo no se calcula sobre las 450 clasificaciones como si lo fueran.
Se calcula sobre la proporción de aciertos de cada mensaje en sus tres
repeticiones (0, 1/3, 2/3 o 1), cuya media sobre los 150 mensajes es la
exactitud media por repetición, con la t de Student de 149 grados de libertad.

Dos modos de cálculo:

  --recuentos (por defecto)  No necesita la base de datos. Los recuentos que
      publica resultados/analisis_e8.txt —aciertos de cada repetición, aciertos
      por mayoría y mensajes con la misma etiqueta en las tres— determinan cuántos
      mensajes acertaron 3, 2, 1 o 0 veces, salvo en pocos casos: con a, b, c y e
      mensajes con 3, 2, 1 y 0 aciertos, y s mensajes estables (siempre 3 o 0),
      a + b = mayoría; 3a + 2b + c = total de aciertos; a + e_estables = s;
      b + c + e_inestables = 150 − s. Se enumeran todas las soluciones enteras y
      se informa el intervalo MÁS AMPLIO entre ellas, que es conservador.
  --base   Lee las predicciones de la base (Docker levantado), verifica que los
      aciertos de cada repetición coincidan con analisis_e8.txt, deja los aciertos
      por mensaje en resultados/e8_aciertos_por_mensaje.csv y calcula el intervalo
      exacto, que debe quedar dentro del informado por --recuentos.

Uso:
    python media_por_repeticion_e8.py
    python media_por_repeticion_e8.py --base
    python media_por_repeticion_e8.py --pruebas
"""
import sys
import io
import os
import re
import csv
import json
import math
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
RESULTADOS = os.path.join(BASE, 'resultados')
ANALISIS = os.path.join(RESULTADOS, 'analisis_e8.txt')
REFERENCIA = os.path.join(RAIZ, 'experiments', 'E2', 'resultados', 'e2_corrida2_clasificaciones.csv')
ACIERTOS_CSV = os.path.join(RESULTADOS, 'e8_aciertos_por_mensaje.csv')
CONDICIONES = ['C1', 'C2', 'C3', 'C4']
REPETICIONES = [1, 2, 3]
N = 150
T_149 = 1.976013   # cuantil 0,975 de la t de Student con 149 grados de libertad


# ------------------------------------------------------------------ estadística
def media_ic_t(valores, t=T_149):
    n = len(valores)
    m = sum(valores) / n
    s = math.sqrt(sum((v - m) ** 2 for v in valores) / (n - 1))
    semi = t * s / math.sqrt(n)
    return m, m - semi, m + semi


def distribuciones_compatibles(mayoria, total, estables, n=N):
    """Todas las (a, b, c, e) enteras —mensajes con 3, 2, 1 y 0 aciertos— compatibles con los recuentos."""
    sol = []
    for b in range(n + 1):
        a = mayoria - b
        c = total - 3 * a - 2 * b
        e_est = estables - a
        if a < 0 or c < 0 or e_est < 0:
            continue
        e_inest = (n - estables) - b - c
        if e_inest < 0 or c + e_est + e_inest != n - mayoria:
            continue
        sol.append((a, b, c, e_est + e_inest))
    return sol


def valores(a, b, c, e):
    return [1.0] * a + [2 / 3] * b + [1 / 3] * c + [0.0] * e


def intervalo_conservador(mayoria, total, estables):
    sol = distribuciones_compatibles(mayoria, total, estables)
    assert sol, 'ninguna distribución compatible con los recuentos'
    ics = [media_ic_t(valores(*s)) for s in sol]
    return ics[0][0], min(lo for _, lo, _ in ics), max(hi for _, _, hi in ics), len(sol)


# ------------------------------------------------------------------ recuentos publicados
def leer_recuentos(texto):
    aciertos = {(c, int(r)): int(x) for c, r, x in re.findall(r'^\s+(C\d) R(\d)\s+(\d+)/150', texto, re.M)}
    may, est = {}, {}
    for c, x, pct in re.findall(r'^\s+(C\d) .*?(\d+)/150 = .*?misma etiqueta en las 3:\s+([\d.]+) %', texto, re.M):
        may[c] = int(x)
        est[c] = int(round(float(pct) * N / 100))
    return aciertos, may, est


# ------------------------------------------------------------------ base de datos
def psql(sql):
    out = subprocess.run(['docker', 'exec', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d', 'ecommerce_tesis',
                          '-t', '-A', '-F', '\x1f', '-R', '\x1e', '-c', sql], capture_output=True)
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    registros = out.stdout.decode('utf-8', 'replace').strip('\n').split('\x1e')
    return [r.strip('\n').split('\x1f') for r in registros if r.strip()]


def aciertos_desde_base():
    with io.open(REFERENCIA, encoding='utf-8-sig') as f:
        ref = list(csv.DictReader(f))
    gt = {r['id']: r['intent_humano'].strip() for r in ref}
    id_de_usr = {r['user_id'].strip(): r['id'] for r in ref}
    oov = list(csv.DictReader(io.open(os.path.join(RESULTADOS, 'e8_fuera_de_vocabulario.csv'), encoding='utf-8-sig')))
    acierto = {}
    for c in CONDICIONES:
        for r in REPETICIONES:
            bloque = '%s_R%d' % (c, r)   # bloque primario: el primer intento, según analisis_e8.txt
            m = json.load(io.open(os.path.join(RESULTADOS, 'e8_manifiesto_%s.json' % bloque), encoding='utf-8-sig'))
            prefijo = m['prefijo_user_id']
            pred = {}
            for uid, intent in psql("SELECT user_id, intent FROM interactions WHERE user_id LIKE '%s%%' ORDER BY id;"
                                    % prefijo):
                crudo = uid[len(prefijo):].replace('@whatsapp.sim', '')
                assert crudo in id_de_usr and id_de_usr[crudo] not in pred, (bloque, uid)
                pred[id_de_usr[crudo]] = intent.strip()
            for o in oov:
                if o['bloque'] == bloque and o['clase'] == 'fuera_de_vocabulario':
                    assert o['id'] not in pred
                    pred[o['id']] = o['etiqueta']
            assert set(pred) == set(gt), '%s: %d predicciones' % (bloque, len(pred))
            acierto[(c, r)] = {i: int(pred[i] == gt[i]) for i in gt}
    return acierto


# ------------------------------------------------------------------ informes
def informe_recuentos():
    aciertos, may, est = leer_recuentos(io.open(ANALISIS, encoding='utf-8').read())
    assert len(aciertos) == 12 and len(may) == 4 and len(est) == 4, 'analisis_e8.txt no tiene los recuentos esperados'
    print('Desde los recuentos de resultados/analisis_e8.txt (sin base de datos).')
    print('Intervalo: el más amplio entre las distribuciones por mensaje compatibles con los recuentos.')
    print()
    print('%-4s %-12s %-10s %-10s %-22s %s' % ('', 'por mayoría', 'estables', 'media rep.', 'IC 95 % conservador',
                                             'distribuciones compatibles'))
    for c in CONDICIONES:
        total = sum(aciertos[(c, r)] for r in REPETICIONES)
        m, lo, hi, k = intervalo_conservador(may[c], total, est[c])
        assert abs(m - total / (3 * N)) < 1e-12
        print('%-4s %-12s %-10s %-10s %-22s %d' % (c, '%.1f %%' % (100 * may[c] / N), est[c], '%.1f %%' % (100 * m),
                                                  '[%.1f ; %.1f]' % (100 * lo, 100 * hi), k))


def informe_base():
    acierto = aciertos_desde_base()
    aciertos, may, est = leer_recuentos(io.open(ANALISIS, encoding='utf-8').read())
    for clave, x in aciertos.items():
        assert sum(acierto[clave].values()) == x, 'los aciertos de %s_R%d no coinciden con analisis_e8.txt' % clave
    ids = sorted(acierto[('C1', 1)], key=int)
    with io.open(ACIERTOS_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id'] + ['%s_R%d' % (c, r) for c in CONDICIONES for r in REPETICIONES])
        for i in ids:
            w.writerow([i] + [acierto[(c, r)][i] for c in CONDICIONES for r in REPETICIONES])
    print('Desde la base de datos; aciertos por repetición verificados contra analisis_e8.txt.')
    for c in CONDICIONES:
        prop = [sum(acierto[(c, r)][i] for r in REPETICIONES) / 3 for i in ids]
        m, lo, hi = media_ic_t(prop)
        _, clo, chi, _ = intervalo_conservador(may[c], round(3 * N * m), est[c])
        assert clo - 1e-9 <= lo and hi <= chi + 1e-9, '%s: el intervalo exacto no cae dentro del conservador' % c
        print('%-4s media %.1f %% · IC 95 %% exacto [%.1f ; %.1f] · conservador [%.1f ; %.1f]'
              % (c, 100 * m, 100 * lo, 100 * hi, 100 * clo, 100 * chi))


# ------------------------------------------------------------------ pruebas
def pruebas():
    fallas = []

    def igual(rot, obtenido, esperado):
        if obtenido != esperado:
            fallas.append('%s: se obtuvo %r, se esperaba %r' % (rot, obtenido, esperado))

    m, lo, hi = media_ic_t([1, 1, 0, 0], t=3.182446)   # t de 3 grados de libertad
    igual('media de proporciones', m, 0.5)
    igual('semiancho t conocido', round(hi - m, 4), round(3.182446 * math.sqrt(1 / 3) / 2, 4))
    igual('la media por repetición es la media de las proporciones por mensaje',
          round(media_ic_t(valores(10, 5, 0, 0))[0], 6), round(40 / 45, 6))

    # 4 mensajes: uno acierta 3 veces, uno 2 (inestable), uno 0 estable y uno 0 inestable
    sol = distribuciones_compatibles(mayoria=2, total=5, estables=2, n=4)
    igual('recupera la distribución cuando es única', sol, [(1, 1, 0, 2)])
    sol = distribuciones_compatibles(mayoria=140, total=419, estables=147)
    igual('C1 admite dos distribuciones', sorted(sol), [(138, 2, 1, 9), (139, 1, 0, 10)])
    for a, b, c, e in sol:
        igual('suman 150', a + b + c + e, 150)
        igual('reproducen los aciertos', 3 * a + 2 * b + c, 419)

    texto = ('  C1 R1  140/150 =  93.3 %  IC 95 % [88.2 ; 96.3]\n'
             '  C1 base + reglas y ejemplos              140/150 =  93.3 %  IC 95 % [88.2 ; 96.3] · '
             'misma etiqueta en las 3:  98.0 %\n')
    igual('lee aciertos por repetición', leer_recuentos(texto)[0], {('C1', 1): 140})
    igual('lee mayoría y estables', leer_recuentos(texto)[1:], ({'C1': 140}, {'C1': 147}))

    if fallas:
        print('PRUEBAS: %d FALLAS' % len(fallas))
        for f in fallas:
            print('  - ' + f)
        sys.exit(1)
    print('PRUEBAS: todas pasan')


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if '--pruebas' in sys.argv:
        pruebas()
    elif '--base' in sys.argv:
        informe_base()
    else:
        informe_recuentos()
