# ============================================================
#  verificar_entorno.ps1 — ¿se puede grabar desde esta máquina?
#
#  Comprueba, en orden, todo lo que el video necesita y dice qué falta.
#  No escribe nada en la base salvo que se pase -Completo, que además
#  dispara un pedido y una consulta de verdad (y avisa cómo limpiarlos).
#
#  Uso:
#    .\video\verificar_entorno.ps1                      (contra esta máquina)
#    .\video\verificar_entorno.ps1 -Host 192.168.1.2    (contra la de Santiago)
#    .\video\verificar_entorno.ps1 -Completo            (prueba de punta a punta)
# ============================================================

[CmdletBinding()]
param(
    [Alias('Host')]
    [string]$Servidor = 'localhost',
    [switch]$Completo
)

$ErrorActionPreference = 'Stop'
$base = "http://${Servidor}:3001"
$portal = "http://${Servidor}:8080"
$fallas = @()
$avisos = @()

function Escribir-Paso {
    param([string]$Nombre, [string]$Estado, [string]$Detalle = '')
    $color = switch ($Estado) {
        'OK'    { 'Green' }
        'FALLA' { 'Red' }
        default { 'Yellow' }
    }
    Write-Host ('  {0,-6}' -f $Estado) -ForegroundColor $color -NoNewline
    Write-Host (' {0}' -f $Nombre) -NoNewline
    if ($Detalle) { Write-Host ("  $Detalle") -ForegroundColor DarkGray } else { Write-Host '' }
}

function Probar-Url {
    param([string]$Url, [int]$Timeout = 10)
    try {
        $r = Invoke-WebRequest -Uri $Url -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop
        return @{ ok = $true; codigo = $r.StatusCode; cuerpo = $r.Content }
    } catch {
        return @{ ok = $false; codigo = 0; error = $_.Exception.Message }
    }
}

Write-Host ''
Write-Host '  ==============================================' -ForegroundColor Cyan
Write-Host '   ¿Se puede grabar el video desde acá?' -ForegroundColor Cyan
Write-Host '  ==============================================' -ForegroundColor Cyan
Write-Host ("  Apuntando a: {0}" -f $Servidor) -ForegroundColor DarkGray
Write-Host ''

# ---------------------------------------------------------------- 1. la landing
Write-Host '  LA LANDING' -ForegroundColor White
$r = Probar-Url "$base/"
if ($r.ok) {
    Escribir-Paso 'La página abre' 'OK' $base
} else {
    Escribir-Paso 'La página abre' 'FALLA' $base
    $fallas += "La landing no responde en $base. Si apuntás a otra máquina, revisá que estén en la misma red y que allá esté levantado el sistema."
}

# ---------------------------------------------------------------- 2. contadores
$r = Probar-Url "$base/api/demo/stats"
if ($r.ok) {
    $s = $r.cuerpo | ConvertFrom-Json
    Escribir-Paso 'Contadores en vivo' 'OK' ("{0} pedidos - {1} consultas - {2} casos" -f $s.orders, $s.interactions, $s.tickets)
    if ($s.orders -lt 100) {
        $avisos += "Hay solo $($s.orders) pedidos: la base parece vacía o recién creada. En la instalación de Santiago hay ~218."
    }
} else {
    Escribir-Paso 'Contadores en vivo' 'FALLA' 'la tarjeta va a decir "Sin conexión"'
    $fallas += 'El servicio de datos no responde. Sin esto, los contadores del encabezado quedan en guiones y el botón de pedido y el chat no funcionan.'
}

# ---------------------------------------------------------------- 3. el portal
Write-Host ''
Write-Host '  EL PORTAL  (solo lo graba Santiago)' -ForegroundColor White
$r = Probar-Url "$portal/"
if ($r.ok) {
    Escribir-Paso 'El portal abre' 'OK' $portal
} else {
    Escribir-Paso 'El portal abre' 'AVISO' 'no hace falta si no grabás esa parte'
    $avisos += "El portal no responde en $portal. Solo importa para la parte de Santiago."
}

# ---------------------------------------------------------------- 4. las placas
Write-Host ''
Write-Host '  LAS PLACAS' -ForegroundColor White
$placas = Join-Path (Split-Path $PSScriptRoot -Parent) 'video\placas.html'
if (Test-Path $placas) {
    Escribir-Paso 'El archivo está' 'OK' $placas
} else {
    Escribir-Paso 'El archivo está' 'FALLA'
    $fallas += 'Falta video/placas.html. ¿Clonaste la rama feature/landing-demo?'
}

# ---------------------------------------------------------------- 5. punta a punta
if ($Completo) {
    Write-Host ''
    Write-Host '  PRUEBA DE PUNTA A PUNTA  (escribe en la base)' -ForegroundColor White
    $sesion = 'verif' + (Get-Random -Minimum 1000000 -Maximum 9999999)

    try {
        $cuerpo = @{ session = $sesion; scenario = 'con_stock' } | ConvertTo-Json -Compress
        $p = Invoke-RestMethod -Uri "$base/api/demo/order" -Method Post -Body $cuerpo `
             -ContentType 'application/json' -TimeoutSec 60
        Escribir-Paso 'Entra un pedido real' 'OK' ("{0} - {1} - {2} ms de punta a punta" -f $p.order_number, $p.status, [math]::Round($p.end_to_end_seconds * 1000))
    } catch {
        Escribir-Paso 'Entra un pedido real' 'FALLA'
        $fallas += 'El botón de pedido no funciona. El motor de automatización no está respondiendo.'
    }

    try {
        # El cuerpo se manda como bytes UTF-8: con acentos, PowerShell puede mandarlo mal.
        $json = @{ session = $sesion; message = '¿Hacen envíos a Mendoza?' } | ConvertTo-Json -Compress
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        $c = Invoke-RestMethod -Uri "$base/api/demo/chat" -Method Post -Body $bytes `
             -ContentType 'application/json; charset=utf-8' -TimeoutSec 90
        Escribir-Paso 'El asistente responde' 'OK' ("{0} - {1} s" -f $c.intent, $c.seconds)
    } catch {
        Escribir-Paso 'El asistente responde' 'FALLA'
        $fallas += 'El chat no funciona. Puede faltar la credencial del modelo de lenguaje en el motor.'
    }

    $avisos += 'La prueba dejó un pedido y una conversación. Que Santiago corra video/limpiar_demo.ps1 antes de la toma buena.'
}

# ---------------------------------------------------------------- veredicto
Write-Host ''
Write-Host '  ----------------------------------------------' -ForegroundColor DarkGray
if ($fallas.Count -eq 0) {
    Write-Host '  LISTO PARA GRABAR' -ForegroundColor Green
} else {
    Write-Host '  TODAVÍA NO SE PUEDE GRABAR' -ForegroundColor Red
    Write-Host ''
    foreach ($f in $fallas) { Write-Host "    - $f" -ForegroundColor Red }
}
if ($avisos.Count -gt 0) {
    Write-Host ''
    foreach ($a in $avisos) { Write-Host "    - $a" -ForegroundColor Yellow }
}
Write-Host ''

if (-not $Completo -and $fallas.Count -eq 0) {
    Write-Host '  Para probar el pedido y el chat de verdad: volvé a correrlo con -Completo' -ForegroundColor DarkGray
    Write-Host ''
}

if ($fallas.Count -gt 0) { exit 1 } else { exit 0 }
