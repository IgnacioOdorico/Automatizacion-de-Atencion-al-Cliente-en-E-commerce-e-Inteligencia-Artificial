# Landing de presentación: sitio estático, sin paso de build.
# Es HTML, CSS y un guion sin dependencias a propósito: lo que se muestra en el
# video tiene que levantar siempre, sin npm install de por medio.
FROM nginx:1.27-alpine

COPY nginx.conf            /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/conf.d/security-headers.conf
COPY site/                 /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=4s --retries=4 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
