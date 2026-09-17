-- ============================================================
--  TESIS UTN FRM — Schema PostgreSQL SIMPLIFICADO
--  "Automatización del ciclo post-venta en e-commerce:
--   pipeline de procesamiento de órdenes y atención al cliente
--   omnicanal con IA, implementado con n8n"
--
--  Autores: Santiago Sordi, Ignacio Odorico, Juan Cruz Ana
--  Tutor:   Prof. Alberto Cortez
--
--  VERSIÓN PARA DEMO (endurecida tras la auditoría, A-12):
--    - TIMESTAMPTZ en todas las marcas temporales
--    - Índices de rendimiento (los que OE3 promete)
--    - Tabla order_items (N productos por orden; orders.product_id
--      se conserva por compatibilidad con los workflows actuales)
--    - Columna data_source (measured/synthetic) para separar datos
--      medidos del seed en las métricas (B-5)
--    - Tabla stock_alerts (alerta de reposición, A-07)
--    - Sin tabla pipeline_events ni COMMENT ON (no necesarios en demo)
--
--  ESTRUCTURA:
--    Flujo 1 — Pipeline de órdenes: products, orders, order_items, stock_alerts
--    Flujo 2 — Chatbot:             interactions, tickets, faq_responses
--    Vistas:   5 vistas de métricas (MTTD, MTTR, TMR)
-- ============================================================

-- ############################################################
--  FLUJO 1 — PIPELINE DE PROCESAMIENTO DE ÓRDENES
-- ############################################################

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

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    order_number    VARCHAR(50)    UNIQUE NOT NULL,
    customer_name   VARCHAR(200)   NOT NULL,
    customer_email  VARCHAR(200)   NOT NULL,
    customer_phone  VARCHAR(50),
    product_id      INTEGER        REFERENCES products(id),
    quantity        INTEGER        NOT NULL CHECK (quantity > 0),
    total_amount    DECIMAL(10,2)  NOT NULL CHECK (total_amount >= 0),
    status          VARCHAR(50)    DEFAULT 'pending'
                    CHECK (status IN (
                        'pending',
                        'processing',
                        'confirmed',
                        'shipped',
                        'delivered',
                        'no_stock',
                        'cancelled',
                        'error'
                    )),
    received_at     TIMESTAMPTZ    DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    notified_at     TIMESTAMPTZ,
    raw_payload     JSONB,
    data_source     VARCHAR(20)    NOT NULL DEFAULT 'measured'
                    CHECK (data_source IN ('measured', 'synthetic', 'e4_manual'))
);

-- Ítems de una orden: N productos por orden (A-12). orders.product_id y
-- orders.quantity se conservan por compatibilidad con los workflows
-- actuales (que cargan una orden mono-producto); el diseño objetivo es
-- que cada línea de la orden viva acá.
CREATE TABLE IF NOT EXISTS order_items (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER        NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      INTEGER        NOT NULL REFERENCES products(id),
    quantity        INTEGER        NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10,2)  NOT NULL CHECK (unit_price >= 0),
    subtotal        DECIMAL(10,2)  GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- Alertas de stock bajo (A-07): se registra cada vez que un producto
-- cruza su umbral de reposicion tras descontarse el stock de una orden.
CREATE TABLE IF NOT EXISTS stock_alerts (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER        NOT NULL REFERENCES products(id),
    order_id        INTEGER        REFERENCES orders(id) ON DELETE SET NULL,
    sku             VARCHAR(50)    NOT NULL,
    stock_actual    INTEGER        NOT NULL CHECK (stock_actual >= 0),
    stock_min       INTEGER        NOT NULL,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    data_source     VARCHAR(20)    NOT NULL DEFAULT 'measured'
                    CHECK (data_source IN ('measured', 'synthetic'))
);

-- ############################################################
--  FLUJO 2 — CHATBOT MULTICANAL CON IA
-- ############################################################

CREATE TABLE IF NOT EXISTS interactions (
    id              SERIAL PRIMARY KEY,
    channel         VARCHAR(20)    NOT NULL
                    CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    user_id         VARCHAR(200)   NOT NULL,
    message         TEXT           NOT NULL,
    intent          VARCHAR(50)    NOT NULL
                    CHECK (intent IN ('FAQ', 'ESTADO_PEDIDO', 'RECLAMO', 'GENERAL')),
    ai_response     TEXT           NOT NULL,
    order_id        INTEGER        REFERENCES orders(id) ON DELETE SET NULL,
    is_urgent       BOOLEAN        DEFAULT FALSE,
    received_at     TIMESTAMPTZ    DEFAULT NOW(),
    responded_at    TIMESTAMPTZ,
    data_source     VARCHAR(20)    NOT NULL DEFAULT 'measured'
                    CHECK (data_source IN ('measured', 'synthetic'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id              SERIAL PRIMARY KEY,
    interaction_id  INTEGER        REFERENCES interactions(id) ON DELETE SET NULL,
    order_id        INTEGER        REFERENCES orders(id) ON DELETE SET NULL,
    channel         VARCHAR(20)    NOT NULL
                    CHECK (channel IN ('whatsapp', 'telegram', 'email')),
    user_id         VARCHAR(200)   NOT NULL,
    subject         TEXT           NOT NULL,
    status          VARCHAR(50)    DEFAULT 'open'
                    CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority        VARCHAR(20)    DEFAULT 'normal'
                    CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at      TIMESTAMPTZ    DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    data_source     VARCHAR(20)    NOT NULL DEFAULT 'measured'
                    CHECK (data_source IN ('measured', 'synthetic'))
);

CREATE TABLE IF NOT EXISTS faq_responses (
    id              SERIAL PRIMARY KEY,
    question        TEXT           NOT NULL,
    answer          TEXT           NOT NULL,
    category        VARCHAR(100),
    enabled         BOOLEAN        DEFAULT TRUE,
    created_at      TIMESTAMPTZ    DEFAULT NOW()
);

-- ############################################################
--  ÍNDICES DE RENDIMIENTO (OE3 / A-12)
--  Cada índice responde a una query real de los flujos o vistas.
-- ############################################################

CREATE INDEX IF NOT EXISTS idx_orders_status              ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_source_received     ON orders (data_source, received_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id       ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id     ON order_items (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_product     ON stock_alerts (product_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_created     ON stock_alerts (created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_intent        ON interactions (intent);
CREATE INDEX IF NOT EXISTS idx_interactions_channel_received ON interactions (channel, received_at);
CREATE INDEX IF NOT EXISTS idx_interactions_source        ON interactions (data_source);
CREATE INDEX IF NOT EXISTS idx_interactions_order_id      ON interactions (order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_order_id           ON tickets (order_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status             ON tickets (status);

-- ############################################################
--  VISTAS — MÉTRICAS PARA LA TESIS
--  Las cinco restringen por data_source = 'measured': agregan sobre los
--  registros que producen las corridas de medición y dejan fuera el seed
--  ('synthetic') y el baseline manual ('e4_manual'), de modo que la separación
--  entre lo medido y lo precargado es una propiedad del esquema y no una
--  convención de cada panel. Es la definición con la que se capturaron las
--  figuras de resultados (experiments/E5/vistas_measured.sql).
-- ############################################################

CREATE OR REPLACE VIEW v_order_processing_time AS
SELECT
    o.id,
    o.order_number,
    o.customer_email,
    o.status,
    o.received_at,
    o.processed_at,
    o.notified_at,
    EXTRACT(EPOCH FROM (o.processed_at - o.received_at))   AS mttd_seconds,
    EXTRACT(EPOCH FROM (o.notified_at - o.processed_at))   AS mttr_seconds,
    EXTRACT(EPOCH FROM (o.notified_at - o.received_at))    AS total_seconds
FROM orders o
WHERE o.processed_at IS NOT NULL
  AND o.data_source = 'measured';

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
WHERE data_source = 'measured'
GROUP BY DATE(received_at)
ORDER BY fecha DESC;

CREATE OR REPLACE VIEW v_chatbot_response_time AS
SELECT
    i.id,
    i.channel,
    i.user_id,
    i.intent,
    i.received_at,
    i.responded_at,
    EXTRACT(EPOCH FROM (i.responded_at - i.received_at))   AS tmr_seconds,
    i.is_urgent
FROM interactions i
WHERE i.responded_at IS NOT NULL
  AND i.data_source = 'measured';

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
WHERE data_source = 'measured'
GROUP BY DATE(received_at)
ORDER BY fecha DESC;

CREATE OR REPLACE VIEW v_metrics_summary AS
SELECT
    (SELECT COUNT(*) FROM orders
      WHERE data_source = 'measured')                   AS total_orders,
    (SELECT COUNT(*) FROM orders
      WHERE data_source = 'measured' AND status = 'confirmed')
                                                        AS orders_confirmed,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::NUMERIC, 2)
     FROM orders
      WHERE data_source = 'measured' AND processed_at IS NOT NULL)
                                                        AS avg_mttd_seg,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (notified_at - processed_at)))::NUMERIC, 2)
     FROM orders
      WHERE data_source = 'measured' AND notified_at IS NOT NULL)
                                                        AS avg_mttr_seg,
    (SELECT COUNT(*) FROM interactions
      WHERE data_source = 'measured')                   AS total_interactions,
    (SELECT ROUND(AVG(EXTRACT(EPOCH FROM (responded_at - received_at)))::NUMERIC, 2)
     FROM interactions
      WHERE data_source = 'measured' AND responded_at IS NOT NULL)
                                                        AS avg_tmr_seg,
    (SELECT COUNT(*) FROM tickets
      WHERE data_source = 'measured')                   AS total_tickets,
    (SELECT COUNT(*) FROM tickets
      WHERE data_source = 'measured' AND status = 'resolved')
                                                        AS tickets_resolved;

-- ############################################################
--  DATOS INICIALES — Productos
-- ############################################################

INSERT INTO products (sku, name, price, stock, stock_min, category) VALUES
    ('PROD-001', 'Notebook Lenovo IdeaPad 15',    599.99, 20, 3, 'Notebooks'),
    ('PROD-002', 'Mouse Inalámbrico Logitech',     29.99, 50, 5, 'Periféricos'),
    ('PROD-003', 'Teclado Mecánico Redragon',      79.99, 15, 3, 'Periféricos'),
    ('PROD-004', 'Monitor Samsung 24" FHD',       249.99,  8, 2, 'Monitores'),
    ('PROD-005', 'Auriculares Sony WH-1000XM5',   349.99,  4, 2, 'Audio'),
    ('PROD-006', 'Webcam Logitech C920',            69.99, 25, 5, 'Periféricos'),
    ('PROD-007', 'SSD Kingston 480GB',              44.99, 30, 5, 'Almacenamiento'),
    ('PROD-008', 'Cargador USB-C 65W',              24.99, 40, 8, 'Accesorios')
ON CONFLICT (sku) DO NOTHING;

-- ############################################################
--  DATOS INICIALES — FAQ
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
--  Vista del corpus evaluado del Flujo 2 (150 mensajes con ground truth)
--  Alimenta 5 de los 13 paneles de Grafana. Ver docs/ Anexo A.
-- ============================================================
CREATE OR REPLACE VIEW v_chatbot_corpus AS
SELECT
    i.id,
    i.channel,
    i.user_id,
    i.intent,                              -- intent PREDICHO por el modelo
    i.received_at,
    i.responded_at,
    EXTRACT(EPOCH FROM (i.responded_at - i.received_at)) AS tmr_seconds,
    i.is_urgent
FROM interactions i
WHERE i.data_source = 'measured'
  AND i.responded_at IS NOT NULL
  AND i.received_at >= '2026-08-12 23:00:00'
  AND i.received_at <  '2026-08-13 00:00:00';
