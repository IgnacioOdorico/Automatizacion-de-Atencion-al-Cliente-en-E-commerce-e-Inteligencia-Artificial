# -*- coding: utf-8 -*-
"""E6 — Todas las corridas de la evaluación por jueces, en un solo informe.

Se hicieron seis corridas con el mismo instrumento (preparar_e6.py): dos de
Máximo Muguruza y cuatro de Joaquín Maya. Este guion no elige cuáles mirar:
aplica a TODAS el mismo control de validez por tiempos que analizar_e6.py
(mediana >= 8 s por ítem) y reporta, sobre las corridas válidas,

  - el acuerdo entre evaluadores distintos, para cada par posible, y
  - el acuerdo de cada evaluador consigo mismo, cuando tiene dos corridas válidas.

Las corridas inválidas se listan, pero no entran en ningún cálculo.

Uso:
    python analizar_rondas_e6.py
"""
import os
import sys
from itertools import combinations

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from analizar_e6 import leer, mediana, kappa, landis_koch, UMBRAL_SEG  # noqa: E402

# (evaluador, n.º de corrida, fecha, archivo), en orden cronológico
CORRIDAS = [
    ('Máximo Muguruza', 1, '2026-09-11', 'resultados/v1/e6_maximo_muguruza.csv'),
    ('Joaquín Maya',    1, '2026-09-11', 'resultados/v1/descartadas/e6_joaquin_maya_corrida1_2026-09-11_1421.csv'),
    ('Joaquín Maya',    2, '2026-09-11', 'resultados/v1/descartadas/e6_joaquin_maya_corrida2_2026-09-11_1736.csv'),
    ('Joaquín Maya',    3, '2026-09-14', 'resultados/v1/e6_joaquin_maya.csv'),
    ('Máximo Muguruza', 2, '2026-09-14', 'resultados/ronda2/e6_maximo_muguruza.csv'),
    ('Joaquín Maya',    4, '2026-09-14', 'resultados/ronda2/e6_joaquin_maya.csv'),
]


def titulo(t):
    print()
    print('=' * 76)
    print(' ' + t)
    print('=' * 76)


def acuerdo(A, B):
    ids = sorted(set(A) & set(B), key=int)
    pares = [(A[i]['nivel'], B[i]['nivel']) for i in ids]
    po, pe, k = kappa(pares)
    return len(ids), sum(a == b for a, b in pares), po, pe, k


def main():
    titulo('1. CORRIDAS Y CONTROL DE VALIDEZ (mediana >= %.0f s por ítem)' % UMBRAL_SEG)
    validas = []
    for nombre, n, fecha, ruta in CORRIDAS:
        D = leer(os.path.join(BASE, ruta))
        segs = [v['seg'] for v in D.values()]
        med = mediana(segs)
        ok = med >= UMBRAL_SEG
        print('  %-16s corrida %d  %s  n=%-2d  mediana %4.1f s  <3 s: %-2d  %s'
              % (nombre, n, fecha, len(D), med, sum(s < 3 for s in segs), 'VÁLIDA' if ok else 'inválida'))
        if ok:
            validas.append((nombre, n, D))
    print('\n  %d de %d corridas válidas.' % (len(validas), len(CORRIDAS)))

    titulo('2. ACUERDO ENTRE EVALUADORES DISTINTOS (todas las combinaciones válidas)')
    for (na, ca, A), (nb, cb, B) in combinations(validas, 2):
        if na == nb:
            continue
        n, iguales, po, pe, k = acuerdo(A, B)
        print('  %s %d × %s %d: %d de %d coinciden  Po = %.3f  Pe = %.3f  κ = %.3f (%s)'
              % (na, ca, nb, cb, iguales, n, po, pe, k, landis_koch(k)))

    titulo('3. ACUERDO DE CADA EVALUADOR CONSIGO MISMO')
    hubo = False
    for (na, ca, A), (nb, cb, B) in combinations(validas, 2):
        if na != nb:
            continue
        hubo = True
        n, iguales, po, pe, k = acuerdo(A, B)
        print('  %s, corridas %d y %d: repite su nivel en %d de %d  Po = %.3f  κ = %.3f (%s)'
              % (na, ca, cb, iguales, n, po, k, landis_koch(k)))
    if not hubo:
        print('  ningún evaluador tiene dos corridas válidas')


if __name__ == '__main__':
    main()
