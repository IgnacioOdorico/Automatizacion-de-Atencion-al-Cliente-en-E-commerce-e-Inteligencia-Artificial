<#
.SYNOPSIS
    E8 — Un bloque del experimento: fija una condición de prompt en el workflow
    vigente, pasa el corpus de 150 mensajes y guarda la evidencia de qué prompt
    corrió en cada ejecución.

.DESCRIPTION
    1. Exporta la versión publicada del workflow "Flujo 2 — Chatbot WhatsApp +
       Telegram", reemplaza SOLO el prompt del nodo de inferencia por el de la
       condición (condiciones_e8.py verifica que no cambie nada más), la importa,
       la publica y reinicia n8n.
    2. Verifica en la base que la versión activa tenga el md5 del prompt de la
       condición. Si no coincide, aborta sin enviar nada.
    3. Envía el corpus con user_id E8-<condición>-R<repetición>-<id>@whatsapp.sim.
    4. Concilia filas escritas y exporta, por ejecución, el md5 del prompt que
       n8n guardó en su copia del workflow. Esa es la prueba de qué condición
       corrió en cada llamada.

.PARAMETER Condicion   C1, C2, C3 o C4 (ver condiciones_e8.py).
.PARAMETER Repeticion  1, 2 o 3.
.PARAMETER Intento     1 por defecto. Un bloque inválido se vuelve a correr con Intento 2, 3...:
                       prefijo E8-<condición>-R<repetición>i<intento>- y los datos del intento
                       anterior quedan intactos (regla pre-registrada: se informan ambos).
.PARAMETER Prueba      Envía solo N mensajes con prefijo E8-PRUEBA- (no entran al análisis).
.PARAMETER EspaciadoSeg Segundos entre envíos (por defecto 1).
.PARAMETER Force       Sin confirmación interactiva.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('C1','C2','C3','C4')][string]$Condicion,
    [ValidateRange(1,3)][int]$Repeticion = 1,
    [ValidateRange(1,9)][int]$Intento = 1,
    [int]$Prueba = 0,
    [int]$EspaciadoSeg = 1,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\E1\_comun.ps1')

$WfId       = 'GyT06kIZgB5Kmw4P'
$NodoIA     = 'IA - Motor Decision'
$UrlChatbot = 'http://localhost:5678/webhook/whatsapp-business'
$Corpus     = Join-Path $PSScriptRoot '..\E2\corpus_intents.csv'
$DirSalida  = Join-Path $PSScriptRoot 'resultados'
$Sello      = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$Nombre     = 'Anotador E2'          # el mismo nombre que la corrida del 12/08
$SufijoInt  = if ($Intento -gt 1) { "i$Intento" } else { '' }
$Prefijo    = if ($Prueba -gt 0) { "E8-PRUEBA-$Condicion-" } else { "E8-$Condicion-R$Repeticion$SufijoInt-" }
$Bloque     = if ($Prueba -gt 0) { "prueba_$Condicion" } else { "$Condicion`_R$Repeticion" + $(if ($Intento -gt 1) { "_i$Intento" } else { '' }) }

$condiciones = Get-Content (Join-Path $PSScriptRoot 'condiciones_e8.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Md5Esperado = $condiciones.condiciones.$Condicion.md5

function Invoke-Nativo {
    param([Parameter(Mandatory)][string[]]$Argumentos)
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $salida = & docker @Argumentos 2>&1 } finally { $ErrorActionPreference = $prev }
    if ($LASTEXITCODE -ne 0) { throw ("docker " + ($Argumentos -join ' ') + " fallo:`n" + ($salida -join "`n")) }
    return $salida
}

function Get-Md5Activo {
    $sql = @"
SELECT md5(n->'parameters'->'messages'->'messageValues'->0->>'message')
FROM workflow_entity w
JOIN workflow_history h ON h."versionId" = w."activeVersionId"
CROSS JOIN LATERAL json_array_elements(h.nodes) n
WHERE w.id = '$WfId' AND w.active AND n->>'name' = '$NodoIA';
"@
    return ("" + (Get-Escalar -Sql $sql)).Trim()
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host (" E8 — bloque {0}  (prefijo {1})" -f $Bloque, $Prefijo) -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ------------------------------------------------------------ 1. verificación previa
$nombres = docker ps --format '{{.Names}}' 2>$null
if ($nombres -notcontains 'tesis_postgres' -or $nombres -notcontains 'tesis_n8n') { throw 'Los contenedores no están arriba.' }
$cred = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM credentials_entity WHERE type = 'openAiApi';")
if ($cred -lt 1) { throw 'No hay credencial openAiApi en n8n.' }
$filas = Import-Csv -Path $Corpus -Encoding UTF8
if ($filas.Count -ne 150) { throw "El corpus tiene $($filas.Count) filas; se esperaban 150." }
if ($Prueba -gt 0) { $filas = $filas | Select-Object -First $Prueba }
$previas = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM interactions WHERE user_id LIKE '$Prefijo%';")
if ($previas -gt 0 -and $Prueba -eq 0) { throw "El bloque $Bloque ya tiene $previas filas. No se repite un bloque sobre datos existentes." }
Write-Host "  [OK] contenedores, credencial y corpus ($($filas.Count) mensajes)"

if (-not $Force) {
    $r = Read-Host "`nEjecutar el bloque $Bloque? Cambia el prompt activo, reinicia n8n y consume cuota de OpenAI. (s/N)"
    if ($r -notin @('s','S','si','SI')) { Write-Host 'Cancelado.'; return }
}
if (-not (Test-Path $DirSalida)) { $null = New-Item -ItemType Directory -Path $DirSalida }

# ------------------------------------------------------------ 2. fijar la condición
Write-Host "`n=== Condición $Condicion (md5 esperado $Md5Esperado) ===" -ForegroundColor Cyan
if ((Get-Md5Activo) -eq $Md5Esperado) {
    Write-Host '  El prompt activo ya es el de esta condición; no se reimporta.'
} else {
    $tmp = Join-Path $env:TEMP "e8_$Sello"
    $null = New-Item -ItemType Directory -Path $tmp
    Invoke-Nativo @('exec', 'tesis_n8n', 'n8n', 'export:workflow', "--id=$WfId", '--published', '--output=/tmp/e8_base.json') | Out-Null
    Invoke-Nativo @('cp', 'tesis_n8n:/tmp/e8_base.json', (Join-Path $tmp 'base.json')) | Out-Null
    $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    & python (Join-Path $PSScriptRoot 'condiciones_e8.py') workflow --base (Join-Path $tmp 'base.json') --condicion $Condicion --salida (Join-Path $tmp 'wf.json')
    $codigo = $LASTEXITCODE; $ErrorActionPreference = $prev
    if ($codigo -ne 0) { throw 'condiciones_e8.py no pudo armar el workflow de la condición.' }
    Invoke-Nativo @('cp', (Join-Path $tmp 'wf.json'), 'tesis_n8n:/tmp/e8_wf.json') | Out-Null
    Invoke-Nativo @('exec', 'tesis_n8n', 'n8n', 'import:workflow', '--input=/tmp/e8_wf.json') | Out-Null
    Invoke-Nativo @('exec', 'tesis_n8n', 'n8n', 'publish:workflow', "--id=$WfId") | Out-Null
    Write-Host '  importado y publicado; reiniciando n8n...'
    Invoke-Nativo @('restart', 'tesis_n8n') | Out-Null
    $listo = $false
    for ($k = 0; $k -lt 60; $k++) {
        Start-Sleep -Seconds 2
        try { if ((Invoke-WebRequest -Uri 'http://localhost:5678/healthz/readiness' -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200) { $listo = $true; break } } catch {}
    }
    if (-not $listo) { throw 'n8n no quedó listo después del reinicio.' }
    Start-Sleep -Seconds 8
}
$md5Activo = Get-Md5Activo
if ($md5Activo -ne $Md5Esperado) { throw "El prompt activo tiene md5 $md5Activo y la condición $Condicion espera $Md5Esperado. No se envía nada." }
$hooks = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM webhook_entity WHERE ""webhookPath"" = 'whatsapp-business';")
if ($hooks -lt 1) { throw 'El webhook whatsapp-business no está registrado.' }
Write-Host "  [OK] versión activa con el prompt de $Condicion y webhook registrado" -ForegroundColor Green

# ------------------------------------------------------------ 3. envío
Write-Host "`n=== Envío ===" -ForegroundColor Cyan
$inicioUtc = (Get-Date).ToUniversalTime()
$envios = New-Object System.Collections.Generic.List[object]
$i = 0
foreach ($fila in $filas) {
    $i++
    $uid = "$Prefijo$($fila.user_id)@whatsapp.sim"
    $cuerpo = @{ user_id = $uid; name = $Nombre; message = $fila.mensaje } | ConvertTo-Json -Compress
    $tEnvio = (Get-Date).ToUniversalTime()
    $cron = [System.Diagnostics.Stopwatch]::StartNew()
    $estadoHttp = $null; $mensajeError = $null
    try {
        $resp = Invoke-WebRequest -Uri $UrlChatbot -Method POST -ContentType 'application/json; charset=utf-8' `
                    -Body ([System.Text.Encoding]::UTF8.GetBytes($cuerpo)) -UseBasicParsing -TimeoutSec 90
        $estadoHttp = $resp.StatusCode
    } catch {
        $estadoHttp = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        $mensajeError = $_.Exception.Message
    }
    $cron.Stop()
    $envios.Add([pscustomobject]@{ id = $fila.id; user_id = $uid; enviado_utc = $tEnvio.ToString('yyyy-MM-dd HH:mm:ss.fff')
                                   http = $estadoHttp; latencia_ms = [int]$cron.ElapsedMilliseconds; error = $mensajeError })
    if ($i % 25 -eq 0 -or $estadoHttp -ne 200) {
        Write-Host ("  [{0,3}/{1}] HTTP {2}  {3} ms" -f $i, $filas.Count, $estadoHttp, $cron.ElapsedMilliseconds)
    }
    if ($i -lt $filas.Count) { Start-Sleep -Seconds $EspaciadoSeg }
}
$finUtc = (Get-Date).ToUniversalTime()
$envios | Export-Csv -Path (Join-Path $DirSalida "e8_envios_$Bloque.csv") -NoTypeInformation -Encoding UTF8

# ------------------------------------------------------------ 4. conciliación y evidencia
# El webhook responde al recibir, antes de que termine el workflow: se espera a que no
# quede ninguna ejecucion en curso (hasta 120 s) en lugar de un tiempo fijo.
$okHttp = ($envios | Where-Object { $_.http -eq 200 }).Count
$desde = $inicioUtc.AddSeconds(-5).ToString('yyyy-MM-dd HH:mm:ss')
for ($espera = 0; $espera -lt 60; $espera++) {
    Start-Sleep -Seconds 2
    $enCurso  = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM execution_entity WHERE ""workflowId"" = '$WfId' AND ""startedAt"" >= '$desde'::timestamp AND status IN ('new','running','waiting');")
    $escritas = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM interactions WHERE user_id LIKE '$Prefijo%';")
    if ($enCurso -eq 0 -and $escritas -ge $filas.Count) { break }
}
Start-Sleep -Seconds 2
$escritas = [int](Get-Escalar -Sql "SELECT COUNT(*) FROM interactions WHERE user_id LIKE '$Prefijo%';")
$hasta = (Get-Date).ToUniversalTime().AddSeconds(5).ToString('yyyy-MM-dd HH:mm:ss')
$evid = Invoke-Psql -Tuplas -Sql @"
SELECT e.id, to_char(e."startedAt" AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS.MS'), e.status, d."workflowVersionId",
       md5((SELECT n->'parameters'->'messages'->'messageValues'->0->>'message'
            FROM json_array_elements(d."workflowData"::json->'nodes') n WHERE n->>'name' = '$NodoIA'))
FROM execution_entity e JOIN execution_data d ON d."executionId" = e.id
WHERE e."workflowId" = '$WfId' AND e."startedAt" >= '$desde'::timestamp AND e."startedAt" <= '$hasta'::timestamp
ORDER BY e.id;
"@
$ejecuciones = @($evid | Where-Object { $_ -ne '' } | ForEach-Object {
    $c = $_ -split "`t"
    [pscustomobject]@{ execution_id = $c[0]; inicio_utc = $c[1]; estado = $c[2]; version_id = $c[3]; md5_prompt = $c[4] }
})
$ejecuciones | Export-Csv -Path (Join-Path $DirSalida "e8_evidencia_$Bloque.csv") -NoTypeInformation -Encoding UTF8
$conMd5  = ($ejecuciones | Where-Object { $_.md5_prompt -eq $Md5Esperado }).Count
$exitos  = ($ejecuciones | Where-Object { $_.estado -eq 'success' }).Count
$ajenas  = ($ejecuciones | Where-Object { $_.md5_prompt -ne $Md5Esperado }).Count

Write-Host "`n=== Conciliación ===" -ForegroundColor Cyan
Write-Host "  HTTP 200 ............ $okHttp de $($filas.Count)"
Write-Host "  filas en interactions $escritas"
Write-Host "  ejecuciones ......... $($ejecuciones.Count) (éxito $exitos; con el prompt de $Condicion $conMd5; con otro prompt $ajenas)"
$valido = ($okHttp -eq $filas.Count) -and ($escritas -eq $filas.Count) -and ($ajenas -eq 0) -and ($conMd5 -ge $filas.Count)

$commit = (git -C (Join-Path $PSScriptRoot '..\..') rev-parse --short HEAD 2>$null)
[ordered]@{
    experimento = 'E8 - factorial 2x2 base x reglas-y-ejemplos'; bloque = $Bloque; condicion = $Condicion
    repeticion = $Repeticion; intento = $Intento; prueba = ($Prueba -gt 0); prefijo_user_id = $Prefijo; mensajes = $filas.Count
    md5_prompt = $Md5Esperado; caracteres_prompt = $condiciones.condiciones.$Condicion.caracteres
    workflow_id = $WfId; endpoint = $UrlChatbot; espaciado_seg = $EspaciadoSeg; nombre_cliente = $Nombre
    temperatura = 'no fijada en el nodo: rige el valor por defecto de la API de OpenAI (1)'
    inicio_utc = $inicioUtc.ToString('yyyy-MM-dd HH:mm:ss'); fin_utc = $finUtc.ToString('yyyy-MM-dd HH:mm:ss')
    http_200 = $okHttp; filas_escritas = $escritas; ejecuciones = $ejecuciones.Count
    ejecuciones_con_prompt_de_la_condicion = $conMd5; ejecuciones_con_otro_prompt = $ajenas
    valido = $valido; commit_git = $commit
} | ConvertTo-Json | Set-Content -Path (Join-Path $DirSalida "e8_manifiesto_$Bloque.json") -Encoding UTF8

if (-not $valido) { throw "Bloque $Bloque INVÁLIDO: revisar la conciliación antes de seguir." }
Write-Host "`n  Bloque $Bloque válido." -ForegroundColor Green
