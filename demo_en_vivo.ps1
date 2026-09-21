# ============================================================
#  DEMO EN VIVO — Tesis UTN FRM
#  Dispara UNA orden nueva contra n8n (y, opcionalmente, un mensaje
#  al chatbot) mientras se filma el dashboard: el dashboard hace
#  polling cada 4 s y la orden aparece sola en Pedidos.
#
#  !! ADVERTENCIA: ESTE SCRIPT ESCRIBE EN LA BASE DE DATOS COMPARTIDA !!
#  La BD `ecommerce_tesis` es la misma que usan Grafana y las metricas
#  de la tesis (MTTD / MTTR / TMR):
#    - la orden queda guardada en `orders` (con data_source 'measured'
#      y, si hay stock, se DESCUENTA stock de `products`);
#    - el mensaje del chatbot (-ConChatbot) queda en `interactions` y
#      puede crear un `ticket`.
#  Esas filas NO se borran solas y se mezclan con los datos medidos.
#  Para limpiarlas a mano (ejemplo, revisar antes de correr):
#    DELETE FROM orders WHERE order_number LIKE 'ORD-DEMO-%';
#  y restituir el stock descontado.
#
#  Uso:
#    .\demo_en_vivo.ps1                       # 1 orden con stock (PROD-001)
#    .\demo_en_vivo.ps1 -Sku PROD-005 -Cantidad 2
#    .\demo_en_vivo.ps1 -SinStock             # pide mas unidades que el stock
#    .\demo_en_vivo.ps1 -ConChatbot           # ademas, un mensaje al chatbot
#    .\demo_en_vivo.ps1 -ConChatbot -Mensaje "Necesito hacer un reclamo por mi pedido"
#    .\demo_en_vivo.ps1 -Si                   # sin pedir confirmacion
#
#  Requisitos: docker compose up -d, y en n8n el Flujo 1 (y el Flujo 2
#  si se usa -ConChatbot) ACTIVOS y con sus credenciales cargadas.
# ============================================================

[CmdletBinding()]
param(
    # SKU del producto (ver catalogo en el dashboard o en el README)
    [string]$Sku = 'PROD-001',
    # Unidades a pedir (se ignora con -SinStock)
    [int]$Cantidad = 1,
    # Pide muchas mas unidades que el stock para forzar la rama "sin stock"
    [switch]$SinStock,
    # Ademas de la orden, manda un mensaje al webhook del chatbot
    [switch]$ConChatbot,
    # Texto del mensaje al chatbot (por defecto pregunta por el pedido recien creado)
    [string]$Mensaje,
    [string]$Cliente = 'Carolina Benítez',
    [string]$Email = 'carolina.benitez@example.com',
    [string]$Telefono = '5492615550142',
    [string]$N8nUrl = 'http://localhost:5678',
    # Salta la confirmacion interactiva
    [switch]$Si
)

$ErrorActionPreference = 'Stop'

# Cantidad que garantiza superar el stock de cualquier producto del catalogo
$cantidadSinStock = 9999

$fecha = Get-Date -Format 'yyyyMMddHHmmss'
$orderNumber = "ORD-DEMO-$fecha"
$unidades = if ($SinStock) { $cantidadSinStock } else { $Cantidad }

if ($unidades -lt 1) {
    Write-Host "ERROR: -Cantidad tiene que ser 1 o mas." -ForegroundColor Red
    exit 1
}
if ($Sku -notmatch '^[A-Za-z0-9_-]+$') {
    Write-Host "ERROR: -Sku solo admite letras, numeros, guion y guion bajo." -ForegroundColor Red
    exit 1
}

$urlOrden = "$N8nUrl/webhook/orden-nueva"
$urlChatbot = "$N8nUrl/webhook/whatsapp-business"

# ------------------------------------------------------------
# Envia un POST JSON en UTF-8 (para que los acentos lleguen bien)
# y devuelve Status / Content / Error sin cortar el script.
# ------------------------------------------------------------
function Invoke-Webhook {
    param([string]$Url, [hashtable]$Cuerpo)

    $json = $Cuerpo | ConvertTo-Json -Depth 5 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    try {
        $r = Invoke-WebRequest -Uri $Url -Method Post `
            -ContentType 'application/json; charset=utf-8' `
            -Body $bytes -UseBasicParsing -TimeoutSec 30
        return [pscustomobject]@{ Status = [int]$r.StatusCode; Content = [string]$r.Content; Error = $null }
    }
    catch {
        $status = 0
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        return [pscustomobject]@{ Status = $status; Content = $null; Error = $_.Exception.Message }
    }
}

# ------------------------------------------------------------
# Resumen y confirmacion
# ------------------------------------------------------------
Write-Host ""
Write-Host "DEMO EN VIVO" -ForegroundColor Cyan
Write-Host "  ADVERTENCIA: escribe en la BD compartida (orders" -ForegroundColor Yellow -NoNewline
if ($ConChatbot) { Write-Host ", interactions, tickets" -ForegroundColor Yellow -NoNewline }
Write-Host ")." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Orden:    $orderNumber"
Write-Host "  Producto: $Sku x $unidades$(if ($SinStock) { '  (forzando sin stock)' })"
Write-Host "  Cliente:  $Cliente <$Email>"
Write-Host "  n8n:      $N8nUrl"
if ($ConChatbot) { Write-Host "  Chatbot:  si, desde $Telefono" }
Write-Host ""

if (-not $Si) {
    $confirm = Read-Host "Disparar ahora? (s/n)"
    if ($confirm -ne 's') { exit 0 }
}

# ------------------------------------------------------------
# 1. Verificar que n8n responde
# ------------------------------------------------------------
Write-Host ""
Write-Host "[1/3] Verificando que n8n responde..."
try {
    $null = Invoke-WebRequest -Uri "$N8nUrl/healthz" -UseBasicParsing -TimeoutSec 5
    Write-Host "      OK -> $N8nUrl"
}
catch {
    Write-Host "ERROR: n8n no responde en $N8nUrl ($($_.Exception.Message))." -ForegroundColor Red
    Write-Host "       Levantalo con: docker compose up -d" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------
# 2. Orden nueva -> Flujo 1
# ------------------------------------------------------------
Write-Host "[2/3] Enviando la orden al Flujo 1..."
$orden = @{
    order_number   = $orderNumber
    customer_name  = $Cliente
    customer_email = $Email
    customer_phone = $Telefono
    product_sku    = $Sku
    quantity       = $unidades
}
$res = Invoke-Webhook -Url $urlOrden -Cuerpo $orden

if ($res.Status -eq 404) {
    Write-Host "ERROR: n8n no conoce el webhook $urlOrden." -ForegroundColor Red
    Write-Host "       El Flujo 1 tiene que estar ACTIVO en n8n ($N8nUrl)." -ForegroundColor Red
    exit 1
}
if ($res.Error) {
    Write-Host "ERROR: el webhook respondio con un fallo ($($res.Status)): $($res.Error)" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($res.Content)) {
    # n8n acepta la request pero la ejecucion falla despues (p. ej. credenciales sin cargar)
    Write-Host "      ATENCION: n8n respondio $($res.Status) SIN cuerpo." -ForegroundColor Yellow
    Write-Host "      Lo normal es que el Flujo 1 devuelva {success, order_number, status, ...}." -ForegroundColor Yellow
    Write-Host "      Casi seguro la ejecucion fallo: mira n8n -> Executions y revisa que las" -ForegroundColor Yellow
    Write-Host "      credenciales de Postgres y SMTP esten cargadas en los nodos." -ForegroundColor Yellow
    exit 1
}

try {
    $r = $res.Content | ConvertFrom-Json
    Write-Host "      OK -> HTTP $($res.Status)"
    Write-Host "      Pedido:  $($r.order_number)"
    Write-Host "      Estado:  $($r.status)"
    if ($null -ne $r.total_amount) { Write-Host "      Total:   $($r.total_amount)" }
    if ($r.message) { Write-Host "      Mensaje: $($r.message)" }
    if ($r.status -eq 'no_stock' -and -not $SinStock) {
        Write-Host "      (el producto no tenia stock suficiente para $unidades unidades)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "      OK -> HTTP $($res.Status) (respuesta no JSON):"
    Write-Host "      $($res.Content)"
}

# ------------------------------------------------------------
# 3. Mensaje al chatbot -> Flujo 2 (opcional)
# ------------------------------------------------------------
if ($ConChatbot) {
    Write-Host "[3/3] Enviando un mensaje al chatbot (Flujo 2)..."
    if ([string]::IsNullOrWhiteSpace($Mensaje)) {
        $Mensaje = "Hola, quiero saber el estado de mi pedido $orderNumber"
    }
    # Payload PLANO que entiende el nodo "Normalizar Mensaje" (no la envoltura
    # entry[].changes[] de la Cloud API: ver docs/DESVIOS_SPEC.md 2.4).
    $mensajeBot = @{
        from = $Telefono
        text = @{ body = $Mensaje }
        name = $Cliente
    }
    # Un respiro para que la orden ya este registrada cuando el bot la consulte
    Start-Sleep -Seconds 2
    $bot = Invoke-Webhook -Url $urlChatbot -Cuerpo $mensajeBot

    if ($bot.Status -eq 404) {
        Write-Host "      ATENCION: el webhook $urlChatbot no existe: el Flujo 2 no esta activo." -ForegroundColor Yellow
    }
    elseif ($bot.Error) {
        Write-Host "      ATENCION: el chatbot respondio con un fallo ($($bot.Status)): $($bot.Error)" -ForegroundColor Yellow
    }
    else {
        Write-Host "      OK -> HTTP $($bot.Status): '$Mensaje'"
        Write-Host "      (el webhook no devuelve la respuesta del bot: contesta por su canal y"
        Write-Host "       deja la interaccion registrada en la tabla interactions)"
    }
}
else {
    Write-Host "[3/3] Chatbot: omitido (usa -ConChatbot para mandar un mensaje)."
}

Write-Host ""
Write-Host "Listo. Mira el dashboard: http://localhost:8080 -> Pedidos (se actualiza solo cada 4 s)."
Write-Host ""
