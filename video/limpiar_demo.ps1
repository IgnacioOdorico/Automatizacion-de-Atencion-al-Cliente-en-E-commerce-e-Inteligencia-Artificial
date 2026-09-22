# ============================================================
#  limpiar_demo.ps1 — dejar la base como estaba antes de ensayar
#
#  Borra SOLO lo que genera la landing:
#    - pedidos con prefijo ORD-WEB-  (el botón «Probalo»)
#    - conversaciones y casos de usuarios demo-*  (el chat de la landing)
#  y repone el stock que descontaron los pedidos confirmados.
#
#  NO toca nada de las corridas de la tesis (ORD-E1A-, ORD-E1B-, ORD-E4-,
#  ORD-HIST-, ORD-LOAD-) ni el corpus de interacciones medido.
#
#  Uso:   .\video\limpiar_demo.ps1
#         .\video\limpiar_demo.ps1 -Simular    (muestra qué borraría, sin borrar)
# ============================================================

param(
    [switch]$Simular
)

$ErrorActionPreference = 'Stop'
$contenedor = 'tesis_postgres'
$baseDatos  = 'ecommerce_tesis'
$usuario    = 'n8n_user'

function Invoke-Sql {
    param([string]$Consulta)
    $salida = $Consulta | docker exec -i $contenedor psql -U $usuario -d $baseDatos -At -F' | ' -v ON_ERROR_STOP=1 2>&1
    if ($LASTEXITCODE -ne 0) { throw "psql falló: $salida" }
    return $salida
}

Write-Host ''
Write-Host '  Limpieza de la demostración' -ForegroundColor Cyan
Write-Host '  ---------------------------' -ForegroundColor Cyan

$resumen = Invoke-Sql @"
SELECT 'pedidos de la landing', count(*)::text FROM orders WHERE order_number LIKE 'ORD-WEB-%'
UNION ALL
SELECT 'unidades a reponer', COALESCE(sum(quantity),0)::text FROM orders
 WHERE order_number LIKE 'ORD-WEB-%' AND status = 'confirmed'
UNION ALL
SELECT 'conversaciones de la landing', count(*)::text FROM interactions WHERE user_id LIKE 'demo-%'
UNION ALL
SELECT 'casos de la landing', count(*)::text FROM tickets WHERE user_id LIKE 'demo-%';
"@

$resumen | ForEach-Object { Write-Host "  $_" }
Write-Host ''

if ($Simular) {
    Write-Host '  Modo simulación: no se borró nada.' -ForegroundColor Yellow
    Write-Host ''
    return
}

# El stock se repone ANTES de borrar los pedidos: después ya no se sabe cuánto descontaron.
Invoke-Sql @"
BEGIN;
UPDATE products p SET stock = p.stock + s.unidades
  FROM (SELECT product_id, sum(quantity) AS unidades
          FROM orders
         WHERE order_number LIKE 'ORD-WEB-%' AND status = 'confirmed'
         GROUP BY product_id) s
 WHERE p.id = s.product_id;
DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE order_number LIKE 'ORD-WEB-%');
DELETE FROM orders      WHERE order_number LIKE 'ORD-WEB-%';
DELETE FROM tickets     WHERE user_id LIKE 'demo-%';
DELETE FROM interactions WHERE user_id LIKE 'demo-%';
COMMIT;
"@ | Out-Null

Write-Host '  Listo. Estado actual:' -ForegroundColor Green
Invoke-Sql @"
SELECT 'pedidos totales', count(*)::text FROM orders
UNION ALL SELECT 'interacciones totales', count(*)::text FROM interactions
UNION ALL SELECT 'casos totales', count(*)::text FROM tickets;
"@ | ForEach-Object { Write-Host "  $_" }
Write-Host ''
Write-Host '  Los correos de prueba quedan en la bandeja (http://localhost:8025).' -ForegroundColor DarkGray
Write-Host '  Si querés vaciarla, usá el botón "Delete all" de esa página.' -ForegroundColor DarkGray
Write-Host ''
