-- ============================================================
--  TESIS UTN FRM — Seed: capa de Dashboard Cliente (Fase 1)
--  Change OpenSpec: dashboard-cliente
--
--  Cuenta demo realista (PyME) + conexiones de canal en
--  estados variados para la demo en video:
--    whatsapp  → pending      (solicitud enviada, esperando a Meta)
--    telegram  → connected    (external_reference = chat_id numérico)
--    email     → disconnected (canal sin vincular aún)
--
--  Idempotente: ON CONFLICT DO NOTHING, SIN TRUNCATE.
--  (seed_expand.sql está congelado; este seed solo agrega.)
--
--  El password de la cuenta demo se guarda SOLO como hash
--  bcrypt (nunca en claro) — QA §9.1.
-- ============================================================

-- ############################################################
--  CUENTA DEMO MYME
-- ############################################################

INSERT INTO client_accounts (business_name, email, password_hash)
VALUES (
    'TechStore',
    'ventas@techstore.com.ar',
    '$2b$12$gFkzp0IobEcDZSP0zYjW/OfQtaF2tqxGTA6JgSXT3Ak476cnPt/M.'
)
ON CONFLICT (email) DO NOTHING;

-- ############################################################
--  CONEXIONES DE LA CUENTA DEMO
--  (INSERT ... SELECT: toma el id de la cuenta por su email,
--   nunca TRUNCATE ni DELETE)
-- ############################################################

-- WhatsApp en `pending`: es el estado REAL de un alta de WhatsApp Business.
-- La aprobación de un número de negocio la da Meta y tarda de 1 a 3 días hábiles;
-- no depende de esta instalación. Sembrarlo como `connected` hacía que la pantalla
-- afirmara una conexión que no existe: en una demostración eso no se sostiene si
-- alguien pregunta. `pending` es verdad y además es el comportamiento correcto.
INSERT INTO channel_connections
    (client_account_id, channel, status, external_reference, connected_at)
SELECT
    c.id, 'whatsapp', 'pending',
    '5492615550102',
    NULL
FROM client_accounts c
WHERE c.email = 'ventas@techstore.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;

-- Telegram conectado con chat_id numérico como external_reference
INSERT INTO channel_connections
    (client_account_id, channel, status, external_reference, connected_at)
SELECT
    c.id, 'telegram', 'connected',
    '458721336',
    NOW() - INTERVAL '2 days'
FROM client_accounts c
WHERE c.email = 'ventas@techstore.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;

-- Email sin vincular (Gmail OAuth2 pendiente, se conecta en la demo)
INSERT INTO channel_connections
    (client_account_id, channel, status)
SELECT
    c.id, 'email', 'disconnected'
FROM client_accounts c
WHERE c.email = 'ventas@techstore.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;