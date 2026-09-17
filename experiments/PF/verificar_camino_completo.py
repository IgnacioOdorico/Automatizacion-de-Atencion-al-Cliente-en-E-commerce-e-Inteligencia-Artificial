# -*- coding: utf-8 -*-
"""Comprobación de humo del Flujo 1 con las consultas parametrizadas.

PF-06 verifica que un apóstrofo llegue como dato, pero ejercita solo el primer nodo:
la orden se rechaza por unicidad. Esta comprobación recorre el camino completo de la
rama con stock —registrar, verificar, descontar, confirmar, notificar— para que la
parametrización no rompa la demostración.

La orden que escribe se borra al terminar y el stock del producto se repone, porque
una orden con la marca de los datos medidos alteraría los totales del Capítulo 5.
El guion informa los recuentos antes y después: si algo queda, se ve.

Uso (con los contenedores arriba):
    python verificar_camino_completo.py
Salida: resultados/camino_completo_<fecha>.txt
"""
import io
import os
import sys
import json
import time
import subprocess
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
WEBHOOK = 'http://localhost:5678/webhook/orden-nueva'
SKU = 'PROD-018'          # pendrive: stock 80 sobre un mínimo de 10, no dispara la alerta
CANT = 1


def sql(consulta):
    out = subprocess.run(['docker', 'exec', '-i', 'tesis_postgres', 'psql', '-U', 'n8n_user',
                          '-d', 'ecommerce_tesis', '-At', '-F', '\x1f'],
                         input=consulta.encode('utf-8'), capture_output=True)
    if out.returncode != 0:
        sys.exit('psql falló: ' + out.stderr.decode('utf-8', 'replace'))
    return [f.split('\x1f') for f in out.stdout.decode('utf-8').strip().splitlines() if f]


def main():
    sello = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    numero = 'ORD-SMOKE-%s' % datetime.now().strftime('%Y%m%d%H%M%S')
    antes = sql("SELECT (SELECT COUNT(*) FROM orders), (SELECT stock FROM products WHERE sku = '%s');" % SKU)[0]
    L = ['Comprobación de humo del Flujo 1 con las consultas parametrizadas · %s'
         % datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ'),
         'orden de prueba: %s · producto %s · órdenes antes: %s · stock antes: %s'
         % (numero, SKU, antes[0], antes[1]), '']
    cuerpo = json.dumps({'order_number': numero, 'customer_name': 'Prueba de humo',
                         'customer_email': 'humo@example.com', 'customer_phone': '5492610000000',
                         'product_sku': SKU, 'quantity': CANT}).encode('utf-8')
    req = urllib.request.Request(WEBHOOK, data=cuerpo,
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(req, timeout=60) as r:
        status, resp = r.status, r.read().decode('utf-8', 'replace')
    time.sleep(6)
    fila = sql("SELECT status, received_at IS NOT NULL, processed_at IS NOT NULL, notified_at IS NOT NULL, "
               "round(EXTRACT(epoch FROM processed_at - received_at)::numeric, 3), "
               "round(EXTRACT(epoch FROM notified_at - processed_at)::numeric, 3), customer_name "
               "FROM orders WHERE order_number = '%s';" % numero)
    stock = sql("SELECT stock FROM products WHERE sku = '%s';" % SKU)[0][0]
    L.append('HTTP %d · cuerpo: %s' % (status, resp[:160] or "''"))
    if fila:
        est, rec, pro, notif, mttd, mttr, nombre = fila[0]
        L += ['orden registrada · estado %s · marcas: received %s, processed %s, notified %s'
              % (est, rec, pro, notif),
              'MTTD %s s · MTTR %s s · nombre guardado: %s' % (mttd, mttr, nombre),
              'stock del producto: %s -> %s' % (antes[1], stock),
              'resultado: %s' % ('CAMINO COMPLETO OK' if est == 'confirmed' and notif == 't' else 'REVISAR')]
    else:
        L += ['orden registrada: NO', 'resultado: REVISAR']

    # la orden de prueba no puede quedar: alteraría los totales del Capítulo 5
    sql("DELETE FROM stock_alerts WHERE order_id IN (SELECT id FROM orders WHERE order_number = '%s');"
        "DELETE FROM orders WHERE order_number = '%s';"
        "UPDATE products SET stock = %s WHERE sku = '%s';" % (numero, numero, antes[1], SKU))
    despues = sql("SELECT (SELECT COUNT(*) FROM orders), (SELECT stock FROM products WHERE sku = '%s');" % SKU)[0]
    L += ['', 'limpieza: la orden de prueba se borró y el stock se repuso',
          'órdenes: %s antes, %s después · stock: %s antes, %s después'
          % (antes[0], despues[0], antes[1], despues[1]),
          'estado de la base: %s' % ('sin cambios' if despues == antes else 'REVISAR')]
    salida = os.path.join(BASE, 'resultados', 'camino_completo_%s.txt' % sello)
    io.open(salida, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('\n'.join(L))
    print('\nguardado en', salida)


if __name__ == '__main__':
    main()
