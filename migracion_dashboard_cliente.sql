-- ============================================================
--  TESIS UTN FRM — Migración: capa de Dashboard Cliente
--  Change OpenSpec: dashboard-cliente (Fase 1)
--
--  Agrega SOLO las tablas nuevas del dashboard:
--    client_accounts      → cuentas PyME (auth por email + bcrypt)
--    channel_connections  → estado de conexión por canal
--                           (whatsapp / telegram / email)
--
--  NO modifica ninguna tabla existente de los flujos
--  (products, orders, order_items, stock_alerts,
--   interactions, tickets, faq_responses) ni las vistas v_*.
--
--  ROLLBACK (solo afecta las tablas nuevas):
--    DROP TABLE channel_connections, client_accounts;
--    En ESE orden: channel_connections tiene la FK hacia
--    client_accounts con ON DELETE CASCADE.
--
--  HALLAZGO FASE 1 (AC 2.5) — tipo temporal de la instancia:
--    `\d orders` → received_at / processed_at / notified_at son
--    TIMESTAMPTZ (timestamp with time zone) en el volumen
--    desplegado; la instancia coincide con el canónico
--    init_simple.sql. La API debe serializar con AT TIME ZONE
--    'UTC' explícito (decisión 11 de design.md) y el front
--    formatea a hora local.
--
--  Convenciones del repo (init_simple.sql): PK SERIAL INTEGER,
--  TIMESTAMPTZ, CHECK constraints, snake_case, IF NOT EXISTS.
-- ============================================================

-- ############################################################
--  CUENTAS DE CLIENTE Pyme (SaaS del dashboard)
-- ############################################################

CREATE TABLE IF NOT EXISTS client_accounts (
    id              SERIAL PRIMARY KEY,
    business_name   TEXT            NOT NULL,
    email           TEXT            UNIQUE NOT NULL,
    password_hash   TEXT            NOT NULL,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- ############################################################
--  CONEXIONES DE CANAL POR CUENTA
--  (whatsapp / telegram / email) — dominio unificado con el
--  CHECK de interactions.channel y tickets.channel
-- ############################################################

CREATE TABLE IF NOT EXISTS channel_connections (
    id                    SERIAL PRIMARY KEY,
    client_account_id     INTEGER        NOT NULL
                          REFERENCES client_accounts(id) ON DELETE CASCADE,
    channel               VARCHAR(20)    NOT NULL
                          CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    status                VARCHAR(20)    NOT NULL DEFAULT 'disconnected'
                          CHECK (status IN ('disconnected', 'pending', 'connected', 'error')),
    external_reference    TEXT,
    connected_at          TIMESTAMPTZ,
    encrypted_credentials TEXT,
    UNIQUE (client_account_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_channel_connections_account
    ON channel_connections (client_account_id);