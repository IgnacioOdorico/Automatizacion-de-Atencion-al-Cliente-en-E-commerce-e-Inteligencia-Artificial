# -*- coding: utf-8 -*-
"""E6 — Evaluacion de la correccion del contenido de las respuestas de tipo FAQ.

Es el procedimiento que el Capitulo 7 de la tesis deja especificado y que el
trabajo todavia no habia ejecutado. Se cumple al pie de la letra:

  - se extraen de `interactions` las respuestas efectivamente entregadas,
  - se restringe la muestra a los mensajes clasificados como FAQ (n = 45),
  - las juzgan DOS evaluadores independientes contra las 23 entradas de la base
    de conocimiento del Anexo D,
  - con una rubrica de TRES niveles,
  - y se reporta el acuerdo con el mismo kappa de Cohen que se uso para el
    conjunto de etiquetas de referencia.

Este guion genera un archivo HTML por evaluador. Cada uno recibe la muestra en
un ORDEN DISTINTO (semilla propia) para que no puedan compararse por posicion,
y escribe su propio CSV. Igual que en el etiquetado de intenciones, se registra
el tiempo por item: es el control forense que invalido la primera ronda de
aquel experimento y corresponde repetirlo aca.
"""
import sys
import io
import os
import csv
import json
import random
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(BASE, '..', '..'))

EVALUADORES = [
    ('maximo_muguruza',  'Máximo Muguruza',  20260909),
    ('joaquin_maya',     'Joaquín Maya',     20260910),
]

NIVELES = [
    ('A', 'Consistente con la política',
     'La respuesta coincide con lo que dice la base de conocimiento de TechStore.'),
    ('B', 'Genérica pero no contradictoria',
     'La respuesta es correcta para un e-commerce cualquiera, pero no afirma nada '
     'que esté en la base de conocimiento; tampoco la contradice.'),
    ('C', 'Contradice la política vigente',
     'La respuesta afirma algo que la base de conocimiento dice de otra manera, '
     'o inventa una política que la tienda no tiene.'),
]


# ---------------------------------------------------------------- las 23 FAQ
def leer_faqs(ruta):
    txt = open(ruta, encoding='utf-8').read()
    m = re.search(r"INSERT INTO faq_responses \(question, answer, category\) VALUES"
                  r"(.*?)(?:ON CONFLICT|;)\s*\n", txt, re.S)
    if not m:
        return []
    return [(q.replace("''", "'"), a.replace("''", "'"), c)
            for q, a, c in re.findall(
                r"\(\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*,\s*'((?:[^']|'')*)'\s*\)",
                m.group(1))]


faqs = (leer_faqs(os.path.join(RAIZ, 'init_simple.sql'))
        + leer_faqs(os.path.join(RAIZ, 'seed_expand.sql')))
assert len(faqs) == 23, 'se esperaban 23 FAQ, se leyeron %d' % len(faqs)

# ------------------------------------------------------------ las respuestas
with io.open(os.path.join(BASE, 'faq_respuestas.csv'), encoding='utf-8') as f:
    filas = list(csv.DictReader(f))
assert filas, 'faq_respuestas.csv vacio'
for r in filas:
    assert (r.get('ai_response') or '').strip(), 'interaccion %s sin respuesta' % r['id']

print('base de conocimiento : %d entradas, %d categorías'
      % (len(faqs), len({c for _, _, c in faqs})))
print('respuestas a evaluar : %d' % len(filas))
print()

PLANTILLA = u"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>E6 — Evaluación de respuestas · __NOMBRE__</title>
<style>
 :root{--bg:#12131a;--card:#1c1e28;--bd:#2e3140;--fg:#e8eaf2;--mut:#9aa0b5;
       --a:#4ea87a;--b:#c9a227;--c:#c4544f;--ac:#6f8cff}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif}
 .wrap{max-width:820px;margin:0 auto;padding:28px 20px 80px}
 h1{font-size:21px;margin:0 0 4px} h2{font-size:18px}
 .sub{color:var(--mut);font-size:14px;margin-bottom:22px}
 .card{background:var(--card);border:1px solid var(--bd);border-radius:12px;
       padding:18px 20px;margin-bottom:16px}
 .rot{font-size:12px;letter-spacing:.09em;text-transform:uppercase;
      color:var(--mut);margin-bottom:7px}
 .msg{font-size:17px}
 .resp{font-size:16px;white-space:pre-wrap}
 .btns{display:grid;gap:10px;margin-top:6px}
 button{width:100%;text-align:left;padding:13px 16px;border-radius:10px;
        border:1px solid var(--bd);background:#232634;color:var(--fg);
        font:inherit;cursor:pointer;transition:.12s}
 button:hover{border-color:var(--ac);background:#282c3c}
 button b{display:block;font-size:15px}
 button span{color:var(--mut);font-size:13.5px}
 .kA b{color:var(--a)} .kB b{color:var(--b)} .kC b{color:var(--c)}
 .prog{height:5px;background:#232634;border-radius:3px;overflow:hidden;margin-bottom:20px}
 .prog i{display:block;height:100%;background:var(--ac);transition:.25s}
 details{background:var(--card);border:1px solid var(--bd);border-radius:12px;
         padding:12px 18px;margin-bottom:16px}
 summary{cursor:pointer;font-weight:600}
 table{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}
 th,td{border:1px solid var(--bd);padding:7px 9px;text-align:left;vertical-align:top}
 th{color:var(--mut);font-weight:600}
 .dl{display:inline-block;margin-top:14px;padding:12px 20px;background:var(--ac);
     color:#fff;border-radius:9px;text-decoration:none;font-weight:600}
 .ini{padding:13px 22px;font-size:16px;font-weight:600;background:var(--ac);
      color:#fff;border:0;width:auto}
 code{background:#232634;padding:1px 6px;border-radius:5px;font-size:13.5px}
</style></head><body><div class="wrap" id="app"></div>
<script>
const EVALUADOR = "__SLUG__";
const NOMBRE    = "__NOMBRE__";
const FAQS      = __FAQS__;
const DATOS     = __DATOS__;
const NIVELES   = __NIVELES__;

const app = document.getElementById('app');
let i = 0, res = [], t0 = 0;
const CLAVE = 'e6_avance_' + EVALUADOR;
const MITAD = Math.ceil(DATOS.length / 2);
let pausaMostrada = false;

function guardar(){
  try { localStorage.setItem(CLAVE, JSON.stringify({i:i, res:res, pausa:pausaMostrada})); } catch(e){}
}
function leerAvance(){
  try { const v = localStorage.getItem(CLAVE); return v ? JSON.parse(v) : null; } catch(e){ return null; }
}
function borrarAvance(){
  try { localStorage.removeItem(CLAVE); } catch(e){}
}
function reanudar(){
  const a = leerAvance();
  if(!a){ return arrancar(); }
  i = a.i; res = a.res; pausaMostrada = !!a.pausa; render();
}

function tablaFaqs(){
  return `<details><summary>Base de conocimiento de TechStore — las 23 entradas (consultala siempre que dudes)</summary>
    <table><tr><th>Categoría</th><th>Pregunta</th><th>Respuesta oficial</th></tr>
    ${FAQS.map(f=>`<tr><td>${f.c}</td><td>${f.q}</td><td>${f.a}</td></tr>`).join('')}
    </table></details>`;
}

function intro(){
  app.innerHTML = `<h1>Evaluación de respuestas del chatbot</h1>
  <div class="sub">Evaluador: <b>${NOMBRE}</b> · ${DATOS.length} respuestas</div>
  <div class="card">
    <p>Vas a ver <b>${DATOS.length} consultas reales de clientes</b> con la respuesta que
    dio el chatbot. Tu tarea es una sola: decidir si esa respuesta <b>se corresponde con
    la política real de TechStore</b>, que está en la tabla de acá abajo.</p>
    <p><b>No evalúes</b> si la respuesta es simpática, si está bien redactada ni si el
    cliente quedaría contento. Eso no se mide acá. Lo único que importa es si lo que
    afirma es lo que la tienda dice.</p>
    <p>Los tres niveles:</p>
    <table><tr><th>Nivel</th><th>Cuándo</th></tr>
    ${NIVELES.map(n=>`<tr><td><b>${n[0]} — ${n[1]}</b></td><td>${n[2]}</td></tr>`).join('')}
    </table>
    <p style="margin-top:14px"><b>La diferencia entre A y B es la clave del experimento.</b>
    Si la respuesta dice algo que <i>podría</i> ser cierto en cualquier tienda pero que la
    base de conocimiento no afirma, es <b>B</b>, no A. Reservá la <b>A</b> para cuando la
    respuesta se apoya en algo que efectivamente está en la tabla.</p>
    <p>Tomate el tiempo que necesites: se registra cuánto tardás en cada una, y una
    evaluación demasiado rápida se descarta por inválida.</p>
  </div>
  ${tablaFaqs()}
  ${(() => { const a = leerAvance();
     return (a && a.i > 0 && a.i < DATOS.length)
       ? `<div class="card"><p>Tenés una evaluación empezada: vas por la respuesta <b>${a.i + 1} de ${DATOS.length}</b>.
          Tu avance quedó guardado.</p>
          <button class="ini" onclick="reanudar()">Seguir desde la ${a.i + 1}</button></div>`
       : `<button class="ini" onclick="arrancar()">Empezar</button>`; })()}`;
}

function arrancar(){ i=0; res=[]; pausaMostrada=false; borrarAvance(); render(); }

function render(){
  if(i>=DATOS.length) return fin();
  if(i === MITAD && !pausaMostrada){
    pausaMostrada = true; guardar();
    app.innerHTML = `<h1>Llegaste a la mitad</h1>
    <div class="card">
      <p>Evaluaste <b>${i} de ${DATOS.length}</b>. <b>Es un buen momento para parar.</b></p>
      <p>Cotejar respuestas contra la tabla cansa, y una evaluación cansada se nota en los
      tiempos. Si querés, cerrá esta pestaña y seguí más tarde o mañana: tu avance quedó
      guardado y vas a retomar exactamente desde la ${i + 1}.</p>
      <p>Si preferís seguir ahora, tomate un par de minutos antes.</p>
      <button class="ini" onclick="render()">Seguir con la ${i + 1}</button>
    </div>`;
    window.scrollTo(0,0);
    return;
  }
  const d = DATOS[i]; t0 = Date.now();
  app.innerHTML = `<h1>Evaluación de respuestas del chatbot</h1>
  <div class="sub">${NOMBRE} · ${i+1} de ${DATOS.length}</div>
  <div class="prog"><i style="width:${(i/DATOS.length*100).toFixed(1)}%"></i></div>
  <div class="card"><div class="rot">Consulta del cliente</div>
    <div class="msg">${d.m}</div></div>
  <div class="card"><div class="rot">Respuesta que dio el chatbot</div>
    <div class="resp">${d.r}</div></div>
  <div class="btns">
    ${NIVELES.map(n=>`<button class="k${n[0]}" onclick="elegir('${n[0]}')">
        <b>${n[0]} — ${n[1]}</b><span>${n[2]}</span></button>`).join('')}
  </div>
  ${tablaFaqs()}`;
  window.scrollTo(0,0);
}

function elegir(nivel){
  res.push({id:DATOS[i].id, nivel:nivel, segundos:((Date.now()-t0)/1000).toFixed(1)});
  i++; guardar(); render();
}

function fin(){
  const csv = "id,nivel,segundos\\n" + res.map(r=>`${r.id},${r.nivel},${r.segundos}`).join("\\n");
  const url = URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const tot = res.reduce((a,r)=>a+parseFloat(r.segundos),0);
  app.innerHTML = `<h1>Listo, ${NOMBRE}</h1>
  <div class="card"><p>Evaluaste las <b>${res.length}</b> respuestas en
  ${(tot/60).toFixed(1)} minutos (${(tot/res.length).toFixed(1)} s por respuesta en promedio).</p>
  <p>Descargá el archivo y pasáselo al equipo. <b>No lo compares con el del otro
  evaluador</b>: el acuerdo entre ambos es justamente lo que se mide.</p>
  <a class="dl" href="${url}" download="e6_${EVALUADOR}.csv" onclick="setTimeout(borrarAvance, 1500)">Descargar resultado</a></div>`;
}

intro();
</script></body></html>
"""

faqs_js = json.dumps([{'q': q, 'a': a, 'c': c} for q, a, c in faqs], ensure_ascii=False)
niveles_js = json.dumps([[k, t, d] for k, t, d in NIVELES], ensure_ascii=False)

for slug, nombre, semilla in EVALUADORES:
    muestra = [{'id': r['id'], 'm': r['message'], 'r': r['ai_response']} for r in filas]
    random.Random(semilla).shuffle(muestra)
    html = (PLANTILLA
            .replace('__SLUG__', slug)
            .replace('__NOMBRE__', nombre)
            .replace('__FAQS__', faqs_js)
            .replace('__DATOS__', json.dumps(muestra, ensure_ascii=False))
            .replace('__NIVELES__', niveles_js))
    destino = os.path.join(BASE, 'etiquetar_e6_%s.html' % slug)
    io.open(destino, 'w', encoding='utf-8').write(html)
    print('  %-18s -> %s  (%d items, semilla %d, primer id %s)'
          % (nombre, os.path.basename(destino), len(muestra), semilla, muestra[0]['id']))

print()
print('Los dos archivos llevan la MISMA muestra en ORDEN DISTINTO.')
print('Cada evaluador abre el suyo, lo completa y descarga su CSV a resultados/.')
