# Spec — client-dashboard/auth

## ADDED Requirements

### Requirement: Registro de cliente PyME
El sistema SHALL permitir registrar una cuenta de cliente PyME (`POST /auth/register`) con `business_name`, `email` único y `password`. La contraseña SHALL almacenarse únicamente como hash bcrypt (`password_hash` en `client_accounts`), nunca en texto plano. Si el email ya existe, el registro SHALL fallar con error 409 y mensaje claro.

#### Scenario: Alta de cuenta nueva
- **WHEN** se envía `POST /auth/register` con `business_name`, `email` y `password` válidos
- **THEN** el sistema crea la fila en `client_accounts` con `password_hash` bcrypt y responde 201 con los datos de la cuenta (sin el hash)

#### Scenario: Email duplicado
- **WHEN** se envía `POST /auth/register` con un email ya registrado
- **THEN** el sistema responde 409 y no modifica ningún dato

### Requirement: Login con JWT de expiración corta + refresh token
El sistema SHALL autenticar con `POST /auth/login` (email + contraseña), verificar el hash bcrypt y emitir un access token JWT con expiración corta (2h) y un refresh token de mayor vida (7 días). El refresh token SHALL rotar en `/auth/refresh` y el access token renovado no SHALL exigir re-login. El secreto de firma SHALL provenir de variable de entorno (`DASHBOARD_JWT_SECRET`), nunca hardcodeado.

#### Scenario: Credenciales válidas
- **WHEN** se envía `POST /auth/login` con email y contraseña correctos
- **THEN** el sistema responde 200 con access token (expira en 2h) y refresh token

#### Scenario: Contraseña incorrecta
- **WHEN** se envía `POST /auth/login` con contraseña equivocada
- **THEN** el sistema responde 401 y no emite ningún token

#### Scenario: Renovación con refresh token
- **WHEN** se envía `POST /auth/refresh` con un refresh token válido y no vencido
- **THEN** el sistema responde con un access token nuevo y un refresh token renovado

### Requirement: Rate limiting en /auth/login
El sistema SHALL limitar los intentos de login por IP y email para mitigar fuerza bruta (umbral inicial: 5 intentos fallidos por ventana de 5 minutos). Superado el umbral, el sistema SHALL devolver 429 hasta que expire la ventana.

#### Scenario: Exceso de intentos fallidos
- **WHEN** se superan 5 intentos fallidos de login en 5 minutos desde la misma IP o contra el mismo email
- **THEN** el sistema responde 429 y rechaza nuevos intentos hasta que caduque la ventana

### Requirement: Perfil del usuario logueado
El sistema SHALL exponer `GET /me` que devuelve los datos de la cuenta autenticada (leídos de `client_accounts`) y el estado de sus conexiones de canal. El endpoint SHALL requerir JWT válido y devolver únicamente los datos de la `client_account_id` del token.

#### Scenario: Lectura del propio perfil
- **WHEN** se envía `GET /me` con un JWT válido
- **THEN** el sistema responde 200 con `business_name`, `email`, `created_at` y las conexiones de canal de esa cuenta

#### Scenario: Acceso sin token
- **WHEN** se envía `GET /me` sin header de autorización
- **THEN** el sistema responde 401 y no devuelve ningún dato

### Requirement: Aislamiento de datos entre cuentas
Todo endpoint autenticado SHALL obtener la `client_account_id` del JWT y filtrar las queries por ella; el sistema SHALL prohibir cruzar datos entre cuentas. El front SHALL proteger las rutas internas (dashboard, pedidos, tickets, catálogo, conexiones, perfil) redirigiendo a login cuando no hay sesión válida.

#### Scenario: Cuenta A no ve datos de Cuenta B
- **WHEN** se pide información con un JWT de la cuenta A mientras existen datos de la cuenta B
- **THEN** el sistema responde solo datos pertenecientes a la cuenta A

#### Scenario: Sesión vencida en el front
- **WHEN** el access token expira y hay una ruta protegida cargada
- **THEN** el front intenta renovar el token con el refresh; si falla, redirige al login