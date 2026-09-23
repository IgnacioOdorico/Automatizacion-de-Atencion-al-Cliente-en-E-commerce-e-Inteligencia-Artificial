# Instrucciones para el asistente de Juan Cruz

> **Juan Cruz:** pasale este archivo entero a tu Claude y decile «seguí esto».
> Él se encarga de dejarte todo listo.

---

## Contexto

Juan Cruz es uno de los tres autores de un Trabajo Integrador de la UTN Facultad Regional
Mendoza, ya aprobado. Ahora tienen que grabar un **video de presentación del producto** para
la defensa. El video se graba entre los tres y después se monta.

**La parte de Juan Cruz** son cuatro tramos, unos dos minutos en total: la apertura, el
problema que resuelve el producto, qué hace el producto, y el cierre. **No necesita
credenciales de nada**: no se loguea en ningún lado.

Su guion completo, con el texto que tiene que narrar, está en
[`video/GUION_JUANCRUZ.md`](GUION_JUANCRUZ.md). Tu trabajo es dejarle el entorno listo para
que abra eso y grabe.

---

## Paso 1 — Traer el proyecto

```bash
git clone https://github.com/IgnacioOdorico/Automatizacion-de-Atencion-al-Cliente-en-E-commerce-e-Inteligencia-Artificial.git
cd Automatizacion-de-Atencion-al-Cliente-en-E-commerce-e-Inteligencia-Artificial
git checkout feature/landing-demo
```

Si ya lo tenía clonado: `git fetch origin && git checkout feature/landing-demo && git pull`.

**Verificá que existan** `video/GUION_JUANCRUZ.md`, `video/placas.html` y la carpeta
`landing/`. Si falta alguno, está en la rama equivocada.

---

## Paso 2 — Lo que no depende de nadie: las placas

Las **placas** son la presentación animada que Juan Cruz usa en la apertura y en el cierre.
Es un archivo HTML suelto, **sin dependencias, sin servidor, sin nada**. Abrilo:

```bash
start video/placas.html          # Windows
open video/placas.html           # macOS
```

Comprobá con él que:
- Se ve la placa 1: logo, «El post-venta de tu tienda, resuelto solo», y los tres autores.
- `F` la pone en pantalla completa.
- `→` o la barra espaciadora avanzan; `←` vuelve.
- El cartelito de ayuda de abajo a la derecha **desaparece solo** a los ~2,6 segundos.
  Decile a Juan Cruz que espere a que se vaya antes de empezar a grabar.

Con esto ya puede grabar la escena 1 y la escena 8. **La mitad de su parte no necesita nada
más.**

---

## Paso 3 — La landing: acá sí hay una dependencia

Las escenas 2 y 3 se graban sobre la landing del producto. Las **secciones de texto** son
HTML y se ven siempre, pero el encabezado tiene una tarjeta, **«Actividad del sistema»**, que
lee datos en vivo del sistema de Santiago: pedidos procesados, consultas atendidas, casos.

Si esa tarjeta dice «Sin conexión» en vez de «En vivo», **queda mal en cámara** y además
Juan Cruz tiene una línea de guion que la señala.

Ese sistema corre **solo en la máquina de Santiago**. Dos escenarios:

### Escenario A — Juan Cruz está en la misma red que Santiago

Es el caso cómodo. Pedile a Santiago que:
1. Tenga el sistema levantado (`docker compose up -d` en su máquina).
2. Le pase su IP de red local. Al momento de escribir esto era `192.168.1.2`.

Después, desde la máquina de Juan Cruz:

```powershell
video\verificar_entorno.ps1 -Host 192.168.1.2
```

Si dice **LISTO PARA GRABAR**, abrí `http://192.168.1.2:3001` y ya está.

> Si no tenés PowerShell (macOS/Linux), el equivalente es:
> ```bash
> curl -s -o /dev/null -w '%{http_code}\n' http://192.168.1.2:3001/
> curl -s http://192.168.1.2:3001/api/demo/stats
> ```
> El primero tiene que dar `200` y el segundo, un JSON con más de 200 pedidos.

### Escenario B — Juan Cruz NO está en la red de Santiago

Tres salidas, en orden de conveniencia:

1. **Graba las escenas 1 y 8** (las placas) ahora, que no dependen de nada, y deja las
   escenas 2 y 3 para cuando esté con Santiago o en la misma red.
2. **Graba en la máquina de Santiago**, en otro momento.
3. Montar el sistema completo en la máquina de Juan Cruz. **No lo recomiendo para su
   parte**: necesita Docker, credenciales del motor de automatización, una clave de un
   servicio de IA que es de Santiago, y una copia de la base. Es mucho trabajo para lo poco
   que él necesita del sistema.

---

## Paso 4 — Dejarlo listo para grabar

Repasá con Juan Cruz:

- [ ] Grabadora de pantalla configurada a **1920×1080** (OBS anda bien y es gratis).
- [ ] Navegador **sin barra de marcadores, sin extensiones a la vista**, una sola pestaña.
- [ ] **Notificaciones del sistema en silencio** (en Windows, «Asistente de concentración»).
- [ ] Zoom del navegador al 100 %, o 110 % si el texto le queda chico.
- [ ] La tarjeta «Actividad del sistema» diciendo **En vivo** (si graba la landing).

Y después que abra [`video/GUION_JUANCRUZ.md`](GUION_JUANCRUZ.md), que tiene el texto exacto
a narrar, con los tiempos de cada escena.

---

## Reglas que no se rompen

Estas no son sugerencias del guion, son decisiones ya tomadas por el equipo:

- **No entrar al portal** (`:8080`). Esa parte la graba Santiago, que tiene la cuenta.
- **No apretar los botones** «Comprar una unidad» ni «Pedir más de lo que hay»: esos
  disparan pedidos reales y son la escena de Ignacio. Si Juan Cruz los aprieta, le ensucia
  los contadores.
- **No escribir en el chat** de la landing, por lo mismo.
- **No mostrar** la consola del navegador, la terminal, Docker ni el editor de código.
  El video es una presentación de producto: la tecnología de adentro no se muestra.
- **No hacer commits ni push** desde esta máquina. Juan Cruz solo lee y graba.

---

## Si algo falla

| Síntoma | Qué pasa | Qué hacer |
|---|---|---|
| «Sin conexión» en la tarjeta de actividad | El sistema de Santiago no está levantado o no llegás por red | Pedile a Santiago que corra `docker compose up -d` y confirmá la IP |
| La landing no abre por la IP | Están en redes distintas, o el firewall de Santiago bloquea | Probá `ping <ip>`. Si no responde, es red. Ver escenario B |
| Las placas se ven cortadas | La ventana no es 16:9 | Poné pantalla completa con `F`; la placa se escala sola |
| Las placas se ven sin la tipografía buena | No hay internet: la fuente viene de Google Fonts | Con internet se arregla solo. Sin internet, se ve con la fuente del sistema: es aceptable pero no ideal |
| El cartelito de ayuda sale en la grabación | Empezó a grabar muy rápido | Esperá 3 segundos después de la última tecla antes de grabar |
