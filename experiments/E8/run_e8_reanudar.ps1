<#
.SYNOPSIS
    E8 — Reanuda la corrida desde el bloque 9 despues del bloque invalido C3_R3.

.DESCRIPTION
    El bloque 9 (C3 R3) resulto invalido: 149 filas de 150. El modelo devolvio la
    etiqueta "CAMBIO", fuera de las cuatro admitidas, y la restriccion de la tabla
    interactions rechazo el registro. Segun la regla pre-registrada, el bloque se
    vuelve a correr (intento 2, prefijo E8-C3-R3i2-) y se informan los dos intentos.
    Sigue el orden pre-registrado: C3 R3, C4 R3, C2 R3, C1 R3.
#>
[CmdletBinding()]
param([int]$EspaciadoSeg = 1)
$ErrorActionPreference = 'Stop'
$orden = @( @('C3', 3, 2), @('C4', 3, 1), @('C2', 3, 1), @('C1', 3, 1) )
$inicio = Get-Date
$k = 8
foreach ($b in $orden) {
    $k++
    Write-Host ("`n##### Bloque {0}/12: {1} R{2} intento {3}  ({4:HH:mm:ss})" -f $k, $b[0], $b[1], $b[2], (Get-Date)) -ForegroundColor Magenta
    & (Join-Path $PSScriptRoot 'run_e8.ps1') -Condicion $b[0] -Repeticion $b[1] -Intento $b[2] -EspaciadoSeg $EspaciadoSeg -Force
}
$prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& docker exec tesis_n8n n8n export:workflow --id=GyT06kIZgB5Kmw4P --published --output=/tmp/e8_final.json 2>&1 | Out-Null
& docker cp tesis_n8n:/tmp/e8_final.json (Join-Path $PSScriptRoot 'resultados\workflow_final_C1.json') 2>&1 | Out-Null
$ErrorActionPreference = $prev
Write-Host ("`nE8 completo en {0:N0} minutos. Workflow vigente: C1. Siguiente paso: python analizar_e8.py" -f ((Get-Date) - $inicio).TotalMinutes) -ForegroundColor Green
