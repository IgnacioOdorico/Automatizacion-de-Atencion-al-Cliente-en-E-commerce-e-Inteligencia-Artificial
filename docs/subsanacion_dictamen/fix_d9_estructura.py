# -*- coding: utf-8 -*-
"""Revisión de estructura del 17/09/2026 (verificar_estructura.py).

  - Numeración de páginas en el pie (sin número en la portada) y encabezado sin el «|» suelto.
  - Sin las reglas horizontales decorativas, que separaban solo algunos capítulos.
  - El índice, los listados y el glosario empiezan página; listados y glosario pasan a
    primer nivel (antes colgaban del ABSTRACT) y se renombran «Listado de figuras» y
    «Listado de tablas».
  - Sin secciones con una única subsección: 4.1.1 y 4.5.1 se integran a 4.1 y 4.5, y
    5.4.1 pasa a ser 5.5; se actualizan todas las remisiones.
  - Títulos con mayúscula solo inicial (Capítulo 1, §5.1 y anexos A a G).
  - Figura 8: la descripción de los listados coincide con su epígrafe.

NO es idempotente. Se ejecuta desde la raíz del repositorio.
"""
import re
import sys

sys.path.insert(0, 'docs/subsanacion_dictamen')
from kit5 import abrir, Kit, qn, OxmlElement, replace_everywhere  # noqa: E402
from lxml import etree  # noqa: E402

d = abrir()
k = Kit(d)
W = qn

# ------------------------------------------------------------------ encabezado y pie
sec = d.sections[0]
for p in sec.header.paragraphs:
    for r in p.runs:
        r.text = ''
sec.different_first_page_header_footer = True
pie = sec.footer.paragraphs[0]
pie.alignment = 1   # centrado


def campo(p, instruccion):
    for tipo, texto in (('begin', None), (None, instruccion), ('separate', None), (None, '1'), ('end', None)):
        r = OxmlElement('w:r')
        if tipo:
            fc = OxmlElement('w:fldChar')
            fc.set(W('w:fldCharType'), tipo)
            r.append(fc)
        elif texto == instruccion:
            it = OxmlElement('w:instrText')
            it.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            it.text = instruccion
            r.append(it)
        else:
            t = OxmlElement('w:t')
            t.text = texto
            r.append(t)
        p._p.append(r)


campo(pie, ' PAGE ')
k.hechos += 2

# ------------------------------------------------------------------ reglas horizontales
body = d.element.body
reglas = [el for el in body.iterchildren() if b'o:hr' in etree.tostring(el)]
assert len(reglas) == 7, len(reglas)
for el in reglas:
    assert not ''.join(el.itertext()).strip()
    body.remove(el)
k.hechos += 1


def salto_antes(p_el):
    ppr = p_el.find(W('w:pPr'))
    if ppr is None:
        ppr = OxmlElement('w:pPr')
        p_el.insert(0, ppr)
    if ppr.find(W('w:pageBreakBefore')) is None:
        nuevo = OxmlElement('w:pageBreakBefore')
        estilo = ppr.find(W('w:pStyle'))
        (estilo.addnext(nuevo) if estilo is not None else ppr.insert(0, nuevo))


# ------------------------------------------------------------------ índice, listados y glosario
indice = [el for el in body.iterchildren() if el.tag == W('w:sdt') and ''.join(el.itertext()).startswith('ÍNDICE')]
assert len(indice) == 1
primer_p = indice[0].find('.//' + W('w:p'))
assert ''.join(t.text or '' for t in primer_p.iter(W('w:t'))).strip() == 'ÍNDICE'
salto_antes(primer_p)
for viejo, nuevo in (('Listado de Figuras', 'Listado de figuras'), ('Listado de Tablas principales', 'Listado de tablas'),
                     ('Glosario de siglas y acrónimos', 'Glosario de siglas y acrónimos')):
    p = [x for x in d.paragraphs if x.text.strip() == viejo]
    assert len(p) == 1, viejo
    p = p[0]
    if nuevo != viejo:
        k.reescribir(p, nuevo)
    p.style = d.styles['Heading 1']
    p.paragraph_format.page_break_before = True
    k.hechos += 1

# ------------------------------------------------------------------ secciones con una única subsección
k.eliminar('4.1.1 Servicios Docker')
k.eliminar('4.5.1 Paneles de los dashboards')
p541 = k.par('5.4.1 Limitaciones observadas')
k.reescribir(p541, '5.5 Limitaciones observadas')
p541.style = d.styles['Heading 2']


def contar(token):
    n = 0
    for p in list(d.paragraphs) + [p for t in d.tables for r in t.rows for c in r.cells for p in c.paragraphs]:
        n += len(re.findall(r'(?<![\d.])' + re.escape(token) + r'(?![\d])', p.text))
    return n


for viejo, nuevo in (('5.4.1', '5.5'), ('4.1.1', '4.1'), ('4.5.1', '4.5')):
    esperado = contar(viejo)
    hechos = replace_everywhere(d, viejo, nuevo)
    assert contar(viejo) == 0 and hechos >= esperado, (viejo, esperado, hechos)
    k.hechos += 1

# ------------------------------------------------------------------ títulos
for viejo, nuevo in (
        ('1.4 Pregunta de Investigación e Hipótesis', '1.4 Pregunta de investigación e hipótesis'),
        ('1.5.1 Objetivo General', '1.5.1 Objetivo general'),
        ('1.5.2 Objetivos Específicos', '1.5.2 Objetivos específicos'),
        ('1.6 Alcance y Limitaciones', '1.6 Alcance y limitaciones'),
        ('5.1 Resultados del Flujo 1 — Pipeline de Órdenes', '5.1 Resultados del Flujo 1 — Pipeline de procesamiento de órdenes'),
        ('Anexo A: Resumen del Schema de Base de Datos', 'Anexo A: Resumen del esquema de la base de datos'),
        ('Anexo B: Configuración Docker Compose', 'Anexo B: Configuración de Docker Compose'),
        ('Anexo C: Catálogo de Productos Seed', 'Anexo C: Catálogo de productos de la carga inicial'),
        ('Anexo D: FAQ predefinidas (base de conocimiento completa)', 'Anexo D: Base de conocimiento completa (preguntas frecuentes)'),
        ('Anexo E: Comandos de Testing', 'Anexo E: Comandos de prueba'),
        ('Anexo F: Lista de Figuras — Implementación de Desarrollo (SIMPLE)', 'Anexo F: Capturas de la implementación de desarrollo'),
        ('Anexo G: Propuesta de Arquitectura de Producción', 'Anexo G: Propuesta de arquitectura de producción')):
    p = [x for x in d.paragraphs if x.text.strip() == viejo and x.style.name.startswith('Heading')]
    assert len(p) == 1, viejo
    k.reescribir(p[0], nuevo)

# ------------------------------------------------------------------ Figura 8 en los listados
cap8 = k.par('Figura 8:').text.strip()[len('Figura 8: '):]
desc8 = cap8.split('. Esas cinco órdenes')[0]
assert desc8 != cap8
for t in d.tables:
    h = [c.text.strip() for c in t.rows[0].cells]
    if len(h) == 3 and h[0] == 'Figura' and h[2] == 'Sección':
        for i, r in enumerate(t.rows):
            if r.cells[0].text.strip() == 'Figura 8':
                k.celda(t, i, 1, desc8)

k.guardar()
