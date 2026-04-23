# ============================================================
#  BACKUP — Tesis UTN FRM
#  Guarda credenciales y workflows de n8n desde PostgreSQL
#  Uso: .\backup.ps1
# ============================================================

$fecha = Get-Date -Format "yyyy-MM-dd_HH-mm"
$dir = "backups\$fecha"
New-Item -ItemType Directory -Path $dir -Force | Out-Null

Write-Host ""
Write-Host "Haciendo backup en: $dir"
Write-Host ""

# 1. Workflows de n8n
Write-Host "[1/4] Exportando workflows..."
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "\COPY (SELECT id, name, active, nodes, connections, settings, `"updatedAt`" FROM workflow_entity ORDER BY id) TO STDOUT WITH CSV HEADER" > "$dir\n8n_workflows.csv"
Write-Host "      OK -> $dir\n8n_workflows.csv"

# 2. Credenciales de n8n (encriptadas, pero alcanza para restaurar)
Write-Host "[2/4] Exportando credenciales..."
docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "\COPY (SELECT id, name, type, data, `"updatedAt`" FROM credentials_entity ORDER BY id) TO STDOUT WITH CSV HEADER" > "$dir\n8n_credentials.csv"
Write-Host "      OK -> $dir\n8n_credentials.csv"

# 3. Datos de la tesis (tablas propias)
Write-Host "[3/4] Exportando datos de la tesis..."
docker exec tesis_postgres pg_dump -U n8n_user -d ecommerce_tesis `
    --table=products --table=orders --table=interactions --table=tickets --table=faq_responses `
    --data-only --inserts > "$dir\tesis_data.sql"
Write-Host "      OK -> $dir\tesis_data.sql"

# 4. Backup completo de la BD (por las dudas)
Write-Host "[4/4] Backup completo de PostgreSQL..."
docker exec tesis_postgres pg_dump -U n8n_user -d ecommerce_tesis > "$dir\full_backup.sql"
Write-Host "      OK -> $dir\full_backup.sql"

# 5. Copiar JSONs de workflows
Write-Host "[5/5] Copiando workflows JSON..."
Copy-Item "workflows\*" "$dir\" -ErrorAction SilentlyContinue
Write-Host "      OK -> JSONs copiados"

Write-Host ""
Write-Host "Backup completado en: $dir"
Write-Host ""
