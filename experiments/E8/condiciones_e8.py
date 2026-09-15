# -*- coding: utf-8 -*-
"""E8 — Las cuatro condiciones de prompt y el workflow de cada una.

El prompt medido el 12/08 (versión 4e2d3bc4 del workflow de 14 nodos, idéntico
al del commit f68da9d) tiene, en este orden:

    marca de inicio
    ## IDENTIDAD                      \
    ## TU TAREA                        >  núcleo: presente en todas las condiciones
    ## FORMATO DE RESPUESTA           /
    ## REGLAS DE CLASIFICACIÓN        -> factor R (reglas y ejemplos)
    ## BASE DE CONOCIMIENTO FAQ       -> factor B (base de conocimiento)
    ## REGLAS CRÍTICAS                -> factor R
    ## EJEMPLOS                       -> factor R
    ## MENSAJE DEL CLIENTE + fin      -> presente en todas las condiciones

Diseño factorial 2 x 2 sobre B y R, con el núcleo y el mensaje del cliente
constantes. Solo cambia el texto del prompt de sistema; el resto del workflow
queda idéntico, y eso se verifica.

    C1  B + R   (la configuración principal; debe reproducir el prompt medido)
    C2      R   (sin base)
    C3  B       (sin reglas ni ejemplos)
    C4  -       (solo núcleo y mensaje)

Uso:
    python condiciones_e8.py construir
    python condiciones_e8.py workflow --base base.json --condicion C2 --salida wf.json
    python condiciones_e8.py --pruebas
"""
import sys
import io
import os
import re
import json
import hashlib
import argparse
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))
COMMIT_MEDIDO = 'f68da9d'
ARCHIVO_MEDIDO = 'workflows/Flujo 2 — Chatbot Omnicanal IA.json'
MD5_MEDIDO = 'c11c2fe1cdd4f5c2eedd7e8f9b013c3c'
NODO_IA = 'IA - Motor Decision'

ENCABEZADOS = [
    '## IDENTIDAD',
    '## TU TAREA',
    '## FORMATO DE RESPUESTA (JSON estricto)',
    '## REGLAS DE CLASIFICACIÓN',
    '## BASE DE CONOCIMIENTO FAQ',
    '## REGLAS CRÍTICAS (nunca las violes)',
    '## EJEMPLOS',
    '## MENSAJE DEL CLIENTE',
]
NUCLEO = {'## IDENTIDAD', '## TU TAREA', '## FORMATO DE RESPUESTA (JSON estricto)', '## MENSAJE DEL CLIENTE'}
FACTOR_B = {'## BASE DE CONOCIMIENTO FAQ'}
FACTOR_R = {'## REGLAS DE CLASIFICACIÓN', '## REGLAS CRÍTICAS (nunca las violes)', '## EJEMPLOS'}

CONDICIONES = {
    'C1': {'base': True, 'reglas_y_ejemplos': True},
    'C2': {'base': False, 'reglas_y_ejemplos': True},
    'C3': {'base': True, 'reglas_y_ejemplos': False},
    'C4': {'base': False, 'reglas_y_ejemplos': False},
}


def md5(texto):
    return hashlib.md5(texto.encode('utf-8')).hexdigest()


def prompt_medido():
    raw = subprocess.run(['git', '-C', RAIZ, 'show', '%s:%s' % (COMMIT_MEDIDO, ARCHIVO_MEDIDO)],
                         capture_output=True, check=True).stdout
    w = json.loads(raw.decode('utf-8'))
    nodo = [n for n in w['nodes'] if n['name'] == NODO_IA][0]
    p = nodo['parameters']['messages']['messageValues'][0]['message']
    assert md5(p) == MD5_MEDIDO, 'el prompt de %s no es el medido' % COMMIT_MEDIDO
    return p


def partir(prompt):
    """Devuelve (marca_inicio, [(encabezado, texto_de_la_seccion), ...])."""
    trozos = re.split(r'(?m)^(?=## )', prompt)
    inicio, secciones = trozos[0], trozos[1:]
    assert inicio.startswith('=# --- START ---'), 'falta la marca de inicio con prefijo de expresión'
    pares = [(s.split('\n', 1)[0].rstrip(), s) for s in secciones]
    assert [e for e, _ in pares] == ENCABEZADOS, 'la estructura del prompt cambió: %s' % [e for e, _ in pares]
    assert inicio + ''.join(s for _, s in pares) == prompt, 'partir y unir no reproduce el prompt'
    return inicio, pares


def armar(prompt, condicion):
    inicio, pares = partir(prompt)
    cfg = CONDICIONES[condicion]
    incluidos = []
    for enc, texto in pares:
        if enc in NUCLEO or (enc in FACTOR_B and cfg['base']) or (enc in FACTOR_R and cfg['reglas_y_ejemplos']):
            incluidos.append((enc, texto))
    return inicio + ''.join(t for _, t in incluidos), [e for e, _ in incluidos]


def construir():
    p = prompt_medido()
    os.makedirs(os.path.join(BASE, 'prompts'), exist_ok=True)
    resumen = {'prompt_medido': {'commit': COMMIT_MEDIDO, 'version_n8n': '4e2d3bc4', 'md5': MD5_MEDIDO,
                                 'caracteres': len(p)},
               'condiciones': {}}
    for c in CONDICIONES:
        texto, bloques = armar(p, c)
        if c == 'C1':
            assert texto == p, 'C1 no reproduce el prompt medido'
        io.open(os.path.join(BASE, 'prompts', '%s.txt' % c), 'w', encoding='utf-8', newline='').write(texto)
        resumen['condiciones'][c] = dict(CONDICIONES[c], bloques=bloques, caracteres=len(texto), md5=md5(texto))
        print('%s  %5d caracteres  md5 %s  %s' % (c, len(texto), md5(texto), ' + '.join(
            b.replace('## ', '').split(' (')[0] for b in bloques)))
    json.dump(resumen, io.open(os.path.join(BASE, 'condiciones_e8.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('\nprompts/ y condiciones_e8.json escritos')


def _cargar_workflow(ruta):
    data = json.load(io.open(ruta, encoding='utf-8-sig'))
    return data[0] if isinstance(data, list) else data


def _sin_prompt(w):
    w = json.loads(json.dumps(w))
    for n in w['nodes']:
        if n['name'] == NODO_IA:
            n['parameters']['messages']['messageValues'][0]['message'] = '<PROMPT>'
    for k in ('versionId', 'activeVersionId', 'updatedAt', 'createdAt', 'versionCounter', 'active', 'activeVersion'):
        w.pop(k, None)
    return w


def workflow(base, condicion, salida):
    texto = io.open(os.path.join(BASE, 'prompts', '%s.txt' % condicion), encoding='utf-8', newline='').read()
    esperado = json.load(io.open(os.path.join(BASE, 'condiciones_e8.json'), encoding='utf-8'))['condiciones'][condicion]['md5']
    assert md5(texto) == esperado, 'el archivo de prompt de %s no coincide con condiciones_e8.json' % condicion
    w = _cargar_workflow(base)
    nodos = [n for n in w['nodes'] if n['name'] == NODO_IA]
    assert len(nodos) == 1, 'el workflow base no tiene un único nodo %s' % NODO_IA
    original = json.loads(json.dumps(w))
    nodos[0]['parameters']['messages']['messageValues'][0]['message'] = texto
    assert _sin_prompt(original) == _sin_prompt(w), 'cambió algo más que el prompt'
    json.dump(w, io.open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('%s md5 %s -> %s' % (condicion, esperado, salida))


def pruebas():
    fallas = []

    def ok(rot, cond):
        if not cond:
            fallas.append(rot)

    p = prompt_medido()
    inicio, pares = partir(p)
    ok('partir/unir reproduce el prompt', inicio + ''.join(s for _, s in pares) == p)
    textos = {c: armar(p, c)[0] for c in CONDICIONES}
    ok('C1 es el prompt medido', textos['C1'] == p)
    ok('C2 no tiene la base', '{{ $json.faq_context }}' not in textos['C2'] and '## BASE DE CONOCIMIENTO' not in textos['C2'])
    ok('C2 conserva reglas y ejemplos', '## REGLAS DE CLASIFICACIÓN' in textos['C2'] and '## EJEMPLOS' in textos['C2']
       and '## REGLAS CRÍTICAS' in textos['C2'])
    ok('C3 tiene la base y no las reglas ni los ejemplos', '{{ $json.faq_context }}' in textos['C3']
       and '## REGLAS' not in textos['C3'] and '## EJEMPLOS' not in textos['C3'])
    ok('C4 no tiene base, reglas ni ejemplos', all(x not in textos['C4'] for x in ('## BASE', '## REGLAS', '## EJEMPLOS')))
    for c, t in textos.items():
        ok('%s conserva núcleo y mensaje del cliente' % c, all(h in t for h in NUCLEO))
        ok('%s es expresión de n8n (empieza con =)' % c, t.startswith('='))
        ok('%s cierra con la marca de fin' % c, t.rstrip().endswith('# --- END ---'))
    ok('los largos siguen el orden esperado', len(textos['C1']) > len(textos['C2']) > len(textos['C3']) > len(textos['C4']))
    # el reemplazo en un workflow no toca nada más
    w = {'id': 'X', 'nodes': [{'name': NODO_IA, 'parameters': {'messages': {'messageValues': [{'message': 'viejo'}]}}},
                              {'name': 'Otro', 'parameters': {'a': 1}}]}
    w2 = json.loads(json.dumps(w))
    w2['nodes'][0]['parameters']['messages']['messageValues'][0]['message'] = 'nuevo'
    ok('_sin_prompt ignora solo el prompt', _sin_prompt(w) == _sin_prompt(w2))
    w2['nodes'][1]['parameters']['a'] = 2
    ok('_sin_prompt detecta otro cambio', _sin_prompt(w) != _sin_prompt(w2))
    if fallas:
        print('PRUEBAS: %d FALLAS' % len(fallas))
        for f in fallas:
            print('  - ' + f)
        sys.exit(1)
    print('PRUEBAS: todas pasan')


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', nargs='?', choices=['construir', 'workflow'])
    ap.add_argument('--pruebas', action='store_true')
    ap.add_argument('--base')
    ap.add_argument('--condicion', choices=list(CONDICIONES))
    ap.add_argument('--salida')
    a = ap.parse_args()
    if a.pruebas:
        pruebas()
    elif a.accion == 'construir':
        construir()
    elif a.accion == 'workflow':
        workflow(a.base, a.condicion, a.salida)
    else:
        ap.print_help()
