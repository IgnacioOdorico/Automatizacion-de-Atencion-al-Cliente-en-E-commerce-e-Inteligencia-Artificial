<#
.SYNOPSIS
    E8 - Bloques 10 a 12 (C4 R3, C2 R3, C1 R3) tras el desvio declarado sobre etiquetas fuera de vocabulario.
#>
[CmdletBinding()]
param([int]$EspaciadoSeg = 1)
$ErrorActionPreference = 'Stop'
$orden = @( @('C4', 3), @('C2', 3), @('C1', 3) )
$k = 9
foreach ($b in $orden) {
    $k++
    Write-Host ("`n##### Bloque {0}/12: {1} R{2}  ({3:HH:mm:ss})" -f $k, $b[0], $b[1], (Get-Date)) -ForegroundColor Magenta
    & (Join-Path $PSScriptRoot 'run_e8.ps1') -Condicion $b[0] -Repeticion $b[1] -EspaciadoSeg $EspaciadoSeg -Force
}
$prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& docker exec tesis_n8n n8n export:workflow --id=GyT06kIZgB5Kmw4P --published --output=/tmp/e8_final.json 2>&1 | Out-Null
& docker cp tesis_n8n:/tmp/e8_final.json (Join-Path $PSScriptRoot 'resultados\workflow_final_C1.json') 2>&1 | Out-Null
$ErrorActionPreference = $prev
Write-Host "`nE8 completo. Workflow vigente: C1. Siguiente paso: python analizar_e8.py" -ForegroundColor Green
