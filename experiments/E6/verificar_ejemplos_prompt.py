# -*- coding: utf-8 -*-
"""E6 — Los ejemplos del prompt medido frente a la base de conocimiento.

Aplica a las siete respuestas de ejemplo del prompt de la configuración vigente
(experiments/E8/prompts/C1.txt, idéntico al medido) la MISMA regla con que
verificar_datos_e6.py verifica las respuestas del sistema: extrae los datos
concretos (cifra con unidad) y comprueba si cada uno figura en la base.

Un ejemplo del prompt que afirma un dato ausente de la base le enseña al modelo
ese dato, en contra de la instrucción del propio prompt de usar exclusivamente
la base. Los límites son los de la regla: no alcanza a las afirmaciones sin
cifra, como un compromiso de plazo sin número («hoy mismo»).

Uso:
    python verificar_ejemplos_prompt.py             # corre sobre los siete ejemplos
    python verificar_ejemplos_prompt.py --pruebas   # corre las pruebas
"""
import sys
import io
import os
import re
import json

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
sys.path.insert(0, BASE)
from verificar_datos_e6 import extraer, clasificar, leer_faqs  # noqa: E402

PROMPT = os.path.join(RAIZ, 'experiments', 'E8', 'prompts', 'C1.txt')


def leer_ejemplos(texto):
    """Pares (mensaje, respuesta) del bloque EJEMPLOS, que termina donde empieza el siguiente bloque."""
    bloque = texto.split('## EJEMPLOS', 1)[1].split('\n## ', 1)[0]
    ejemplos = []
    for m in re.finditer(r'^Mensaje: "(.*?)" \| Cliente: (.*?)\n→ (\{.*\})$', bloque, re.M):
        ejemplos.append({'mensaje': m.group(1), 'cliente': m.group(2),
                         'respuesta': json.loads(m.group(3))['respuesta']})
    return ejemplos


def verificar(ejemplos, datos_base):
    filas = []
    for e in ejemplos:
        for cifras, unidad, original in extraer(e['respuesta']):
            estado, entradas = clasificar(cifras, unidad, datos_base, e['mensaje'])
            filas.append({'mensaje': e['mensaje'], 'dato': original, 'unidad': unidad,
                          'estado': estado, 'entradas': entradas})
    return filas


def main():
    faqs = leer_faqs()
    datos_base = [(c, u, n) for n, (_, a) in enumerate(faqs, 1) for c, u, _ in extraer(a)]
    ejemplos = leer_ejemplos(io.open(PROMPT, encoding='utf-8').read())
    assert len(ejemplos) == 7, 'se esperaban 7 ejemplos, hay %d' % len(ejemplos)
    filas = verificar(ejemplos, datos_base)
    print('Ejemplos del prompt de la configuración vigente: %d' % len(ejemplos))
    print('Ejemplos con al menos un dato concreto: %d' % len({f['mensaje'] for f in filas}))
    print()
    print('%-14s %-24s %-22s %s' % ('estado', 'dato', 'entrada de la base', 'mensaje del ejemplo'))
    for f in filas:
        entrada = ' / '.join(faqs[n - 1][0] for n in f['entradas']) or '—'
        print('%-14s %-24s %-22s %s' % (f['estado'], f['dato'], entrada[:22], f['mensaje'][:60]))
    cuenta = {e: sum(f['estado'] == e for f in filas) for e in ('respaldado', 'eco', 'no respaldado')}
    print()
    print('datos concretos: %d (respaldados %d · eco %d · no respaldados %d)'
          % (len(filas), cuenta['respaldado'], cuenta['eco'], cuenta['no respaldado']))


# ------------------------------------------------------------------ pruebas
def pruebas():
    fallas = []

    def igual(rot, obtenido, esperado):
        if obtenido != esperado:
            fallas.append('%s: se obtuvo %r, se esperaba %r' % (rot, obtenido, esperado))

    texto = ('## EJEMPLOS\n\nMensaje: "hola" | Cliente: Ana\n'
             '→ {"intent": "FAQ", "order_id": null, "urgente": false, "respuesta": "Tardan 3 y 5 días hábiles."}\n\n'
             'Mensaje: "chau" | Cliente: desconocido\n'
             '→ {"intent": "GENERAL", "order_id": null, "urgente": false, "respuesta": "¡Hasta luego!"}\n\n'
             '## MENSAJE DEL CLIENTE\nMensaje: {{ $json.message }}\n')
    ej = leer_ejemplos(texto)
    igual('dos ejemplos', len(ej), 2)
    igual('mensaje del primero', ej[0]['mensaje'], 'hola')
    igual('respuesta del primero', ej[0]['respuesta'], 'Tardan 3 y 5 días hábiles.')
    igual('no toma el bloque del mensaje del cliente', [e['mensaje'] for e in ej], ['hola', 'chau'])

    base = [((3, 7), 'días hábiles', 2), ((12,), 'meses', 4)]
    igual('dato ausente de la base', verificar(ej, base)[0]['estado'], 'no respaldado')
    igual('ejemplo sin datos no aporta filas', [r['mensaje'] for r in verificar(ej, base)], ['hola'])

    reales = leer_ejemplos(io.open(PROMPT, encoding='utf-8').read())
    igual('el prompt medido tiene siete ejemplos', len(reales), 7)

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
