# -*- coding: utf-8 -*-
"""E6 — Verificación automática de los datos concretos de las respuestas FAQ.

Complementa la evaluación por jueces, que no alcanzó un acuerdo aceptable. No
requiere juicio: extrae de cada respuesta los DATOS CONCRETOS (una cifra con su
unidad) y comprueba si cada uno figura en alguna de las 23 entradas de la base
de conocimiento, con la misma cifra y la misma unidad.

Qué cuenta como dato concreto: una cifra o un rango de cifras seguido de una
unidad de la lista cerrada UNIDADES (días, días hábiles, horas, horas hábiles,
meses, semanas, años, cuotas, minutos, %). Un rango se escribe «1-3», «1 a 3»
o «1 y 3»; «de 9 a 18 hs» es un rango en horas.

Clasificación de cada dato, en este orden:
  respaldado     existe en la base un dato con la misma unidad que contiene
                 todas sus cifras («3 días hábiles» está respaldado por «1-3
                 días hábiles»; «3 días» no, porque cambia la unidad).
  eco            no está en la base, pero sus cifras ya estaban en el mensaje
                 del cliente: repetirlas no es afirmar nada sobre la tienda.
  no respaldado  ninguna de las dos cosas.

Límites, que se declaran junto al resultado:
  - no alcanza a las afirmaciones sin cifra (un servicio que la tienda no presta);
  - no controla el contexto: un dato presente en la base pero usado para otra
    cosa cuenta como respaldado.
Por eso el resultado es una COTA INFERIOR de lo que las respuestas agregan.

La regla se fijó con conocimiento del corpus. Se publica con este guion para
que cualquiera pueda reproducirla o discutirla.

Uso:
    python verificar_datos_e6.py             # corre sobre las 45 respuestas
    python verificar_datos_e6.py --pruebas   # corre las pruebas de la regla
"""
import sys
import io
import os
import re
import csv
import math

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))

# (patrón, unidad canónica). El orden importa: la unidad compuesta va primero.
UNIDADES = [
    (r'd[ií]as?\s+h[aá]biles', 'días hábiles'),
    (r'(?:horas?|hs\.?)\s+h[aá]biles', 'horas hábiles'),
    (r'd[ií]as?', 'días'),
    (r'horas?|hs\.?', 'horas'),
    (r'meses|mes', 'meses'),
    (r'semanas?', 'semanas'),
    (r'a[nñ]os?', 'años'),
    (r'cuotas?', 'cuotas'),
    (r'minutos?', 'minutos'),
    (r'%', '%'),
]
NUM = r'(\d+)'
DATO = re.compile(
    NUM + r'(?:\s*(?:-|–|a|y|al)\s*' + NUM + r')?\s*(' +
    '|'.join(p for p, _ in UNIDADES) + r')(?![A-Za-zÁÉÍÓÚáéíóúÑñ])',
    re.I)


def canonica(texto_unidad):
    for patron, nombre in UNIDADES:
        if re.fullmatch(patron, texto_unidad.strip(), re.I):
            return nombre
    raise ValueError('unidad no reconocida: %r' % texto_unidad)


def extraer(texto):
    """Devuelve [(cifras, unidad, texto_original)] en orden de aparición."""
    t = texto.replace('**', '')
    salida = []
    for m in DATO.finditer(t):
        cifras = tuple(int(x) for x in (m.group(1), m.group(2)) if x is not None)
        salida.append((cifras, canonica(m.group(3)), m.group(0).strip()))
    return salida


def clasificar(cifras, unidad, datos_base, mensaje):
    """datos_base: [(cifras, unidad, n_entrada)]. Devuelve (estado, entradas)."""
    entradas = sorted({n for c, u, n in datos_base if u == unidad and set(cifras) <= set(c)})
    if entradas:
        return 'respaldado', entradas
    en_mensaje = {int(x) for x in re.findall(r'\d+', mensaje)}
    if set(cifras) <= en_mensaje:
        return 'eco', []
    return 'no respaldado', []


def leer_faqs():
    def leer(ruta):
        txt = io.open(ruta, encoding='utf-8').read()
        m = re.search(r"INSERT INTO faq_responses \(question, answer, category\) VALUES"
                      r"(.*?)(?:ON CONFLICT|;)\s*\n", txt, re.S)
        return [(q.replace("''", "'"), a.replace("''", "'"))
                for q, a, _ in re.findall(
                    r"\(\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*\)",
                    m.group(1))]
    faqs = leer(os.path.join(RAIZ, 'init_simple.sql')) + leer(os.path.join(RAIZ, 'seed_expand.sql'))
    assert len(faqs) == 23, 'se esperaban 23 entradas, hay %d' % len(faqs)
    return faqs


def wilson(x, n, z=1.959964):
    p = x / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - medio), min(1.0, centro + medio)


# ------------------------------------------------------------------ pruebas
def pruebas():
    fallas = []

    def igual(rot, obtenido, esperado):
        if obtenido != esperado:
            fallas.append('%s: se obtuvo %r, se esperaba %r' % (rot, obtenido, esperado))

    solo = lambda t: [(c, u) for c, u, _ in extraer(t)]
    igual('rango con guion', solo('Tardan 1-3 días hábiles.'), [((1, 3), 'días hábiles')])
    igual('rango con y', solo('entre 1 y 3 días hábiles'), [((1, 3), 'días hábiles')])
    igual('franja horaria', solo('de lunes a viernes de 9 a 18 hs.'), [((9, 18), 'horas')])
    igual('hs pegado y hábiles', solo('en 24hs hábiles'), [((24,), 'horas hábiles')])
    igual('cuotas', solo('hasta 12 cuotas sin interés'), [((12,), 'cuotas')])
    igual('porcentaje', solo('somos 100% online'), [((100,), '%')])
    igual('días no es días hábiles', solo('30 días desde la recepción'), [((30,), 'días')])
    igual('dos datos en una frase', solo('2 horas; después, 5 días hábiles'),
          [((2,), 'horas'), ((5,), 'días hábiles')])
    igual('marcador de lista no es dato', solo('1. Tarjeta de crédito'), [])
    igual('alias con dígito no es dato', solo('¡Hola Anotador E2!'), [])
    igual('cifra sin unidad no es dato', solo('pedido 4521 confirmado'), [])
    igual('palabra que empieza como unidad', solo('3 mesas'), [])

    base = [((1, 3), 'días hábiles', 2), ((3, 7), 'días hábiles', 2), ((12,), 'cuotas', 7)]
    igual('contenido en un rango', clasificar((3,), 'días hábiles', base, ''), ('respaldado', [2]))
    igual('rango exacto', clasificar((1, 3), 'días hábiles', base, ''), ('respaldado', [2]))
    igual('cambia la unidad', clasificar((3,), 'días', base, ''), ('no respaldado', []))
    igual('cifras ausentes', clasificar((5, 10), 'días hábiles', base, ''), ('no respaldado', []))
    igual('eco del cliente', clasificar((8,), 'días', base, 'ya lleva 8 dias'), ('eco', []))
    igual('la base gana al eco', clasificar((12,), 'cuotas', base, 'tienen 12 cuotas?'),
          ('respaldado', [7]))

    lo, hi = wilson(2, 17)
    igual('Wilson 2/17', (round(lo, 4), round(hi, 4)), (0.0329, 0.3434))  # forma cerrada: (2np + z² ∓ z·√(z² + 4np(1−p))) / 2(n + z²)

    if fallas:
        print('PRUEBAS: %d FALLAS' % len(fallas))
        for f in fallas:
            print('  - ' + f)
        sys.exit(1)
    print('PRUEBAS: todas pasan')


# ------------------------------------------------------------------ corrida
def main():
    faqs = leer_faqs()
    datos_base = [(c, u, n) for n, (_, a) in enumerate(faqs, 1) for c, u, _ in extraer(a)]
    with io.open(os.path.join(BASE, 'faq_respuestas.csv'), encoding='utf-8') as f:
        filas = sorted(csv.DictReader(f), key=lambda r: int(r['id']))
    assert len(filas) == 45

    print('Base de conocimiento: %d entradas, %d datos concretos' % (len(faqs), len(datos_base)))
    print()
    registros = []
    residuales = []
    for r in filas:
        texto = r['ai_response']
        datos = extraer(texto)
        consumido = re.sub(DATO, ' ', texto.replace('**', ''))
        for m in re.finditer(r'\d+', consumido):
            antes = consumido[max(0, m.start() - 1): m.start()]
            despues = consumido[m.end(): m.end() + 2]
            if antes.isalpha():
                tipo = 'parte de un identificador (p. ej. «E2»)'
            elif despues.startswith('.') and (not antes or antes.isspace()):
                tipo = 'marcador de lista'
            else:
                tipo = 'otro'
            residuales.append((r['id'], tipo, consumido[max(0, m.start() - 15): m.end() + 15].replace('\n', ' ')))
        for cifras, unidad, original in datos:
            estado, entradas = clasificar(cifras, unidad, datos_base, r['message'])
            registros.append({
                'id': r['id'], 'consulta': r['message'], 'dato': original,
                'unidad': unidad, 'estado': estado,
                'entradas': '|'.join(map(str, entradas)),
                'pregunta_entrada': ' / '.join(faqs[n - 1][0] for n in entradas),
            })

    print('%-5s %-10s %-30s %-15s %s' % ('id', 'estado', 'dato', 'entrada', 'consulta'))
    for x in registros:
        print('%-5s %-10s %-30s %-15s %s' % (x['id'], x['estado'][:10], x['dato'][:30],
                                             x['entradas'] or '—', x['consulta'][:48]))

    print()
    print('Dígitos que no forman un dato (revisión de completitud):')
    tipos = {}
    for _, tipo, _ in residuales:
        tipos[tipo] = tipos.get(tipo, 0) + 1
    for tipo, n in sorted(tipos.items()):
        print('  %-42s %d' % (tipo, n))
    otros = [(i, ctx) for i, tipo, ctx in residuales if tipo == 'otro']
    for i, ctx in otros:
        print('  [%s] …%s…  <- REVISAR' % (i, ctx.strip()))
    if not otros:
        print('  ninguna cifra quedó sin clasificar')

    con_datos = sorted({x['id'] for x in registros}, key=int)
    no_resp = sorted({x['id'] for x in registros if x['estado'] == 'no respaldado'}, key=int)
    cuenta = {e: sum(x['estado'] == e for x in registros) for e in ('respaldado', 'eco', 'no respaldado')}
    lo, hi = wilson(len(no_resp), len(con_datos)) if con_datos else (0, 0)
    lo45, hi45 = wilson(len(no_resp), len(filas))

    print()
    print('=' * 72)
    print(' RESULTADO')
    print('=' * 72)
    print('  respuestas evaluadas ................... %d' % len(filas))
    print('  respuestas con al menos un dato ........ %d' % len(con_datos))
    print('  datos concretos ........................ %d  (respaldados %d · eco %d · no respaldados %d)'
          % (len(registros), cuenta['respaldado'], cuenta['eco'], cuenta['no respaldado']))
    print('  respuestas con algún dato no respaldado  %d de %d (%.1f %%; IC 95 %% de Wilson %.1f %% a %.1f %%)'
          % (len(no_resp), len(con_datos), 100 * len(no_resp) / len(con_datos), 100 * lo, 100 * hi))
    print('  sobre las 45 respuestas ................ %d de %d (%.1f %%; IC 95 %% %.1f %% a %.1f %%)'
          % (len(no_resp), len(filas), 100 * len(no_resp) / len(filas), 100 * lo45, 100 * hi45))
    print('  ids con dato no respaldado ............. %s' % ', '.join(no_resp))

    destino = os.path.join(BASE, 'resultados', 'verificacion_datos.csv')
    with io.open(destino, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, ['id', 'consulta', 'dato', 'unidad', 'estado', 'entradas', 'pregunta_entrada'])
        w.writeheader()
        w.writerows(registros)
    print()
    print('Detalle por dato: resultados/verificacion_datos.csv')


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if '--pruebas' in sys.argv:
        pruebas()
    else:
        main()
