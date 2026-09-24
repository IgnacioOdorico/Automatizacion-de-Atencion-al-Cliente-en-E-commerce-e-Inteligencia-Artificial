/* ============================================================
   Atendo — landing
   Tres cosas: los contadores en vivo, el chat contra el asistente real y
   los detalles de presentación (nav pegada, aparecer al hacer scroll).

   Nada de innerHTML con texto que no escribimos nosotros: la respuesta del
   asistente la escribe un modelo de lenguaje a partir de lo que tipeó el
   visitante, así que se arma como nodos de texto. Misma regla que el portal.
   ============================================================ */
(function () {
  'use strict';

  var API = '/api';
  var INTERVALO_STATS_MS = 10000;

  // ---------------------------------------------------------------- utilidades

  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }

  /** Español rioplatense: separador de miles con punto. */
  function conMiles(n) {
    return new Intl.NumberFormat('es-AR').format(n);
  }

  /** sessionStorage puede fallar (ventana privada, datos bloqueados): nunca rompe la página. */
  function leerSesion(clave) {
    try { return window.sessionStorage.getItem(clave); } catch (e) { return null; }
  }
  function guardarSesion(clave, valor) {
    try { window.sessionStorage.setItem(clave, valor); } catch (e) { /* sin persistencia */ }
  }

  // ---------------------------------------------------------------- contadores en vivo

  var CAMPOS = ['orders', 'interactions', 'tickets', 'products'];
  var previos = {};

  function pintarEstado(estado, texto) {
    var caja = $('.vivo__estado');
    if (!caja) return;
    caja.setAttribute('data-estado', estado);
    var span = $('[data-texto-estado]', caja);
    if (span) span.textContent = texto;
  }

  function pintarStats(datos) {
    CAMPOS.forEach(function (campo) {
      var nodo = $('[data-stat="' + campo + '"]');
      if (!nodo || typeof datos[campo] !== 'number') return;
      var anterior = previos[campo];
      nodo.textContent = conMiles(datos[campo]);
      if (anterior !== undefined && datos[campo] > anterior) {
        nodo.classList.remove('numero--sube');
        void nodo.offsetWidth; // reinicia la animación
        nodo.classList.add('numero--sube');
      }
      previos[campo] = datos[campo];
    });
  }

  function traerStats() {
    return fetch(API + '/demo/stats', { headers: { Accept: 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error('respuesta ' + r.status);
        return r.json();
      })
      .then(function (datos) {
        pintarStats(datos);
        pintarEstado('vivo', 'En vivo');
      })
      .catch(function () {
        pintarEstado('error', 'Sin conexión');
      });
  }

  // ---------------------------------------------------------------- chat

  var chat = $('[data-chat]');
  var mensajes = $('[data-chat-mensajes]');
  var form = $('[data-chat-form]');
  var entrada = $('[data-chat-entrada]');
  var enviar = $('[data-chat-enviar]');
  var estadoChat = $('[data-chat-estado]');
  var sugerencias = $('[data-chat-sugerencias]');
  var esperando = false;

  /** Identificador opaco de esta pestaña. No es un dato de nadie. */
  function idSesion() {
    var guardado = leerSesion('atendo_sesion');
    if (guardado && /^[a-z0-9]{8,40}$/.test(guardado)) return guardado;
    var nuevo = '';
    var alfabeto = 'abcdefghijklmnopqrstuvwxyz0123456789';
    var bytes = new Uint8Array(16);
    (window.crypto || window.msCrypto).getRandomValues(bytes);
    for (var i = 0; i < bytes.length; i++) nuevo += alfabeto[bytes[i] % alfabeto.length];
    guardarSesion('atendo_sesion', nuevo);
    return nuevo;
  }

  var SESION = idSesion();

  /**
   * El asistente responde en Markdown liviano (`**negrita**`, listas numeradas).
   * Se traduce a nodos: un párrafo por línea en blanco, `<strong>` para la negrita.
   * Todo lo demás viaja como texto plano.
   */
  function pintarTexto(contenedor, texto) {
    texto.split(/\n{2,}/).forEach(function (parrafo) {
      var p = document.createElement('p');
      parrafo.split(/(\*\*[^*]+\*\*)/).forEach(function (trozo) {
        if (!trozo) return;
        if (trozo.slice(0, 2) === '**' && trozo.slice(-2) === '**') {
          var fuerte = document.createElement('strong');
          fuerte.textContent = trozo.slice(2, -2);
          p.appendChild(fuerte);
        } else {
          // Los saltos simples dentro de un párrafo se conservan.
          trozo.split('\n').forEach(function (linea, i) {
            if (i > 0) p.appendChild(document.createElement('br'));
            p.appendChild(document.createTextNode(linea));
          });
        }
      });
      contenedor.appendChild(p);
    });
  }

  function burbuja(clase) {
    var div = document.createElement('div');
    div.className = 'burbuja ' + clase;
    mensajes.appendChild(div);
    mensajes.scrollTop = mensajes.scrollHeight;
    return div;
  }

  function agregarMensaje(clase, texto, meta) {
    var div = burbuja(clase);
    pintarTexto(div, texto);
    if (meta) {
      var pie = document.createElement('span');
      pie.className = 'burbuja__meta';
      pie.textContent = meta;
      div.appendChild(pie);
    }
    mensajes.scrollTop = mensajes.scrollHeight;
    return div;
  }

  function mostrarEscribiendo() {
    var div = burbuja('burbuja--bot');
    var puntos = document.createElement('span');
    puntos.className = 'escribiendo';
    puntos.appendChild(document.createElement('span'));
    puntos.appendChild(document.createElement('span'));
    puntos.appendChild(document.createElement('span'));
    div.appendChild(puntos);
    return div;
  }

  function tono(texto, clase) {
    if (!estadoChat) return;
    estadoChat.textContent = texto;
    if (clase) estadoChat.setAttribute('data-tono', clase);
    else estadoChat.removeAttribute('data-tono');
  }

  function bloquear(si) {
    esperando = si;
    if (entrada) entrada.disabled = si;
    if (enviar) enviar.disabled = si;
  }

  /** Cómo se nombra cada intención para quien mira la pantalla. */
  var INTENCIONES = {
    FAQ: 'Consulta frecuente',
    ESTADO_PEDIDO: 'Estado de pedido',
    RECLAMO: 'Reclamo — abrió un caso',
    GENERAL: 'Consulta general'
  };

  function pieDeRespuesta(datos) {
    var partes = [];
    if (datos.intent) partes.push(INTENCIONES[datos.intent] || datos.intent);
    if (typeof datos.seconds === 'number') {
      partes.push('respondió en ' + datos.seconds.toFixed(2).replace('.', ',') + ' s');
    }
    return partes.join(' · ');
  }

  var ERRORES = {
    429: 'Muchas consultas seguidas. Esperá un momento y volvé a probar.',
    503: 'El asistente no está disponible en este momento.',
    504: 'El asistente tardó más de lo esperado. Probá con otra consulta.'
  };

  function preguntar(texto) {
    if (esperando || !texto.trim()) return;
    var limpio = texto.trim().slice(0, 500);

    agregarMensaje('burbuja--yo', limpio);
    if (entrada) entrada.value = '';
    bloquear(true);
    tono('Escribiendo…', 'pensando');
    var pensando = mostrarEscribiendo();

    fetch(API + '/demo/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ message: limpio, session: SESION })
    })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (cuerpo) {
          return { ok: r.ok, status: r.status, cuerpo: cuerpo };
        });
      })
      .then(function (res) {
        pensando.remove();
        if (res.ok && res.cuerpo && res.cuerpo.reply) {
          agregarMensaje('burbuja--bot', res.cuerpo.reply, pieDeRespuesta(res.cuerpo));
          tono('En línea');
          traerStats(); // el contador de arriba sube con este mensaje
        } else {
          agregarMensaje('burbuja--aviso', ERRORES[res.status] || 'No pudimos enviar tu consulta. Probá de nuevo.');
          tono('Con problemas', 'error');
        }
      })
      .catch(function () {
        pensando.remove();
        agregarMensaje('burbuja--aviso', 'No pudimos conectarnos. Revisá tu conexión y probá de nuevo.');
        tono('Sin conexión', 'error');
      })
      .then(function () {
        bloquear(false);
        if (entrada) entrada.focus();
      });
  }

  // ---------------------------------------------------------------- pedido en vivo

  var pedido = $('[data-pedido]');
  var pasos = $('[data-pasos]');
  var recibo = $('[data-recibo]');
  var reposo = $('[data-pedido-reposo]');
  var avisoPedido = $('[data-pedido-aviso]');
  var pidiendo = false;

  var ESTADOS = {
    confirmed: 'Confirmado',
    no_stock: 'Sin stock — no se vendió de más',
    pending: 'Pendiente',
    processing: 'En proceso',
    shipped: 'Despachado',
    delivered: 'Entregado',
    cancelled: 'Cancelado'
  };

  function segundos(n) {
    if (typeof n !== 'number') return '';
    if (n < 1) return Math.round(n * 1000) + ' ms';
    return n.toFixed(2).replace('.', ',') + ' s';
  }

  function limpiarPasos() {
    $$('.paso', pasos).forEach(function (p) {
      p.classList.remove('paso--hecho', 'paso--omitido');
      var t = $('.paso__tiempo', p);
      if (t) t.textContent = '';
    });
  }

  function mostrarAvisoPedido(texto) {
    if (!avisoPedido) return;
    if (!texto) { avisoPedido.hidden = true; avisoPedido.textContent = ''; return; }
    avisoPedido.textContent = texto;
    avisoPedido.hidden = false;
  }

  /**
   * Va marcando los pasos uno por uno. La demora entre marcas es de presentación:
   * el pedido ya terminó cuando la respuesta llegó. Los tiempos que se escriben al
   * lado de cada paso sí son los medidos.
   */
  function animarPasos(datos) {
    var sinStock = datos.status === 'no_stock';
    var secuencia = [
      { clave: 'recibido',    estado: 'hecho',                       tiempo: '0 ms' },
      { clave: 'stock',       estado: sinStock ? 'omitido' : 'hecho',
        tiempo: sinStock ? 'sin stock' : segundos(datos.mttd_seconds) },
      { clave: 'confirmado',  estado: sinStock ? 'omitido' : 'hecho',
        tiempo: sinStock ? 'venta frenada' : segundos(datos.mttd_seconds) },
      { clave: 'aviso',       estado: 'hecho',                       tiempo: segundos(datos.end_to_end_seconds) }
    ];
    secuencia.forEach(function (paso, i) {
      window.setTimeout(function () {
        var nodo = $('[data-paso="' + paso.clave + '"]', pasos);
        if (!nodo) return;
        nodo.classList.add('paso--' + paso.estado);
        var t = $('.paso__tiempo', nodo);
        if (t) t.textContent = paso.tiempo;
      }, 420 * i);
    });
  }

  function pintarRecibo(datos) {
    var textos = {
      order_number: datos.order_number,
      product_name: datos.product_name,
      quantity: conMiles(datos.quantity) + (datos.quantity === 1 ? ' unidad' : ' unidades'),
      status: ESTADOS[datos.status] || datos.status,
      end_to_end_seconds: segundos(datos.end_to_end_seconds)
    };
    Object.keys(textos).forEach(function (clave) {
      var nodo = $('[data-recibo="' + clave + '"]', recibo);
      if (nodo) nodo.textContent = textos[clave];
    });
    var estado = $('[data-recibo="status"]', recibo);
    if (estado) {
      if (datos.status === 'no_stock') estado.setAttribute('data-tono', 'aviso');
      else estado.removeAttribute('data-tono');
    }
    recibo.hidden = false;
  }

  var ERRORES_PEDIDO = {
    429: 'Muchos pedidos seguidos. Esperá un momento y volvé a probar.',
    503: 'El sistema de pedidos no está disponible en este momento.',
    504: 'El pedido se envió pero todavía no quedó registrado. Miralo en el panel en unos segundos.'
  };

  function meterPedido(escenario, boton) {
    if (pidiendo) return;
    pidiendo = true;
    mostrarAvisoPedido('');
    $$('[data-escenario]', pedido).forEach(function (b) { b.disabled = true; });
    var textoOriginal = boton.textContent;
    boton.textContent = 'Procesando…';

    if (reposo) reposo.hidden = true;
    if (recibo) recibo.hidden = true;
    limpiarPasos();
    pasos.classList.add('pasos--visible');

    fetch(API + '/demo/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ session: SESION, scenario: escenario })
    })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (cuerpo) {
          return { ok: r.ok, status: r.status, cuerpo: cuerpo };
        });
      })
      .then(function (res) {
        if (res.ok && res.cuerpo && res.cuerpo.order_number) {
          animarPasos(res.cuerpo);
          window.setTimeout(function () { pintarRecibo(res.cuerpo); }, 420 * 4);
          traerStats();
        } else {
          pasos.classList.remove('pasos--visible');
          if (reposo) reposo.hidden = false;
          mostrarAvisoPedido(ERRORES_PEDIDO[res.status] || 'No pudimos meter el pedido. Probá de nuevo.');
        }
      })
      .catch(function () {
        pasos.classList.remove('pasos--visible');
        if (reposo) reposo.hidden = false;
        mostrarAvisoPedido('No pudimos conectarnos. Revisá tu conexión y probá de nuevo.');
      })
      .then(function () {
        pidiendo = false;
        $$('[data-escenario]', pedido).forEach(function (b) { b.disabled = false; });
        boton.textContent = textoOriginal;
      });
  }

  // ---------------------------------------------------------------- enlaces al portal

  /**
   * El portal vive en el puerto 8080 de la MISMA máquina que sirve la landing.
   * Escrito a mano en el HTML quedaría 'localhost', que solo funciona para quien
   * abre la página en esa computadora: desde otra de la red la landing se ve pero
   * el botón no lleva a ningún lado. Se reescribe con el host real de la página.
   */
  function enlazarPortal() {
    var destino = window.location.protocol + '//' + window.location.hostname + ':8080';
    $$('a[href^="http://localhost:8080"]').forEach(function (a) { a.href = destino; });
  }

  // ---------------------------------------------------------------- presentación

  function navPegada() {
    var nav = $('#nav');
    if (!nav) return;
    var marcar = function () { nav.classList.toggle('nav--pegada', window.scrollY > 8); };
    marcar();
    window.addEventListener('scroll', marcar, { passive: true });
  }

  function apareceAlScrollear() {
    var objetivos = $$('.tarjeta, .metrica, .factor, .limites li, .maqueta, .firma__bloque');
    if (!('IntersectionObserver' in window)) return;
    objetivos.forEach(function (n) { n.classList.add('aparece'); });
    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('aparece--visible');
        observador.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -60px 0px', threshold: 0.1 });
    objetivos.forEach(function (n) { observador.observe(n); });
  }

  // ---------------------------------------------------------------- arranque

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      preguntar(entrada ? entrada.value : '');
    });
  }

  if (sugerencias) {
    // Los botones quedan a la vista: en una demostración conviene poder disparar
    // una consulta de cada tipo sin tener que tipear.
    sugerencias.addEventListener('click', function (e) {
      var boton = e.target.closest('.sugerencia');
      if (boton) preguntar(boton.textContent);
    });
  }

  if (pedido) {
    pedido.addEventListener('click', function (e) {
      var boton = e.target.closest('[data-escenario]');
      if (boton) meterPedido(boton.getAttribute('data-escenario'), boton);
    });
  }

  if (chat) tono('En línea');

  traerStats();
  window.setInterval(traerStats, INTERVALO_STATS_MS);

  enlazarPortal();
  navPegada();
  apareceAlScrollear();
})();
