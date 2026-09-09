# -*- coding: utf-8 -*-
"""E6 — Analisis de la evaluacion de correccion del contenido.

Uso:
    python analizar_e6.py resultados/e6_maximo_muguruza.csv resultados/e6_joaquin_maya.csv

Reporta, en este orden:

  1. CONTROL DE VALIDEZ POR TIEMPOS. El mismo control forense que invalido la
     primera ronda del etiquetado de intenciones. Una evaluacion que promedia
     menos de 8 s por item no pudo haber leido la respuesta (235 caracteres de
     media) ni cotejado contra la base de conocimiento. Si el control falla, el
     resto del analisis NO se reporta.
  2. DISTRIBUCION POR NIVEL de cada evaluador.
  3. ACUERDO: Po, Pe y kappa de Cohen, interpretado contra Landis y Koch (1977),
     que es la misma escala que usa la Seccion 3.5.3 para el acuerdo de
     intenciones.
  4. RESULTADO SUSTANTIVO con lectura conservadora: cuantas respuestas se apoyan
     efectivamente en la politica de la tienda segun AMBOS evaluadores.
  5. DESACUERDOS caso por caso. Son los casos frontera y son lo mas informativo:
     van al capitulo, no se esconden.
"""
import sys
import io
import os
import csv
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
NIVELES = ['A', 'B', 'C']
ROTULO = {
    'A': 'Consistente con la política',
    'B': 'Genérica, no contradictoria',
    'C': 'Contradice la política',
}
UMBRAL_SEG = 8.0   # piso de tiempo por item para considerar la evaluacion valida


def titulo(t):
    print()
    print('=' * 74)
    print(' ' + t)
    print('=' * 74)


def leer(path):
    with io.open(path, encoding='utf-8-sig') as f:
        filas = list(csv.DictReader(f))
    d = {}
    for r in filas:
        d[r['id'].strip()] = {
            'nivel': r['nivel'].strip().upper(),
            'seg': float(r['segundos']),
        }
    return d


def mediana(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return 0.0
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def kappa(pares):
    """Kappa de Cohen sobre pares (a, b) de etiquetas."""
    n = len(pares)
    po = sum(1 for a, b in pares if a == b) / n
    ca = Counter(a for a, _ in pares)
    cb = Counter(b for _, b in pares)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in NIVELES)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return po, pe, k


def landis_koch(k):
    if k < 0:      return 'pobre'
    if k < 0.21:   return 'leve'
    if k < 0.41:   return 'aceptable'
    if k < 0.61:   return 'moderado'
    if k < 0.81:   return 'sustancial'
    return 'casi perfecto'


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    pa, pb = sys.argv[1], sys.argv[2]
    na = os.path.basename(pa).replace('e6_', '').replace('.csv', '').replace('_', ' ').title()
    nb = os.path.basename(pb).replace('e6_', '').replace('.csv', '').replace('_', ' ').title()
    A, B = leer(pa), leer(pb)

    # las respuestas evaluadas, con su texto, para poder mostrar los desacuerdos
    with io.open(os.path.join(BASE, 'faq_respuestas.csv'), encoding='utf-8') as f:
        corpus = {r['id']: r for r in csv.DictReader(f)}

    ids = sorted(set(A) & set(B), key=int)
    faltan = (set(A) ^ set(B))
    if faltan:
        print('AVISO: %d ids no coinciden entre ambos archivos: %s'
              % (len(faltan), sorted(faltan)[:10]))

    # ------------------------------------------------ 1. control de validez
    titulo('1. CONTROL DE VALIDEZ POR TIEMPOS')
    valido = True
    for nom, D in ((na, A), (nb, B)):
        segs = [v['seg'] for v in D.values()]
        med, tot, mn = mediana(segs), sum(segs), min(segs)
        bajo = sum(1 for s in segs if s < 3)
        ok = med >= UMBRAL_SEG
        valido &= ok
        print('  %-20s n=%-3d  mediana %5.1f s  total %5.1f min  mínimo %4.1f s  '
              '<3 s: %-2d  %s'
              % (nom, len(segs), med, tot / 60, mn, bajo, 'VÁLIDO' if ok else 'INVÁLIDO'))
    print()
    print('  Criterio: mediana ≥ %.0f s por ítem. Las respuestas promedian 235 caracteres'
          % UMBRAL_SEG)
    print('  y hay que cotejarlas contra 23 entradas: por debajo de ese piso no hubo lectura.')
    if not valido:
        print()
        print('  >>> EVALUACIÓN INVÁLIDA. No se reporta el resto del análisis.')
        sys.exit(2)

    # ------------------------------------------------ 2. distribucion
    titulo('2. DISTRIBUCIÓN POR NIVEL')
    print('  %-30s %-18s %-18s' % ('', na, nb))
    for k in NIVELES:
        ca = sum(1 for i in ids if A[i]['nivel'] == k)
        cb = sum(1 for i in ids if B[i]['nivel'] == k)
        print('  %-30s %3d (%5.1f %%)     %3d (%5.1f %%)'
              % ('%s — %s' % (k, ROTULO[k]), ca, 100 * ca / len(ids), cb, 100 * cb / len(ids)))

    # ------------------------------------------------ 3. acuerdo
    titulo('3. ACUERDO ENTRE EVALUADORES')
    pares = [(A[i]['nivel'], B[i]['nivel']) for i in ids]
    po, pe, k = kappa(pares)
    print('  n = %d respuestas evaluadas por ambos' % len(ids))
    print('  Acuerdo observado  Po = %.4f  (%d de %d coinciden)'
          % (po, sum(1 for a, b in pares if a == b), len(pares)))
    print('  Acuerdo esperado   Pe = %.4f' % pe)
    print('  κ de Cohen         κ  = %.3f   -> %s (Landis y Koch, 1977)' % (k, landis_koch(k)))
    print()
    print('  Matriz de confusión entre evaluadores (filas %s, columnas %s):' % (na, nb))
    print('        ' + ''.join('%8s' % x for x in NIVELES))
    for x in NIVELES:
        fila = [sum(1 for a, b in pares if a == x and b == y) for y in NIVELES]
        print('    %-4s' % x + ''.join('%8d' % v for v in fila))

    # ------------------------------------------------ 4. resultado sustantivo
    titulo('4. RESULTADO SUSTANTIVO')
    ambos_a = [i for i in ids if A[i]['nivel'] == 'B' and B[i]['nivel'] == 'B']
    conA = [i for i in ids if A[i]['nivel'] == 'A' and B[i]['nivel'] == 'A']
    algunaC = [i for i in ids if 'C' in (A[i]['nivel'], B[i]['nivel'])]
    ambasC = [i for i in ids if A[i]['nivel'] == 'C' and B[i]['nivel'] == 'C']
    n = len(ids)
    print('  Respuestas que AMBOS juzgan apoyadas en la política (A y A):')
    print('      %d de %d  (%.1f %%)' % (len(conA), n, 100 * len(conA) / n))
    print('  Respuestas que AMBOS juzgan genéricas pero no contradictorias (B y B):')
    print('      %d de %d  (%.1f %%)' % (len(ambos_a), n, 100 * len(ambos_a) / n))
    print('  Respuestas que ALGUNO juzga contradictorias con la política (lectura conservadora):')
    print('      %d de %d  (%.1f %%)' % (len(algunaC), n, 100 * len(algunaC) / n))
    print('  Respuestas que AMBOS juzgan contradictorias (lectura estricta):')
    print('      %d de %d  (%.1f %%)' % (len(ambasC), n, 100 * len(ambasC) / n))
    if ambasC:
        print()
        print('  Las que ambos marcaron como contradictorias:')
        for i in ambasC:
            print('    [%s] %s' % (i, corpus[i]['message'][:66]))
            print('         -> %s' % corpus[i]['ai_response'][:110].replace('\n', ' '))

    # ------------------------------------------------ 5. desacuerdos
    titulo('5. DESACUERDOS, CASO POR CASO')
    des = [i for i in ids if A[i]['nivel'] != B[i]['nivel']]
    if not des:
        print('  No hubo desacuerdos.')
    else:
        print('  %d de %d (%.1f %%). Son los casos frontera y van al capítulo.'
              % (len(des), n, 100 * len(des) / n))
        print()
        for i in des:
            print('  [%s]  %s: %s   |   %s: %s'
                  % (i, na, A[i]['nivel'], nb, B[i]['nivel']))
            print('        consulta : %s' % corpus[i]['message'][:80])
            print('        respuesta: %s' % corpus[i]['ai_response'][:120].replace('\n', ' '))
            print()

    titulo('CIFRAS PARA EL DOCUMENTO')
    print('  n evaluado ................. %d respuestas de tipo FAQ' % n)
    print('  κ de Cohen ................. %.3f (%s)' % (k, landis_koch(k)))
    print('  acuerdo observado .......... %.1f %%' % (100 * po))
    print('  apoyadas en la política .... %.1f %% (ambos evaluadores)' % (100 * len(conA) / n))
    print('  contradicen la política .... %.1f %% (al menos un evaluador)'
          % (100 * len(algunaC) / n))


if __name__ == '__main__':
    main()
