# -*- coding: utf-8 -*-
"""E8 — Análisis PRE-REGISTRADO del factorial 2 x 2 (base x reglas y ejemplos).

Escrito y commiteado ANTES de correr los doce bloques. Los criterios no se
modifican después de ver los datos.

Diseño: 4 condiciones (condiciones_e8.py) x 3 repeticiones x 150 mensajes, sobre
el workflow vigente, cambiando solo el prompt de sistema. Mismas etiquetas de
referencia que el Capítulo 5 (e2_corrida2_clasificaciones.csv).

Reporta, en este orden:

  0. INTEGRIDAD. Los 12 bloques existen, cada uno con los 150 mensajes una sola
     vez, manifiesto válido y todas las ejecuciones con el md5 del prompt de su
     condición. Si falla, no se reporta nada.
  1. EXACTITUD POR BLOQUE con IC 95 % de Wilson.
  2. POR CONDICIÓN: media, desvío, mínimo y máximo de las 3 repeticiones.
  3. EXACTITUD POR MAYORÍA: un mensaje cuenta como acierto si acertó en al menos
     2 de las 3 repeticiones. Es la medida primaria, con Wilson.
  4. ESTABILIDAD: proporción de mensajes con la misma etiqueta en las 3.
  5. CONTRASTES: McNemar exacto (binomial bilateral) sobre la corrección por
     mayoría, para los 6 pares de condiciones, con ajuste de Holm, alfa 0,05.
  6. EFECTOS DEL FACTORIAL sobre la exactitud por mayoría (puntos porcentuales):
     efecto de la base, efecto de reglas y ejemplos, interacción y efectos simples.
  7. EXHAUSTIVIDAD POR CLASE y migración FAQ -> GENERAL por condición.
  8. H2b sobre C1, con la regla fijada: se sostiene si el límite inferior del IC
     95 % de Wilson de la exactitud por mayoría es >= 85 %. Se informa también el
     valor puntual.
  9. SENSIBILIDAD: se excluyen los mensajes del corpus con similitud >= 0,80 con
     algún ejemplo del prompt y se recalculan las exactitudes por mayoría.
 10. RÉPLICA: C1 por mayoría frente a la corrida del 12/08 (McNemar exacto).
 11. TMR por condición (secundario).

Lo que NO se hace: no se descarta un bloque válido, no se cambia la medida
primaria ni el ajuste de Holm, y un bloque inválido se vuelve a correr y se
informa junto con el inválido.

DESVÍO DECLARADO (decidido tras el bloque 9 y su reintento, antes de correr los
bloques 10 a 12 y sin haber visto ninguna exactitud): el bloque 9 (C3_R3) y su
reintento quedaron con 149 filas porque el modelo devolvió etiquetas fuera de
las cuatro admitidas («CAMBIO», «DEVOLUCION») y la restricción de la tabla
rechazó el registro. Reintentar hasta obtener una etiqueta válida seleccionaría
las salidas del modelo y sesgaría hacia arriba la exactitud de las condiciones
sin reglas. Por eso:
  - una etiqueta fuera de vocabulario cuenta como predicción errónea
    (resultados/e8_fuera_de_vocabulario.csv, extraída de n8n);
  - un bloque es utilizable si recibió las 150 respuestas, todas sus ejecuciones
    llevan el prompt de su condición y cada fila faltante corresponde a una
    etiqueta fuera de vocabulario; cualquier otro error lo invalida;
  - para cada repetición se usa el PRIMER intento utilizable (el que ocupa la
    posición pre-registrada); los demás se informan en la sección 12.

Uso:
    python analizar_e8.py
    python analizar_e8.py --pruebas
"""
import sys
import io
import os
import re
import csv
import json
import math
import glob
import subprocess
import unicodedata
from difflib import SequenceMatcher
from collections import Counter
from itertools import combinations

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
REFERENCIA = os.path.join(RAIZ, 'experiments', 'E2', 'resultados', 'e2_corrida2_clasificaciones.csv')
RESULTADOS = os.path.join(BASE, 'resultados')
CONDICIONES = ['C1', 'C2', 'C3', 'C4']
REPETICIONES = [1, 2, 3]
CLASES = ['FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL']
UMBRAL_H2B = 0.85
UMBRAL_SIMILITUD = 0.80
ALFA = 0.05
ROTULO = {'C1': 'C1 base + reglas y ejemplos', 'C2': 'C2 reglas y ejemplos, sin base',
          'C3': 'C3 base, sin reglas ni ejemplos', 'C4': 'C4 ni base ni reglas ni ejemplos'}


# ------------------------------------------------------------------ estadística
def wilson(x, n, z=1.959963985):
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    semi = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centro - semi), min(1.0, centro + semi))


def mcnemar_exacto(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def holm(pvalores):
    orden = sorted(range(len(pvalores)), key=lambda i: pvalores[i])
    m = len(pvalores)
    ajustados = [0.0] * m
    maximo = 0.0
    for rango, i in enumerate(orden):
        maximo = max(maximo, min(1.0, (m - rango) * pvalores[i]))
        ajustados[i] = maximo
    return ajustados


def media_desvio(xs):
    m = sum(xs) / len(xs)
    s = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    return m, s


def mayoria(aciertos):
    return sum(aciertos) >= 2


def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s).split())


# ------------------------------------------------------------------ datos
def psql(sql):
    # separadores de campo y de registro que no aparecen en el texto de las respuestas,
    # que pueden traer tabulaciones y saltos de línea
    out = subprocess.run(['docker', 'exec', 'tesis_postgres', 'psql', '-U', 'n8n_user', '-d', 'ecommerce_tesis',
                          '-t', '-A', '-F', '\x1f', '-R', '\x1e', '-c', sql], capture_output=True)
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    registros = out.stdout.decode('utf-8', 'replace').strip('\n').split('\x1e')
    return [r.strip('\n').split('\x1f') for r in registros if r.strip()]


def titulo(t):
    print()
    print('=' * 78)
    print(' ' + t)
    print('=' * 78)


def main():
    cond = json.load(io.open(os.path.join(BASE, 'condiciones_e8.json'), encoding='utf-8'))['condiciones']
    with io.open(REFERENCIA, encoding='utf-8-sig') as f:
        ref = list(csv.DictReader(f))
    gt = {r['id']: r['intent_humano'].strip() for r in ref}
    pred_ago = {r['id']: r['intent_modelo_c2'].strip() for r in ref}
    id_de_usr = {r['user_id'].strip(): r['id'] for r in ref}
    with io.open(os.path.join(RAIZ, 'experiments', 'E2', 'corpus_intents.csv'), encoding='utf-8') as f:
        mensaje = {r['id']: r['mensaje'] for r in csv.DictReader(f)}
    ids = sorted(gt, key=int)

    # ------------------------------------------------ 0. integridad
    titulo('0. INTEGRIDAD')
    pred, tmr, errores, problemas = {}, {}, {}, []
    ruta_oov = os.path.join(RESULTADOS, 'e8_fuera_de_vocabulario.csv')
    oov = list(csv.DictReader(io.open(ruta_oov, encoding='utf-8-sig'))) if os.path.exists(ruta_oov) else []

    def cargar(m):
        """Devuelve (utilizable, motivo, predicciones, tmr, errores_parseo, n_fuera_de_vocabulario)."""
        b, c = m['bloque'], m['condicion']
        with io.open(os.path.join(RESULTADOS, 'e8_evidencia_%s.csv' % b), encoding='utf-8-sig') as f:
            ev = list(csv.DictReader(f))
        motivos = []
        if int(m['http_200']) != int(m['mensajes']):
            motivos.append('HTTP 200 en %s de %s' % (m['http_200'], m['mensajes']))
        if any(e['md5_prompt'] != cond[c]['md5'] for e in ev) or len(ev) < int(m['mensajes']):
            motivos.append('ejecuciones con otro prompt o faltantes')
        prefijo = m['prefijo_user_id']
        p, t, err = {}, [], 0
        for uid, intent, resp, seg in psql("SELECT user_id, intent, ai_response, EXTRACT(epoch FROM responded_at - received_at) "
                                           "FROM interactions WHERE user_id LIKE '%s%%' ORDER BY id;" % prefijo):
            crudo = uid[len(prefijo):].replace('@whatsapp.sim', '')
            if crudo in id_de_usr:
                if id_de_usr[crudo] in p:
                    motivos.append('mensaje %s duplicado' % id_de_usr[crudo])
                p[id_de_usr[crudo]] = intent.strip()
            if seg:
                t.append(float(seg))
            err += 'hubo un error' in resp
        suyos = [o for o in oov if o['bloque'] == b]
        if any(o['clase'] != 'fuera_de_vocabulario' for o in suyos):
            motivos.append('errores que no son etiquetas fuera de vocabulario')
        n_oov = 0
        for o in suyos:
            if o['clase'] == 'fuera_de_vocabulario' and o['id'] and o['id'] not in p:
                p[o['id']] = o['etiqueta']
                n_oov += 1
        if set(p) != set(ids):
            motivos.append('%d de %d mensajes con predicción' % (len(p), len(ids)))
        return (not motivos, '; '.join(motivos), p, t, err, n_oov)

    otros_intentos = []
    for c in CONDICIONES:
        for r in REPETICIONES:
            intentos = sorted(glob.glob(os.path.join(RESULTADOS, 'e8_manifiesto_%s_R%d.json' % (c, r))) +
                              glob.glob(os.path.join(RESULTADOS, 'e8_manifiesto_%s_R%d_i*.json' % (c, r))))
            manifs = sorted((json.load(io.open(x, encoding='utf-8-sig')) for x in intentos),
                            key=lambda x: x.get('intento', 1))
            elegido = None
            for m in manifs:
                ok, motivo, p, t, err, n_oov = cargar(m)
                if ok and elegido is None:
                    elegido = m['bloque']
                    pred[(c, r)], tmr[(c, r)], errores[(c, r)] = p, t, err
                    print('  %-10s PRIMARIO · %d predicciones (%d fuera de vocabulario) · errores de parseo %d'
                          % (m['bloque'], len(p), n_oov, err))
                else:
                    otros_intentos.append((m, ok, motivo, p))
                    print('  %-10s %s · %s' % (m['bloque'], 'utilizable, no primario' if ok else 'NO utilizable', motivo or '-'))
            if elegido is None:
                problemas.append('%s_R%d: ningún intento utilizable' % (c, r))
    if problemas:
        print('\n  >>> INTEGRIDAD NO VERIFICADA. No se reporta el análisis:')
        for x in problemas:
            print('      - ' + x)
        sys.exit(3)

    acierto = {(c, r): {i: pred[(c, r)][i] == gt[i] for i in ids} for c in CONDICIONES for r in REPETICIONES}
    may = {c: {i: mayoria([acierto[(c, r)][i] for r in REPETICIONES]) for i in ids} for c in CONDICIONES}
    n = len(ids)

    # ------------------------------------------------ 1 y 2
    titulo('1-2. EXACTITUD POR BLOQUE Y POR CONDICIÓN')
    por_cond = {}
    for c in CONDICIONES:
        accs = []
        for r in REPETICIONES:
            x = sum(acierto[(c, r)].values())
            lo, hi = wilson(x, n)
            accs.append(x / n)
            print('  %s R%d  %3d/%d = %5.1f %%  IC 95 %% [%4.1f ; %4.1f]' % (c, r, x, n, 100 * x / n, 100 * lo, 100 * hi))
        m, s = media_desvio(accs)
        por_cond[c] = (m, s, min(accs), max(accs))
        print('  %-40s media %5.1f %% · desvío %4.1f · rango %4.1f–%4.1f\n'
              % (ROTULO[c], 100 * m, 100 * s, 100 * min(accs), 100 * max(accs)))

    # ------------------------------------------------ 3 y 4
    titulo('3-4. EXACTITUD POR MAYORÍA (MEDIDA PRIMARIA) Y ESTABILIDAD')
    acc_may = {}
    for c in CONDICIONES:
        x = sum(may[c].values())
        lo, hi = wilson(x, n)
        acc_may[c] = x / n
        estables = sum(1 for i in ids if len({pred[(c, r)][i] for r in REPETICIONES}) == 1)
        print('  %-40s %3d/%d = %5.1f %%  IC 95 %% [%4.1f ; %4.1f] · misma etiqueta en las 3: %5.1f %%'
              % (ROTULO[c], x, n, 100 * x / n, 100 * lo, 100 * hi, 100 * estables / n))

    # ------------------------------------------------ 5
    titulo('5. CONTRASTES POR PARES (McNemar exacto, Holm, alfa 0,05)')
    pares = list(combinations(CONDICIONES, 2))
    crudos = []
    for a, b in pares:
        solo_a = sum(1 for i in ids if may[a][i] and not may[b][i])
        solo_b = sum(1 for i in ids if may[b][i] and not may[a][i])
        crudos.append((a, b, solo_a, solo_b, mcnemar_exacto(solo_a, solo_b)))
    ajust = holm([x[4] for x in crudos])
    for (a, b, sa, sb, p), pa in zip(crudos, ajust):
        print('  %s vs %s  diferencia %+5.1f pp · solo %s %2d · solo %s %2d · p %.4f · p Holm %.4f  %s'
              % (a, b, 100 * (acc_may[a] - acc_may[b]), a, sa, b, sb, p, pa, 'SIGNIFICATIVA' if pa < ALFA else ''))

    # ------------------------------------------------ 6
    titulo('6. EFECTOS DEL FACTORIAL (puntos porcentuales, exactitud por mayoría)')
    A = {c: 100 * acc_may[c] for c in CONDICIONES}
    print('  base con reglas y ejemplos (C1 − C2) ........ %+5.1f' % (A['C1'] - A['C2']))
    print('  base sin reglas ni ejemplos (C3 − C4) ....... %+5.1f' % (A['C3'] - A['C4']))
    print('  reglas y ejemplos con base (C1 − C3) ........ %+5.1f' % (A['C1'] - A['C3']))
    print('  reglas y ejemplos sin base (C2 − C4) ........ %+5.1f' % (A['C2'] - A['C4']))
    print('  EFECTO PRINCIPAL de la base ................. %+5.1f' % (((A['C1'] - A['C2']) + (A['C3'] - A['C4'])) / 2))
    print('  EFECTO PRINCIPAL de reglas y ejemplos ....... %+5.1f' % (((A['C1'] - A['C3']) + (A['C2'] - A['C4'])) / 2))
    print('  INTERACCIÓN (C1 − C2) − (C3 − C4) ........... %+5.1f' % ((A['C1'] - A['C2']) - (A['C3'] - A['C4'])))

    # ------------------------------------------------ 7
    titulo('7. EXHAUSTIVIDAD POR CLASE (mayoría) Y MIGRACIÓN FAQ -> GENERAL (media por repetición)')
    print('  %-8s' % '' + ''.join('%16s' % k for k in CLASES) + '%14s' % 'FAQ->GENERAL')
    for c in CONDICIONES:
        celdas = []
        for k in CLASES:
            de_k = [i for i in ids if gt[i] == k]
            celdas.append('%3d/%-3d %5.1f%%' % (sum(may[c][i] for i in de_k), len(de_k), 100 * sum(may[c][i] for i in de_k) / len(de_k)))
        mig = sum(sum(1 for i in ids if gt[i] == 'FAQ' and pred[(c, r)][i] == 'GENERAL') for r in REPETICIONES) / 3
        print('  %-8s' % c + ''.join('%16s' % x for x in celdas) + '%14.1f' % mig)

    # ------------------------------------------------ 8
    titulo('8. H2b SOBRE C1 (regla fijada: límite inferior del IC 95 % >= 85 %)')
    x = sum(may['C1'].values())
    lo, hi = wilson(x, n)
    print('  C1 por mayoría: %d/%d = %.1f %% · IC 95 %% [%.1f ; %.1f] · H2b %s'
          % (x, n, 100 * x / n, 100 * lo, 100 * hi, 'SE SOSTIENE' if lo >= UMBRAL_H2B else 'NO SE SOSTIENE'))
    for c in CONDICIONES[1:]:
        xc = sum(may[c].values())
        loc, _ = wilson(xc, n)
        print('  %s por mayoría: %.1f %% · límite inferior %.1f %% · %s'
              % (c, 100 * xc / n, 100 * loc, 'lo alcanzaría' if loc >= UMBRAL_H2B else 'no lo alcanzaría'))

    # ------------------------------------------------ 9
    titulo('9. SENSIBILIDAD: sin los mensajes parecidos a los ejemplos del prompt (similitud >= 0,80)')
    prompt_c1 = io.open(os.path.join(BASE, 'prompts', 'C1.txt'), encoding='utf-8').read()
    ejemplos = re.findall(r'Mensaje: "([^"]+)"', prompt_c1)
    parecidos = [i for i in ids if any(SequenceMatcher(None, norm(e), norm(mensaje[i])).ratio() >= UMBRAL_SIMILITUD
                                       for e in ejemplos)]
    print('  excluidos: %s' % ', '.join('%s («%s»)' % (i, mensaje[i]) for i in parecidos) if parecidos else '  ninguno')
    resto = [i for i in ids if i not in parecidos]
    for c in CONDICIONES:
        xs = sum(may[c][i] for i in resto)
        print('  %s  %d/%d = %.1f %% (con todos: %.1f %%)' % (c, xs, len(resto), 100 * xs / len(resto), 100 * acc_may[c]))

    # ------------------------------------------------ 10
    titulo('10. RÉPLICA: C1 por mayoría frente a la corrida del 12/08')
    ok_ago = {i: pred_ago[i] == gt[i] for i in ids}
    solo_ago = sum(1 for i in ids if ok_ago[i] and not may['C1'][i])
    solo_c1 = sum(1 for i in ids if may['C1'][i] and not ok_ago[i])
    print('  12/08: %d/%d = %.1f %% · C1: %.1f %% · solo 12/08 %d · solo C1 %d · p exacto %.4f'
          % (sum(ok_ago.values()), n, 100 * sum(ok_ago.values()) / n, 100 * acc_may['C1'], solo_ago, solo_c1,
             mcnemar_exacto(solo_ago, solo_c1)))

    # ------------------------------------------------ 11
    titulo('11. TMR POR CONDICIÓN (secundario)')
    for c in CONDICIONES:
        t = [s for r in REPETICIONES for s in tmr[(c, r)]]
        m, s = media_desvio(t)
        print('  %-40s %.2f s ± %.2f (n = %d) · prompt de %d caracteres' % (ROTULO[c], m, s, len(t), cond[c]['caracteres']))

    titulo('12. ETIQUETAS FUERA DE VOCABULARIO E INTENTOS NO PRIMARIOS')
    fv = [o for o in oov if o['clase'] == 'fuera_de_vocabulario']
    print('  etiquetas fuera de vocabulario: %d' % len(fv))
    for o in fv:
        print('    %-10s mensaje %s «%s» -> «%s» (referencia %s)' % (o['bloque'], o['id'], o['mensaje'][:50], o['etiqueta'], o['referencia']))
    por_condicion = Counter(o['bloque'].split('_')[0] for o in fv)
    print('  por condición: %s' % (', '.join('%s %d' % (c, por_condicion.get(c, 0)) for c in CONDICIONES)))
    if not otros_intentos:
        print('  intentos no primarios: ninguno')
    for x, ok, motivo, alt in otros_intentos:
        c, r = x['condicion'], x['repeticion']
        if set(alt) != set(ids):
            print('  %s: no se puede recalcular (%s)' % (x['bloque'], motivo))
            continue
        ac_alt = {i: alt[i] == gt[i] for i in ids}
        may_alt = {i: mayoria([ac_alt[i] if rr == r else acierto[(c, rr)][i] for rr in REPETICIONES]) for i in ids}
        xa = sum(may_alt.values())
        lo, hi = wilson(xa, n)
        print('  %s en lugar del primario: %s por mayoría %.1f %% [%.1f ; %.1f] (primario %.1f %%) · exactitud de ese intento %.1f %%'
              % (x['bloque'], c, 100 * xa / n, 100 * lo, 100 * hi, 100 * acc_may[c], 100 * sum(ac_alt.values()) / n))

    titulo('CIFRAS PARA EL DOCUMENTO')
    for c in CONDICIONES:
        m, s, mn, mx = por_cond[c]
        print('  %s  mayoría %.1f %% · media de repeticiones %.1f %% ± %.1f (rango %.1f–%.1f)'
              % (c, 100 * acc_may[c], 100 * m, 100 * s, 100 * mn, 100 * mx))


def pruebas():
    fallas = []

    def igual(rot, a, b):
        if a != b:
            fallas.append('%s: %r != %r' % (rot, a, b))

    igual('McNemar E7 (14 contra 4)', round(mcnemar_exacto(14, 4), 3), 0.031)
    igual('McNemar sin discordantes', mcnemar_exacto(0, 0), 1.0)
    igual('McNemar simétrico', mcnemar_exacto(3, 9), mcnemar_exacto(9, 3))
    igual('Holm', [round(x, 4) for x in holm([0.01, 0.04, 0.03])], [0.03, 0.06, 0.06])
    igual('Holm acotado a 1', holm([0.6, 0.9]), [1.0, 1.0])
    igual('Wilson 139/150', tuple(round(x, 3) for x in wilson(139, 150)), (0.873, 0.959))
    igual('mayoría 2 de 3', mayoria([True, False, True]), True)
    igual('mayoría 1 de 3', mayoria([False, False, True]), False)
    igual('media y desvío', tuple(round(x, 4) for x in media_desvio([0.9, 0.92, 0.94])), (0.92, 0.02))
    igual('normalización', norm('Cuánto tarda el envío a Córdoba?'), 'cuanto tarda el envio a cordoba')
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
    else:
        main()
