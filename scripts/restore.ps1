# ============================================================
#  RESTORE — Tesis UTN FRM
#  Restaura todo desde un backup previo
#  Uso: .\restore.ps1
#  
#  IMPORTANTE: Correr DESPUÉS de docker compose up -d
#              y ANTES de configurar nada en n8n
# ============================================================

# Buscar el backup más reciente
$backups = Get-ChildItem "backups" -Directory | Sort-Object Name -Descending
if ($backups.Count -eq 0) {
    Write-Host "ERROR: No hay backups en la carpeta 'backups\'" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Backups disponibles:"
$backups | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host ""

$ultimo = $backups[0].Name
$confirm = Read-Host "Restaurar desde '$ultimo'? (s/n)"
if ($confirm -ne "s") { exit 0 }

$dir = "backups\$ultimo"

Write-Host ""
Write-Host "Restaurando desde: $dir"
Write-Host ""

# Esperar que PostgreSQL esté listo
Write-Host "Esperando PostgreSQL..."
Start-Sleep -Seconds 5

# Restaurar backup completo
Write-Host "[1/1] Restaurando base de datos completa..."
Get-Content "$dir\full_backup.sql" | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
Write-Host "      OK"

Write-Host ""
Write-Host "Restauracion completada."
Write-Host "Reinicia n8n para que tome los cambios:"
Write-Host "  docker compose restart n8n"
Write-Host ""
