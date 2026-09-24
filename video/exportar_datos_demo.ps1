# ============================================================
#  exportar_datos_demo.ps1 — volcado de la base PARA COMPARTIR
#
#  Saca solo las tablas del negocio: productos, pedidos, tickets, conversaciones,
#  alertas de stock, preguntas frecuentes y las cuentas del portal.
#
#  NO incluye las tablas internas del motor de automatización. Eso es a propósito:
#  `credentials_entity` guarda la clave del servicio de IA y el token del bot de
#  Telegram (cifrados, pero ahí), y `execution_data` guarda el contenido de cada
#  ejecución. Un pg_dump completo —como el que hace backup.ps1— se los lleva puestos.
#  Este archivo se puede mandar por chat sin pensarlo dos veces.
#
#  Uso:   .\video\exportar_datos_demo.ps1
#         .\video\exportar_datos_demo.ps1 -Salida C:\ruta\mi_backup.sql
# ============================================================

[CmdletBinding()]
param(
    [string]$Salida = ''
)

$ErrorActionPreference = 'Stop'
$contenedor = 'tesis_postgres'
$usuario    = 'n8n_user'
$baseDatos  = 'ecommerce_tesis'

# Las tablas del negocio, en orden de dependencia (products antes que orders, etc.).
$tablas = @(
    'products', 'faq_responses',
    'orders', 'order_items',
    'interactions', 'tickets', 'stock_alerts'
)

# Las cuentas del portal NO salen por pg_dump: esa tabla puede tener cuentas
# personales de quien instalo (con su hash de contrasena) ademas de la demo.
# Se exporta solo la cuenta demo y sus conexiones, mas abajo.
$emailDemo = 'ventas@techstore.com.ar'

if (-not $Salida) {
    $Salida = Join-Path (Get-Location) ("datos_demo_" + (Get-Date -Format 'yyyy-MM-dd') + ".sql")
}

Write-Host ''
Write-Host '  Exportando los datos de la demostracion' -ForegroundColor Cyan
Write-Host '  ---------------------------------------' -ForegroundColor Cyan

# --- qué se lleva
Write-Host '  Tablas incluidas:' -ForegroundColor White
$consulta = ($tablas | ForEach-Object { "SELECT '$_' AS t, count(*)::text AS n FROM $_" }) -join ' UNION ALL '
$conteos = "$consulta ORDER BY 1;" | docker exec -i $contenedor psql -U $usuario -d $baseDatos -At -F' ' 2>&1
if ($LASTEXITCODE -ne 0) { throw "No pude leer la base: $conteos" }
$conteos | ForEach-Object {
    $p = $_ -split ' '
    Write-Host ('    {0,-22} {1,7} filas' -f $p[0], $p[1]) -ForegroundColor DarkGray
}

# --- el volcado
$parametros = @('exec', $contenedor, 'pg_dump', '-U', $usuario, '-d', $baseDatos,
          '--data-only', '--column-inserts', '--no-owner', '--no-privileges')
foreach ($t in $tablas) { $parametros += @('-t', "public.$t") }

Write-Host ''
Write-Host '  Generando...' -ForegroundColor White
$sql = & docker @parametros 2>&1
if ($LASTEXITCODE -ne 0) { throw "pg_dump fallo: $sql" }

# --- guarda de seguridad: que no se haya colado nada del motor
$texto = $sql -join "`n"
foreach ($prohibida in @('credentials_entity', 'workflow_entity', 'execution_data', 'execution_entity')) {
    if ($texto -match $prohibida) {
        throw "ABORTADO: el volcado contiene '$prohibida'. No se comparte."
    }
}

# --- la cuenta demo y sus conexiones, aparte y acotadas
Write-Host ("  Agregando solo la cuenta demo ($emailDemo)...") -ForegroundColor White
$sqlCuenta = @"
COPY (
  SELECT 'INSERT INTO public.client_accounts (id, business_name, email, password_hash, created_at) VALUES ('
         || id || ', ' || quote_literal(business_name) || ', ' || quote_literal(email) || ', '
         || quote_literal(password_hash) || ', ' || quote_literal(created_at::text) || ');'
    FROM client_accounts WHERE email = '$emailDemo'
  UNION ALL
  SELECT 'INSERT INTO public.channel_connections (id, client_account_id, channel, status, external_reference, connected_at, encrypted_credentials) VALUES ('
         || cc.id || ', ' || cc.client_account_id || ', ' || quote_literal(cc.channel) || ', '
         || quote_literal(cc.status) || ', ' || coalesce(quote_literal(cc.external_reference), 'NULL') || ', '
         || coalesce(quote_literal(cc.connected_at::text), 'NULL') || ', NULL);'
    FROM channel_connections cc JOIN client_accounts c ON c.id = cc.client_account_id
   WHERE c.email = '$emailDemo'
) TO STDOUT;
"@
$cuenta = $sqlCuenta | docker exec -i $contenedor psql -U $usuario -d $baseDatos -At 2>&1
if ($LASTEXITCODE -ne 0) { throw "No pude exportar la cuenta demo: $cuenta" }
$texto = $texto + "`n`n-- Cuenta demo del portal y sus conexiones de canal." +
         "`n-- Las credenciales de canal van en NULL a proposito: son secretos de esa instalacion.`n" +
         (($cuenta) -join "`n") + "`n"
Write-Host ("    " + ($cuenta | Measure-Object).Count + " filas") -ForegroundColor DarkGray

$cabecera = @"
-- ============================================================
--  Datos de la tienda de demostracion
--  Generado el $(Get-Date -Format 'dd/MM/yyyy HH:mm')
--
--  Solo datos del negocio. NO contiene credenciales ni nada del motor
--  de automatizacion: se puede compartir.
--
--  Para cargarlo, con el stack levantado y el schema ya creado:
--    Get-Content datos_demo_*.sql | docker exec -i tesis_postgres psql -U n8n_user -d ecommerce_tesis
--
--  Si la base ya tiene datos, vaciala primero:
--    docker exec tesis_postgres psql -U n8n_user -d ecommerce_tesis -c "TRUNCATE order_items, orders, interactions, tickets, stock_alerts, channel_connections, client_accounts, faq_responses, products RESTART IDENTITY CASCADE"
-- ============================================================

"@

[System.IO.File]::WriteAllText($Salida, $cabecera + $texto, (New-Object System.Text.UTF8Encoding $false))

$tam = [math]::Round((Get-Item $Salida).Length / 1KB)
Write-Host ''
Write-Host "  Listo: $Salida" -ForegroundColor Green
Write-Host "  Tamano: $tam KB" -ForegroundColor DarkGray
Write-Host ''
Write-Host '  Se puede mandar por chat: no lleva credenciales.' -ForegroundColor DarkGray
Write-Host ''
