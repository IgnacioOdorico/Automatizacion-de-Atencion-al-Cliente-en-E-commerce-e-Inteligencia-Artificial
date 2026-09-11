# -*- coding: utf-8 -*-
"""E7 — Analisis de la ablacion: con contexto de FAQ contra sin contexto.

Las dos condiciones corrieron EL MISMO corpus de 150 mensajes contra EL MISMO
conjunto de etiquetas de referencia. Eso hace que el diseño sea APAREADO, y el
contraste que corresponde no es el de dos proporciones independientes sino la
prueba de McNemar sobre los pares discordantes.

  Condicion A (12/08) : prompt de 6338 caracteres — base de conocimiento
                        inyectada, 7 ejemplos etiquetados, reglas por categoria.
                        Es la que produjo el 92,7 % del Capitulo 5.
  Condicion B (E7)    : prompt de 1032 caracteres — solo identidad, tarea y
                        formato de salida. Zero-shot sin contexto.

Uso:
    python analizar_e7.py
"""
import sys
import io
import os
import csv
import math
import subprocess
from collections import Counter, OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
CORRIDA_A = os.path.join(RAIZ, 'experiments', 'E2', 'resultados',
                         'e2_corrida2_clasificaciones.csv')
CLASES = ['FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL']
PREFIJO = 'E7-'


def titulo(t):
    print()
    print('=' * 76)
    print(' ' + t)
    print('=' * 76)


def psql(sql):
    out = subprocess.run(
        ['docker', 'exec', 'tesis_postgres', 'psql', '-U', 'n8n_user',
         '-d', 'ecommerce_tesis', '-t', '-A', '-F', '\t', '-c', sql],
        capture_output=True)
    txt = out.stdout.decode('utf-8', 'replace')
    return [l.split('\t') for l in txt.strip().split('\n') if l.strip()]


def wilson(x, n, z=1.959963985):
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    semi = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centro - semi, centro + semi)


def normal_sf(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def mcnemar(b, c):
    """b: aciertos solo en A. c: aciertos solo en B. Devuelve (chi2, p, exacto)."""
    n = b + c
    if n == 0:
        return (0.0, 1.0, 1.0)
    # chi cuadrado con correccion de continuidad de Yates
    chi2 = (abs(b - c) - 1) ** 2 / n if n > 0 else 0.0
    p_chi = math.erfc(math.sqrt(chi2 / 2)) if chi2 > 0 else 1.0
    # binomial exacta bilateral (la que corresponde con n chico)
    k = min(b, c)
    acum = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    p_exacto = min(1.0, 2 * acum)
    return (chi2, p_chi, p_exacto)


def main():
    # ------------------------------------------------ condicion A (12/08)
    if not os.path.exists(CORRIDA_A):
        sys.exit('No encuentro %s' % CORRIDA_A)
    with io.open(CORRIDA_A, encoding='utf-8-sig') as f:
        filas_a = list(csv.DictReader(f))
    gt = OrderedDict((r['id'], r['intent_humano'].strip()) for r in filas_a)
    pred_a = {r['id']: r['intent_modelo_c2'].strip() for r in filas_a}
    usr_de_id = {r['user_id'].strip(): r['id'] for r in filas_a}

    # ------------------------------------------------ condicion B (E7)
    filas_b = psql("""
        SELECT user_id, intent FROM interactions
        WHERE user_id LIKE '%s%%' ORDER BY id;""" % PREFIJO)
    pred_b = {}
    for uid, intent in filas_b:
        crudo = uid[len(PREFIJO):].replace('@whatsapp.sim', '')
        if crudo in usr_de_id:
            pred_b[usr_de_id[crudo]] = intent.strip()

    titulo('0. INTEGRIDAD DE LAS DOS CORRIDAS')
    print('  corpus / etiquetas de referencia : %d mensajes' % len(gt))
    print('  condicion A (con FAQ, 12/08)     : %d clasificaciones' % len(pred_a))
    print('  condicion B (sin FAQ, E7)        : %d clasificaciones' % len(pred_b))
    ids = [i for i in gt if i in pred_a and i in pred_b]
    print('  mensajes en AMBAS condiciones    : %d' % len(ids))
    if len(ids) != len(gt):
        faltan = [i for i in gt if i not in pred_b]
        print('  AVISO: faltan %d en la condicion B: %s' % (len(faltan), faltan[:12]))
    if not ids:
        sys.exit('\n  Sin datos de la condicion B. Corre primero run_ablacion_zeroshot.ps1')

    # ------------------------------------------------ accuracy
    titulo('1. EXACTITUD EN CADA CONDICION')
    n = len(ids)
    ok_a = sum(1 for i in ids if pred_a[i] == gt[i])
    ok_b = sum(1 for i in ids if pred_b[i] == gt[i])
    for rot, ok in (('A — con contexto de FAQ y 7 ejemplos (6338 car.)', ok_a),
                    ('B — sin contexto de FAQ ni ejemplos (1032 car.)', ok_b)):
        lo, hi = wilson(ok, n)
        print('  %-50s %3d/%d = %5.1f %%   IC 95 %% Wilson [%.1f ; %.1f]'
              % (rot, ok, n, 100 * ok / n, 100 * lo, 100 * hi))
    dif = 100 * (ok_a - ok_b) / n
    print()
    print('  Diferencia: %.1f puntos porcentuales a favor de la condicion con contexto.'
          % dif)

    # ------------------------------------------------ McNemar
    titulo('2. CONTRASTE APAREADO (McNemar)')
    aa = sum(1 for i in ids if pred_a[i] == gt[i] and pred_b[i] == gt[i])
    ab = sum(1 for i in ids if pred_a[i] == gt[i] and pred_b[i] != gt[i])
    ba = sum(1 for i in ids if pred_a[i] != gt[i] and pred_b[i] == gt[i])
    bb = sum(1 for i in ids if pred_a[i] != gt[i] and pred_b[i] != gt[i])
    print('  Tabla 2x2 sobre los mismos %d mensajes:' % n)
    print()
    print('                        B acierta   B falla')
    print('      A acierta   %11d %9d' % (aa, ab))
    print('      A falla     %11d %9d' % (ba, bb))
    print()
    print('  Pares discordantes: %d (solo A acierta) y %d (solo B acierta)' % (ab, ba))
    chi2, p_chi, p_ex = mcnemar(ab, ba)
    print('  chi2 de McNemar con correccion de Yates = %.3f   p = %.4f' % (chi2, p_chi))
    print('  Binomial exacta bilateral                p = %.4f' % p_ex)
    print()
    if p_ex < 0.05:
        print('  La diferencia entre condiciones NO es atribuible al azar (p < 0,05).')
    else:
        print('  La diferencia NO alcanza significacion al 5 %: con este n, el efecto')
        print('  observado es compatible con variacion de muestreo.')
    print('  El diseño es apareado —mismo corpus, mismas etiquetas— de modo que el')
    print('  contraste aisla el efecto del prompt y no la diferencia entre muestras.')

    # ------------------------------------------------ por clase
    titulo('3. EXACTITUD POR CLASE')
    print('  %-16s %8s %14s %14s' % ('clase', 'n', 'A (con FAQ)', 'B (sin FAQ)'))
    for c in CLASES:
        sub = [i for i in ids if gt[i] == c]
        if not sub:
            continue
        a = sum(1 for i in sub if pred_a[i] == c)
        b = sum(1 for i in sub if pred_b[i] == c)
        print('  %-16s %8d %10d (%3.0f %%) %8d (%3.0f %%)'
              % (c, len(sub), a, 100 * a / len(sub), b, 100 * b / len(sub)))

    # ------------------------------------------------ matriz de la condicion B
    titulo('4. MATRIZ DE CONFUSION DE LA CONDICION B (sin contexto)')
    print('  filas = etiqueta de referencia, columnas = prediccion')
    print('  %-16s' % '' + ''.join('%15s' % c for c in CLASES) + '%8s' % 'total')
    for r in CLASES:
        fila = [sum(1 for i in ids if gt[i] == r and pred_b[i] == p) for p in CLASES]
        print('  %-16s' % r + ''.join('%15d' % v for v in fila) + '%8d' % sum(fila))
    print('  %-16s' % 'total' + ''.join(
        '%15d' % sum(1 for i in ids if pred_b[i] == p) for p in CLASES)
        + '%8d' % len(ids))

    # ------------------------------------------------ casos que se dan vuelta
    titulo('5. LOS MENSAJES QUE CAMBIAN DE VEREDICTO')
    msg = {r['id']: r['mensaje'] for r in filas_a}
    perdidos = [i for i in ids if pred_a[i] == gt[i] and pred_b[i] != gt[i]]
    ganados = [i for i in ids if pred_a[i] != gt[i] and pred_b[i] == gt[i]]
    print('  Acertaba CON contexto y falla SIN contexto (%d):' % len(perdidos))
    for i in perdidos[:14]:
        print('    [%3s] %-54s  %s -> %s' % (i, msg[i][:54], gt[i], pred_b[i]))
    if len(perdidos) > 14:
        print('    ... y %d mas' % (len(perdidos) - 14))
    print()
    print('  Fallaba CON contexto y acierta SIN contexto (%d):' % len(ganados))
    for i in ganados[:14]:
        print('    [%3s] %-54s  %s' % (i, msg[i][:54], gt[i]))

    titulo('CIFRAS PARA EL DOCUMENTO')
    lo_a, hi_a = wilson(ok_a, n)
    lo_b, hi_b = wilson(ok_b, n)
    print('  n (apareado) ................ %d mensajes' % n)
    print('  con contexto + ejemplos ..... %.1f %%  IC 95 %% [%.1f ; %.1f]'
          % (100 * ok_a / n, 100 * lo_a, 100 * hi_a))
    print('  sin contexto (zero-shot) .... %.1f %%  IC 95 %% [%.1f ; %.1f]'
          % (100 * ok_b / n, 100 * lo_b, 100 * hi_b))
    print('  diferencia .................. %.1f puntos' % dif)
    print('  McNemar ..................... b=%d  c=%d  p exacto = %.4f' % (ab, ba, p_ex))


if __name__ == '__main__':
    main()
