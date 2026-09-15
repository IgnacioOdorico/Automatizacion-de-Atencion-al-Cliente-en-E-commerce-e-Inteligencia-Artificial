<#
.SYNOPSIS
    E8 — Corre los 12 bloques en el orden pre-registrado y deja C1 como
    configuración vigente.

.DESCRIPTION
    Orden fijado de antemano para que ninguna condición ocupe dos veces la
    misma posición dentro de su repetición (control de deriva temporal del
    proveedor de inferencia):

        R1: C1 C2 C4 C3
        R2: C2 C3 C1 C4
        R3: C3 C4 C2 C1

    El último bloque es C1, de modo que al terminar el workflow vigente queda con
    el prompt de la configuración principal. Se exporta esa versión publicada a
    resultados/workflow_final_C1.json.

    Si un bloque resulta inválido, la corrida se detiene: no se sigue sobre una
    conciliación rota.
#>
[CmdletBinding()]
param([int]$EspaciadoSeg = 1)

$ErrorActionPreference = 'Stop'
$orden = @(
    @('C1', 1), @('C2', 1), @('C4', 1), @('C3', 1),
    @('C2', 2), @('C3', 2), @('C1', 2), @('C4', 2),
    @('C3', 3), @('C4', 3), @('C2', 3), @('C1', 3)
)
$inicio = Get-Date
$k = 0
foreach ($b in $orden) {
    $k++
    Write-Host ("`n##### Bloque {0}/12: {1} R{2}  ({3:HH:mm:ss})" -f $k, $b[0], $b[1], (Get-Date)) -ForegroundColor Magenta
    & (Join-Path $PSScriptRoot 'run_e8.ps1') -Condicion $b[0] -Repeticion $b[1] -EspaciadoSeg $EspaciadoSeg -Force
}
$prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& docker exec tesis_n8n n8n export:workflow --id=GyT06kIZgB5Kmw4P --published --output=/tmp/e8_final.json 2>&1 | Out-Null
& docker cp tesis_n8n:/tmp/e8_final.json (Join-Path $PSScriptRoot 'resultados\workflow_final_C1.json') 2>&1 | Out-Null
$ErrorActionPreference = $prev
Write-Host ("`nE8 completo en {0:N0} minutos. Workflow vigente: C1. Siguiente paso: python analizar_e8.py" -f ((Get-Date) - $inicio).TotalMinutes) -ForegroundColor Green
