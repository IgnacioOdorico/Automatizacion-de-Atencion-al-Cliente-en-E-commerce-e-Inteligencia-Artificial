<#
.SYNOPSIS
    PF-04 y PF-05 — pruebas funcionales de rechazo del Flujo 1, con evidencia.

.DESCRIPTION
    Re-ejecuta las dos pruebas de rechazo de la Tabla 4.9 y deja constancia de
    lo que devuelve el webhook y de cómo termina cada ejecución en n8n.

      PF-04  SKU inexistente (PROD-999).
      PF-05  order_number ya registrado (ORD-DEMO-01).

    Ninguna de las dos escribe filas: el INSERT de PF-04 no encuentra el
    producto y el de PF-05 choca contra la restricción de unicidad. El guion
    lo verifica comparando la cantidad de órdenes antes y después.

    Salida: resultados/pf04_pf05_<fecha>.txt
#>
$ErrorActionPreference = 'Stop'
$wf = 'xICbeLNSWYt89Zxg'   # Flujo 1 activo (15 nodos, con la rama de alerta)
function Q([string]$sql) {
    # por stdin: PowerShell 5.1 pierde las comillas dobles al pasar argumentos a un ejecutable
    ($sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis -At) -join "`n"
}
function Enviar([string]$json) {
    $r = Invoke-WebRequest -Uri 'http://localhost:5678/webhook/orden-nueva' -Method POST `
        -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($json)) -UseBasicParsing
    [pscustomobject]@{ status = [int]$r.StatusCode; cuerpo = [string]$r.Content }
}
$sello = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$salida = Join-Path $PSScriptRoot "resultados\pf04_pf05_$sello.txt"
$lineas = @("PF-04 y PF-05 — $((Get-Date).ToUniversalTime().ToString('u'))", "commit: $(git rev-parse --short HEAD)", '')
$antes = Q 'SELECT count(*) FROM orders;'
$pruebas = @(
    @{ id = 'PF-04'; esperado = 'Rechazo con error controlado'
       json = '{"order_number":"ORD-PF04-' + $sello + '","customer_name":"Prueba PF04","customer_email":"pf04@example.com","customer_phone":"5492610000000","product_sku":"PROD-999","quantity":1}' },
    @{ id = 'PF-05'; esperado = 'Rechazo por restricción de unicidad'
       json = '{"order_number":"ORD-DEMO-01","customer_name":"Prueba PF05","customer_email":"pf05@example.com","customer_phone":"5492610000000","product_sku":"PROD-018","quantity":1}' }
)
foreach ($p in $pruebas) {
    $ultimo = Q "SELECT coalesce(max(id),0) FROM execution_entity WHERE ""workflowId"" = '$wf';"
    $r = Enviar $p.json
    Start-Sleep -Seconds 3
    $ej = Q "SELECT id || ' | ' || status FROM execution_entity WHERE ""workflowId"" = '$wf' AND id > $ultimo ORDER BY id;"
    $eid = ($ej -split ' \| ')[0]
    $datos = Q "SELECT data FROM execution_data WHERE ""executionId"" = $eid;"
    $nodos = @('Registrar Orden', 'Verificar Stock', 'IF Stock Disponible', 'Marcar Sin Stock', 'Confirmar Orden',
               'Respuesta Confirmada', 'Respuesta Sin Stock') | Where-Object { $datos.Contains('"' + $_ + '"') }
    $err = [regex]::Match($datos, '(duplicate key[^"]*|violates[^"]*)').Value
    $lineas += "$($p.id) · esperado: $($p.esperado)"
    $lineas += "  HTTP $($r.status) · cuerpo: '$($r.cuerpo)'"
    $lineas += "  ejecución $ej · nodos ejecutados: $($nodos -join ', ')"
    $lineas += "  error registrado: $(if ($err) { $err } else { '(ninguno)' })"
    $lineas += ''
}
$despues = Q 'SELECT count(*) FROM orders;'
$lineas += "órdenes antes: $antes · después: $despues · filas escritas: $([int]$despues - [int]$antes)"
$lineas | Set-Content -Path $salida -Encoding UTF8
$lineas
