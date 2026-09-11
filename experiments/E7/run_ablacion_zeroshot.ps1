<#
.SYNOPSIS
    E7 — Ablación: el mismo corpus de 150 mensajes, sin contexto de FAQ y sin
    ejemplos etiquetados.

.DESCRIPTION
    El accuracy del 92,7 % que reporta el Capítulo 5 se midió el 2026-08-12 con
    el workflow "Flujo 2 — Chatbot Omnicanal IA" (14 nodos), cuyo prompt de
    sistema tenía 6338 caracteres e incluía tres cosas: la base de conocimiento
    inyectada con {{ $json.faq_context }}, siete ejemplos etiquetados y una
    sección de reglas de clasificación por categoría.

    El workflow vigente, "Flujo 2 — Chatbot WhatsApp + Telegram" (19 nodos),
    tiene un prompt de 1032 caracteres sin nada de eso: enumera las categorías
    y fija el formato de salida. Es el régimen zero-shot.

    Este experimento pasa EL MISMO corpus por el prompt reducido, de modo que la
    comparación entre ambos sea una ablación y no dos mediciones sueltas.

    La corrida se marca con el prefijo E7- en user_id para que quede separada de
    la del 12/08 de manera permanente, sin depender de una ventana temporal.

.PARAMETER EspaciadoSeg
    Segundos entre envíos. Por defecto 3, para no golpear el rate limit.

.PARAMETER DryRun
    Verifica el entorno y muestra el plan, sin enviar nada.

.PARAMETER Force
    Omite la confirmación interactiva.
#>

[CmdletBinding()]
param(
    [int]   $EspaciadoSeg = 3,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\E1\_comun.ps1')

$UrlChatbot = 'http://localhost:5678/webhook/whatsapp-business'
$Corpus     = Join-Path $PSScriptRoot '..\E2\corpus_intents.csv'
$DirSalida  = Join-Path $PSScriptRoot 'resultados'
$Sello      = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$Prefijo    = 'E7-'

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " E7 - Ablacion: corpus de 150 sin contexto de FAQ           " -ForegroundColor Cyan
Write-Host " Endpoint: $UrlChatbot" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ------------------------------------------------------------
#  1. Verificacion previa
# ------------------------------------------------------------
Write-Host "`n=== Verificacion previa ===" -ForegroundColor Cyan

$nombres = docker ps --format '{{.Names}}' 2>$null
if ($nombres -notcontains 'tesis_postgres' -or $nombres -notcontains 'tesis_n8n') {
    throw "Los contenedores no estan arriba. Ejecuta: docker compose up -d"
}
Write-Host "  [OK] Contenedores arriba"

$ping = Get-Escalar -Sql "SELECT 1;"
if ("$ping".Trim() -ne '1') { throw "PostgreSQL no responde." }
Write-Host "  [OK] PostgreSQL responde"

# --- LA verificacion de este experimento: que prompt va a correr ---
$fila = Invoke-Psql -Tuplas -Sql @"
SELECT w.name,
       jsonb_array_length(w.nodes::jsonb),
       length(n->'parameters'->'messages'->'messageValues'->0->>'message'),
       ((n->'parameters'->'messages'->'messageValues'->0->>'message') LIKE '%faq_context%')::text,
       ((n->'parameters'->'messages'->'messageValues'->0->>'message') LIKE '%## EJEMPLOS%')::text
FROM workflow_entity w, jsonb_array_elements(w.nodes::jsonb) n
WHERE w.active AND w.name LIKE 'Flujo 2%' AND w.name NOT LIKE '%PRODUCCION%'
  AND n->>'name' = 'IA - Motor Decision';
"@
$c = (($fila | Where-Object { $_ -ne '' } | Select-Object -First 1) -split "`t")
if ($c.Count -lt 5) { throw "No pude leer el nodo de inferencia del Flujo 2 activo." }

$wfNombre = $c[0].Trim()
$wfNodos  = [int]$c[1].Trim()
$promptN  = [int]$c[2].Trim()
$tieneFaq = ($c[3].Trim() -eq 'true')
$tieneEj  = ($c[4].Trim() -eq 'true')

Write-Host "  Workflow activo : $wfNombre ($wfNodos nodos)"
Write-Host "  Prompt          : $promptN caracteres"
Write-Host "  Inyecta FAQ     : $tieneFaq"
Write-Host "  Tiene ejemplos  : $tieneEj"

if ($tieneFaq -or $tieneEj) {
    throw "El workflow activo INYECTA contexto de FAQ o trae ejemplos etiquetados. Este experimento mide la condicion SIN ellos: activa 'Flujo 2 - Chatbot WhatsApp + Telegram' en http://localhost:5678 y volve a correr."
}
Write-Host "  [OK] Condicion de ablacion verificada: sin FAQ, sin ejemplos" -ForegroundColor Green

$cred = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM credentials_entity WHERE type = 'openAiApi';")
if ($cred -lt 1) {
    Write-Warning "  No hay credencial openAiApi. Si el nodo no autentica, TODO cae al catch y se registra como GENERAL."
} else { Write-Host "  [OK] Credencial de OpenAI configurada" }

$yaCorrio = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM interactions WHERE user_id LIKE '$Prefijo%';")
if ($yaCorrio -gt 0) {
    Write-Warning "  Ya hay $yaCorrio filas con prefijo '$Prefijo'. Se van a sumar a las nuevas: borralas antes si queres una corrida limpia."
    Write-Host "    DELETE FROM interactions WHERE user_id LIKE '$Prefijo%';" -ForegroundColor DarkGray
}

# ------------------------------------------------------------
#  2. Corpus
# ------------------------------------------------------------
if (-not (Test-Path $Corpus)) { throw "No encuentro el corpus en $Corpus" }
$filas = Import-Csv -Path $Corpus -Encoding UTF8
if ($filas.Count -ne 150) { Write-Warning "  El corpus tiene $($filas.Count) filas, se esperaban 150." }
Write-Host "  [OK] Corpus: $($filas.Count) mensajes (el mismo de la corrida del 12/08)"

$duracionMin = [math]::Round(($filas.Count * $EspaciadoSeg) / 60, 1)
Write-Host "`n--- Plan ---" -ForegroundColor Yellow
Write-Host "  Mensajes  : $($filas.Count)"
Write-Host "  Espaciado : ${EspaciadoSeg}s  ->  ~$duracionMin minutos"
Write-Host "  user_id   : prefijo '$Prefijo' (separa esta corrida de la del 12/08)"
Write-Host "  Condicion : prompt de $promptN caracteres, sin FAQ, sin ejemplos"
Write-Host "  Costo     : ~USD 0,05 en gpt-4o-mini"

if ($DryRun) {
    Write-Host "`n[DryRun] Primeros 5 envios:" -ForegroundColor Yellow
    $filas | Select-Object -First 5 | ForEach-Object {
        Write-Host "  #$($_.id) [$Prefijo$($_.user_id)] $($_.mensaje)"
    }
    Write-Host "`n[DryRun] No se envio nada." -ForegroundColor Yellow
    return
}

if (-not $Force) {
    $r = Read-Host "`nEjecutar? Consume cuota de OpenAI y escribe en la BD. (s/N)"
    if ($r -notin @('s','S','si','SI')) { Write-Host "Cancelado."; return }
}

# ------------------------------------------------------------
#  3. Envio
# ------------------------------------------------------------
if (-not (Test-Path $DirSalida)) { $null = New-Item -ItemType Directory -Path $DirSalida }

$inicioUtc = (Get-Date).ToUniversalTime()
$envios = New-Object System.Collections.Generic.List[object]
$i = 0

foreach ($fila in $filas) {
    $i++
    # El nodo de envio del workflow vigente usa toEmail = {{ $json.user }} sin
    # sufijo, de modo que un user_id numerico lo hace fallar con "No recipients
    # defined" y el flujo muere ANTES de Registrar Interaccion. Se manda con
    # forma de direccion, que es lo que el workflow anterior construia por
    # dentro. El user_id no llega al prompt (text = {{ $json.message }}), asi
    # que esto no altera la condicion medida.
    $uid = "$Prefijo$($fila.user_id)@whatsapp.sim"
    $cuerpo = @{ user_id = $uid; name = 'Anotador E7'; message = $fila.mensaje } | ConvertTo-Json -Compress

    $tEnvio = (Get-Date).ToUniversalTime()
    $cron = [System.Diagnostics.Stopwatch]::StartNew()
    $estadoHttp = $null; $mensajeError = $null
    try {
        $resp = Invoke-WebRequest -Uri $UrlChatbot -Method POST `
                    -ContentType 'application/json; charset=utf-8' `
                    -Body ([System.Text.Encoding]::UTF8.GetBytes($cuerpo)) `
                    -UseBasicParsing -TimeoutSec 60
        $estadoHttp = $resp.StatusCode
    } catch {
        $estadoHttp = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        $mensajeError = $_.Exception.Message
    }
    $cron.Stop()

    $envios.Add([pscustomobject]@{
        id = $fila.id; user_id = $uid; mensaje = $fila.mensaje
        enviado_utc = $tEnvio.ToString('yyyy-MM-dd HH:mm:ss.fff')
        http = $estadoHttp; latencia_ms = [int]$cron.ElapsedMilliseconds; error = $mensajeError
    })

    $marca = if ($estadoHttp -eq 200) { 'OK ' } else { 'ERR' }
    Write-Host ("  [{0,3}/{1}] {2} {3,4}ms  {4}" -f $i, $filas.Count, $marca,
                $cron.ElapsedMilliseconds, $fila.mensaje.Substring(0, [math]::Min(46, $fila.mensaje.Length)))
    if ($i -lt $filas.Count) { Start-Sleep -Seconds $EspaciadoSeg }
}
$finUtc = (Get-Date).ToUniversalTime()

$rutaEnvios = Join-Path $DirSalida "e7_envios_$Sello.csv"
$envios | Export-Csv -Path $rutaEnvios -NoTypeInformation -Encoding UTF8
Write-Host "`n  Envios -> $rutaEnvios"

# ------------------------------------------------------------
#  4. Conciliacion
# ------------------------------------------------------------
Write-Host "`n=== Conciliacion ===" -ForegroundColor Cyan
Start-Sleep -Seconds 5
$okHttp = ($envios | Where-Object { $_.http -eq 200 }).Count
Write-Host "  Enviados con HTTP 200: $okHttp de $($filas.Count)"
$escritos = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM interactions WHERE user_id LIKE '$Prefijo%';")
Write-Host "  Filas escritas en interactions: $escritos"
if ($escritos -ne $filas.Count) {
    Write-Warning "  FALTAN $($filas.Count - $escritos) filas. El accuracy no es publicable hasta reconciliar."
}

# ------------------------------------------------------------
#  5. Manifiesto - que condicion corrio, exactamente
# ------------------------------------------------------------
$commit = (git -C (Join-Path $PSScriptRoot '..\..') rev-parse --short HEAD 2>$null)
$manifiesto = [ordered]@{
    experimento       = 'E7 - ablacion sin contexto de FAQ'
    corpus            = 'experiments/E2/corpus_intents.csv'
    mensajes          = $filas.Count
    prefijo_user_id   = $Prefijo
    workflow          = $wfNombre
    workflow_nodos    = $wfNodos
    prompt_caracteres = $promptN
    inyecta_faq       = $tieneFaq
    tiene_ejemplos    = $tieneEj
    endpoint          = $UrlChatbot
    espaciado_seg     = $EspaciadoSeg
    inicio_utc        = $inicioUtc.ToString('yyyy-MM-dd HH:mm:ss')
    fin_utc           = $finUtc.ToString('yyyy-MM-dd HH:mm:ss')
    http_200          = $okHttp
    filas_escritas    = $escritos
    commit_git        = $commit
}
$rutaMan = Join-Path $DirSalida "e7_manifiesto_$Sello.json"
$manifiesto | ConvertTo-Json -Depth 4 | Set-Content -Path $rutaMan -Encoding UTF8
Write-Host "  Manifiesto -> $rutaMan"

Write-Host "`nListo. Siguiente paso:" -ForegroundColor Green
Write-Host "  python analizar_e7.py"
