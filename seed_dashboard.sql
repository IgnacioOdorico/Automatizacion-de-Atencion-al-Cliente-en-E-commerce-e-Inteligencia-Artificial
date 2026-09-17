-- ============================================================
--  TESIS UTN FRM — Seed: capa de Dashboard Cliente (Fase 1)
--  Change OpenSpec: dashboard-cliente
--
--  Cuenta demo realista (PyME) + conexiones de canal en
--  estados variados para la demo en video:
--    whatsapp  → connected    (seed para el video, decisión 10)
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
    'TecnoShop Mendoza SRL',
    'ventas@tecnoshopmza.com.ar',
    '$2b$12$gFkzp0IobEcDZSP0zYjW/OfQtaF2tqxGTA6JgSXT3Ak476cnPt/M.'
)
ON CONFLICT (email) DO NOTHING;

-- ############################################################
--  CONEXIONES DE LA CUENTA DEMO
--  (INSERT ... SELECT: toma el id de la cuenta por su email,
--   nunca TRUNCATE ni DELETE)
-- ############################################################

-- WhatsApp conectado (aprobación de Meta ya dada, semilla para el video)
INSERT INTO channel_connections
    (client_account_id, channel, status, external_reference, connected_at)
SELECT
    c.id, 'whatsapp', 'connected',
    '5492615550102',
    NOW() - INTERVAL '3 days'
FROM client_accounts c
WHERE c.email = 'ventas@tecnoshopmza.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;

-- Telegram conectado con chat_id numérico como external_reference
INSERT INTO channel_connections
    (client_account_id, channel, status, external_reference, connected_at)
SELECT
    c.id, 'telegram', 'connected',
    '458721336',
    NOW() - INTERVAL '2 days'
FROM client_accounts c
WHERE c.email = 'ventas@tecnoshopmza.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;

-- Email sin vincular (Gmail OAuth2 pendiente, se conecta en la demo)
INSERT INTO channel_connections
    (client_account_id, channel, status)
SELECT
    c.id, 'email', 'disconnected'
FROM client_accounts c
WHERE c.email = 'ventas@tecnoshopmza.com.ar'
ON CONFLICT (client_account_id, channel) DO NOTHING;