-- ============================================================
--  TESIS UTN FRM — Schema PostgreSQL Unificado
--  "Automatización del ciclo post-venta en e-commerce:
--   pipeline de procesamiento de órdenes y atención al cliente
--   omnicanal con IA, implementado con n8n"
--
--  Autores: Santiago Sordi, Ignacio Odorico, Juan Cruz Ana
--  Tutor:   Prof. Alberto Cortez
--
--  Este archivo se ejecuta automáticamente al crear el
--  contenedor de PostgreSQL (docker-entrypoint-initdb.d).
--
--  ESTRUCTURA:
--    Flujo 1 — Pipeline de órdenes: products, orders, pipeline_events
--    Flujo 2 — Chatbot omnicanal:   interactions, tickets, faq_responses
--    Conexión: El chatbot consulta `orders` cuando intent = ESTADO_PEDIDO
--    Vistas:   Métricas MTTD, MTTR (Flujo 1) y TMR (Flujo 2)
-- ============================================================

-- ============================================================
-- EXTENSIONES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ############################################################
--  FLUJO 1 — PIPELINE DE PROCESAMIENTO DE ÓRDENES
-- ############################################################

-- ============================================================
-- TABLA: products — Catálogo de productos con control de stock
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(50)    UNIQUE NOT NULL,
    name            VARCHAR(200)   NOT NULL,
    price           DECIMAL(10,2)  NOT NULL CHECK (price >= 0),
    stock           INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0),
    stock_min       INTEGER        NOT NULL DEFAULT 5,
    category        VARCHAR(100),
    created_at      TIMESTAMPTZ    DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Catálogo de productos del e-commerce con control de stock';
COMMENT ON COLUMN products.stock_min IS 'Umbral mínimo de stock — genera alerta cuando stock < stock_min';

-- ============================================================
-- TABLA: orders — Órdenes de compra recibidas por webhook
-- Flujo 1 las crea; Flujo 2 las consulta (intent ESTADO_PEDIDO)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    order_number    VARCHAR(50)    UNIQUE NOT NULL,
    customer_name   VARCHAR(200)   NOT NULL,
    customer_email  VARCHAR(200)   NOT NULL,
    customer_phone  VARCHAR(50),                       -- para vincular con chatbot
    product_id      INTEGER        REFERENCES products(id),
    quantity        INTEGER        NOT NULL CHECK (quantity > 0),
    total_amount    DECIMAL(10,2)  NOT NULL CHECK (total_amount >= 0),
    status          VARCHAR(50)    DEFAULT 'pending'
                    CHECK (status IN (
                        'pending',      -- recibida, esperando procesamiento
                        'processing',   -- n8n verificando stock
                        'confirmed',    -- stock OK, factura generada
                        'shipped',      -- enviada al cliente
                        'delivered',    -- entregada
                        'no_stock',     -- sin stock disponible
                        'cancelled',    -- cancelada
                        'error'         -- error en el pipeline
                    )),
    received_at     TIMESTAMPTZ    DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,                       -- cuando n8n terminó de procesar
    notified_at     TIMESTAMPTZ,                       -- cuando se envió email de confirmación
    raw_payload     JSONB                              -- payload original del webhook
);

COMMENT ON TABLE orders IS 'Órdenes de compra — creadas por Flujo 1 (pipeline), consultadas por Flujo 2 (chatbot)';
COMMENT ON COLUMN orders.customer_phone IS 'Teléfono del cliente — permite vincular consultas del chatbot con órdenes';

-- ============================================================
-- TABLA: pipeline_events — Bitácora de auditoría del pipeline
-- Registra cada paso del procesamiento de una orden
-- ============================================================
CREATE TABLE IF NOT EXISTS pipeline_events (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER        REFERENCES orders(id) ON DELETE CASCADE,
    event_type      VARCHAR(100)   NOT NULL
                    CHECK (event_type IN (
                        'order_received',       -- webhook recibió la orden
                        'stock_checked',        -- verificación de stock completada
                        'stock_updated',        -- stock descontado
                        'invoice_generated',    -- factura/confirmación generada
                        'email_sent',           -- email de confirmación enviado
                        'no_stock_alert',       -- alerta por falta de stock
                        'low_stock_alert',      -- alerta por stock bajo (< stock_min)
                        'error'                 -- error en algún paso
                    )),
    status          VARCHAR(50)    NOT NULL DEFAULT 'success'
                    CHECK (status IN ('success', 'failure', 'warning')),
    duration_ms     INTEGER,                           -- duración del paso en milisegundos
    message         TEXT,
    metadata        JSONB,                             -- datos extra del evento
    created_at      TIMESTAMPTZ    DEFAULT NOW()
);

COMMENT ON TABLE pipeline_events IS 'Bitácora completa del pipeline de órdenes — cada fila es un paso del procesamiento';

-- ############################################################
--  FLUJO 2 — CHATBOT OMNICANAL CON IA
-- ############################################################

-- ============================================================
-- TABLA: interactions — Registro de cada conversación del chatbot
-- Cada mensaje del cliente + respuesta de la IA = 1 fila
-- ============================================================
CREATE TABLE IF NOT EXISTS interactions (
    id              SERIAL PRIMARY KEY,
    channel         VARCHAR(20)    NOT NULL
                    CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    user_id         VARCHAR(200)   NOT NULL,           -- teléfono, chat_id, o email
    message         TEXT           NOT NULL,            -- mensaje original del cliente
    intent          VARCHAR(50)    NOT NULL
                    CHECK (intent IN ('FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL')),
    ai_response     TEXT           NOT NULL,            -- respuesta generada por la IA
    order_id        INTEGER        REFERENCES orders(id),  -- si intent = ESTADO_PEDIDO
    is_urgent       BOOLEAN        DEFAULT FALSE,
    received_at     TIMESTAMPTZ    DEFAULT NOW(),       -- cuando llegó el mensaje
    responded_at    TIMESTAMPTZ,                        -- cuando se envió la respuesta
    metadata        JSONB                               -- datos extra (modelo IA, tokens, etc.)
);

COMMENT ON TABLE interactions IS 'Log de conversaciones del chatbot — cada fila = 1 mensaje + respuesta';
COMMENT ON COLUMN interactions.received_at IS 'Timestamp de recepción — se usa para calcular TMR';
COMMENT ON COLUMN interactions.responded_at IS 'Timestamp de respuesta enviada — se usa para calcular TMR';

-- ============================================================
-- TABLA: tickets — Tickets de soporte para reclamos
-- Se crean cuando intent = RECLAMO
-- ============================================================
CREATE TABLE IF NOT EXISTS tickets (
    id              SERIAL PRIMARY KEY,
    interaction_id  INTEGER        REFERENCES interactions(id) ON DELETE SET NULL,
    order_id        INTEGER        REFERENCES orders(id) ON DELETE SET NULL,
    channel         VARCHAR(20)    NOT NULL
                    CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    user_id         VARCHAR(200)   NOT NULL,
    subject         TEXT           NOT NULL,            -- resumen del reclamo
    status          VARCHAR(50)    DEFAULT 'open'
                    CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority        VARCHAR(20)    DEFAULT 'normal'
                    CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at      TIMESTAMPTZ    DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

COMMENT ON TABLE tickets IS 'Tickets de soporte — se crean automáticamente para intent RECLAMO';

-- ============================================================
-- TABLA: faq_responses — Respuestas predefinidas para preguntas frecuentes
-- El chatbot puede consultar esta tabla para enriquecer respuestas FAQ
-- ============================================================
CREATE TABLE IF NOT EXISTS faq_responses (
    id              SERIAL PRIMARY KEY,
    question        TEXT           NOT NULL,            -- pregunta patrón
    answer          TEXT           NOT NULL,            -- respuesta predefinida
    category        VARCHAR(100),
    enabled         BOOLEAN        DEFAULT TRUE,
    created_at      TIMESTAMPTZ    DEFAULT NOW()
);

COMMENT ON TABLE faq_responses IS 'Base de conocimiento para respuestas FAQ del chatbot';

-- ############################################################
--  VISTAS — MÉTRICAS PARA LA TESIS
-- ############################################################

-- ============================================================
-- VISTA: v_order_processing_time — MTTD y MTTR por orden
-- MTTD = Mean Time To Detect (recepción → inicio procesamiento)
-- MTTR = Mean Time To Resolve (inicio procesamiento → notificación)
-- ============================================================
CREATE OR REPLACE VIEW v_order_processing_time AS
SELECT
    o.id,
    o.order_number,
    o.customer_email,
    o.status,
    o.received_at,
    o.processed_at,
    o.notified_at,
    -- MTTD: tiempo desde recepción hasta procesamiento (segundos)
    EXTRACT(EPOCH FROM (o.processed_at - o.received_at))   AS mttd_seconds,
    -- MTTR: tiempo desde procesamiento hasta notificación (segundos)
    EXTRACT(EPOCH FROM (o.notified_at - o.processed_at))   AS mttr_seconds,
    -- Tiempo total end-to-end
    EXTRACT(EPOCH FROM (o.notified_at - o.received_at))    AS total_seconds
FROM orders o
WHERE o.processed_at IS NOT NULL;

COMMENT ON VIEW v_order_processing_time IS 'Métricas MTTD/MTTR por orden — Flujo 1';

-- ============================================================
-- VISTA: v_daily_order_summary — Resumen diario del pipeline
-- ============================================================
CREATE OR REPLACE VIEW v_daily_order_summary AS
SELECT
    DATE(received_at)           AS fecha,
    COUNT(*)                    AS total_ordenes,
    COUNT(*) FILTER (WHERE status = 'confirmed')  AS confirmadas,
    COUNT(*) FILTER (WHERE status = 'shipped')    AS enviadas,
    COUNT(*) FILTER (WHERE status = 'delivered')  AS entregadas,
    COUNT(*) FILTER (WHERE status = 'no_stock')   AS sin_stock,
    COUNT(*) FILTER (WHERE status = 'error')      AS errores,
    SUM(total_amount) FILTER (WHERE status IN ('confirmed','shipped','delivered'))
                                AS ingresos_del_dia,
    ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
                                AS avg_mttd_seg,
    ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
                                AS avg_mttr_seg
FROM orders
GROUP BY DATE(received_at)
ORDER BY fecha DESC;

COMMENT ON VIEW v_daily_order_summary IS 'Resumen diario de órdenes procesadas — Flujo 1';

-- ============================================================
-- VISTA: v_chatbot_response_time — TMR por interacción
-- TMR = Tiempo Medio de Respuesta (recepción mensaje → envío respuesta)
-- ============================================================
CREATE OR REPLACE VIEW v_chatbot_response_time AS
SELECT
    i.id,
    i.channel,
    i.user_id,
    i.intent,
    i.received_at,
    i.responded_at,
    -- TMR: tiempo de respuesta en segundos
    EXTRACT(EPOCH FROM (i.responded_at - i.received_at))   AS tmr_seconds,
    i.is_urgent
FROM interactions i
WHERE i.responded_at IS NOT NULL;

COMMENT ON VIEW v_chatbot_response_time IS 'Métricas TMR por interacción — Flujo 2';

-- ============================================================
-- VISTA: v_daily_chatbot_summary — Resumen diario del chatbot
-- ============================================================
CREATE OR REPLACE VIEW v_daily_chatbot_summary AS
SELECT
    DATE(received_at)           AS fecha,
    COUNT(*)                    AS total_interacciones,
    COUNT(*) FILTER (WHERE intent = 'FAQ')              AS faq,
    COUNT(*) FILTER (WHERE intent = 'ESTADO_PEDIDO')    AS estado_pedido,
    COUNT(*) FILTER (WHERE intent = 'RECLAMO')          AS reclamos,
    COUNT(*) FILTER (WHERE intent = 'GENERAL')          AS general,
    COUNT(*) FILTER (WHERE channel = 'whatsapp')        AS via_whatsapp,
    COUNT(*) FILTER (WHERE channel = 'telegram')        AS via_telegram,
    COUNT(*) FILTER (WHERE channel = 'email')           AS via_email,
    ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
                                AS avg_tmr_seg,
    COUNT(*) FILTER (WHERE is_urgent)                   AS urgentes
FROM interactions
GROUP BY DATE(received_at)
ORDER BY fecha DESC;

COMMENT ON VIEW v_daily_chatbot_summary IS 'Resumen diario del chatbot omnicanal — Flujo 2';

-- ============================================================
-- VISTA: v_metrics_summary — Resumen ejecutivo de todas las métricas
-- Para el dashboard de Grafana y los resultados de la tesis
-- ============================================================
CREATE OR REPLACE VIEW v_metrics_summary AS
SELECT
    -- Métricas Flujo 1
    (SELECT COUNT(*) FROM orders)                       AS total_orders,
    (SELECT COUNT(*) FROM orders WHERE status = 'confirmed')
                                                        AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders WHERE processed_at IS NOT NULL)        AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders WHERE notified_at IS NOT NULL)         AS avg_mttr_seg,
    -- Métricas Flujo 2
    (SELECT COUNT(*) FROM interactions)                 AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions WHERE responded_at IS NOT NULL)  AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets)                      AS total_tickets,
    (SELECT COUNT(*) FROM tickets WHERE status = 'resolved')
                                                        AS tickets_resolved;

COMMENT ON VIEW v_metrics_summary IS 'Resumen ejecutivo de métricas — ambos flujos — para Grafana y tesis';

-- ############################################################
--  ÍNDICES — Para rendimiento de consultas desde n8n
-- ############################################################

-- Flujo 1
CREATE INDEX IF NOT EXISTS idx_orders_status        ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_received_at   ON orders(received_at);
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_orders_order_number  ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_order ON pipeline_events(order_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_type ON pipeline_events(event_type);

-- Flujo 2
CREATE INDEX IF NOT EXISTS idx_interactions_channel ON interactions(channel);
CREATE INDEX IF NOT EXISTS idx_interactions_intent  ON interactions(intent);
CREATE INDEX IF NOT EXISTS idx_interactions_user    ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_received ON interactions(received_at);
CREATE INDEX IF NOT EXISTS idx_tickets_status       ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_user         ON tickets(user_id);

-- ############################################################
--  DATOS INICIALES — Productos de ejemplo para demo/testing
-- ############################################################

INSERT INTO products (sku, name, price, stock, stock_min, category) VALUES
    ('PROD-001', 'Notebook Lenovo IdeaPad 15',    599.99, 20, 3, 'Notebooks'),
    ('PROD-002', 'Mouse Inalámbrico Logitech',     29.99, 50, 5, 'Periféricos'),
    ('PROD-003', 'Teclado Mecánico Redragon',      79.99, 15, 3, 'Periféricos'),
    ('PROD-004', 'Monitor Samsung 24\" FHD',       249.99,  8, 2, 'Monitores'),
    ('PROD-005', 'Auriculares Sony WH-1000XM5',   349.99,  4, 2, 'Audio'),
    ('PROD-006', 'Webcam Logitech C920',            69.99, 25, 5, 'Periféricos'),
    ('PROD-007', 'SSD Kingston 480GB',              44.99, 30, 5, 'Almacenamiento'),
    ('PROD-008', 'Cargador USB-C 65W',              24.99, 40, 8, 'Accesorios')
ON CONFLICT (sku) DO NOTHING;

-- ############################################################
--  DATOS INICIALES — FAQ predefinidas para el chatbot
-- ############################################################

INSERT INTO faq_responses (question, answer, category) VALUES
    (
        '¿Cuáles son los métodos de pago?',
        'Aceptamos tarjeta de crédito, débito, transferencia bancaria y MercadoPago. Todos los pagos son procesados de forma segura.',
        'Pagos'
    ),
    (
        '¿Cuánto tarda el envío?',
        'Los envíos dentro de Mendoza tardan 1-3 días hábiles. Para el resto del país, entre 3-7 días hábiles. Te notificamos por email cuando tu pedido sea despachado.',
        'Envíos'
    ),
    (
        '¿Cómo puedo devolver un producto?',
        'Tenés 30 días desde la recepción para iniciar una devolución. Escribinos indicando tu número de pedido y el motivo, y te guiamos en el proceso.',
        'Devoluciones'
    ),
    (
        '¿Tienen garantía los productos?',
        'Todos nuestros productos tienen garantía oficial del fabricante. La duración varía según el producto (generalmente 12 meses). Guardá tu comprobante de compra.',
        'Garantía'
    ),
    (
        '¿Cómo contacto a soporte?',
        'Podés escribirnos por WhatsApp, Telegram o email. Nuestro sistema de IA te asiste 24/7 y, si es necesario, escala tu caso a un agente humano.',
        'Soporte'
    ),
    (
        '¿Hacen factura?',
        'Sí, emitimos factura electrónica (AFIP) para todas las compras. La factura se envía automáticamente al email registrado en tu pedido.',
        'Facturación'
    )
ON CONFLICT DO NOTHING;

-- ============================================================
-- CONFIRMACIÓN
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '✓ Schema unificado cargado correctamente en ecommerce_tesis';
    RAISE NOTICE '  • Flujo 1: products, orders, pipeline_events';
    RAISE NOTICE '  • Flujo 2: interactions, tickets, faq_responses';
    RAISE NOTICE '  • Vistas:  v_order_processing_time, v_daily_order_summary,';
    RAISE NOTICE '             v_chatbot_response_time, v_daily_chatbot_summary,';
    RAISE NOTICE '             v_metrics_summary';
    RAISE NOTICE '  • Productos de ejemplo: 8';
    RAISE NOTICE '  • FAQ predefinidas: 6';
    RAISE NOTICE '============================================================';
END $$;
