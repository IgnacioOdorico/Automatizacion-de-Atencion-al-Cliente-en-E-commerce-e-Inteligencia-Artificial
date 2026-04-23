-- ============================================================
-- LIMPIAR FAQs DUPLICADAS (mantener solo ids 1-6)
-- ============================================================
DELETE FROM faq_responses WHERE id > 6;

-- ============================================================
-- EXPANDIR FAQs — de 6 a 22 entradas reales y útiles
-- ============================================================
INSERT INTO faq_responses (question, answer, category) VALUES

-- PAGOS
('¿Puedo pagar en cuotas?',
 'Sí, con tarjetas de crédito Visa, Mastercard y American Express podés pagar en hasta 12 cuotas sin interés en productos seleccionados. Las cuotas disponibles se muestran en el checkout.',
 'Pagos'),

('¿Es seguro pagar con tarjeta en la web?',
 'Totalmente. Usamos encriptación SSL y procesamos los pagos a través de MercadoPago, que cumple con los estándares PCI-DSS. Nunca almacenamos los datos de tu tarjeta.',
 'Pagos'),

-- ENVÍOS
('¿Hacen envíos a todo el país?',
 'Sí, enviamos a todo el territorio argentino. Trabajamos con OCA, Andreani y correo argentino. El costo de envío se calcula en el checkout según tu código postal.',
 'Envíos'),

('¿Puedo hacer el seguimiento de mi envío?',
 'Sí. Una vez despachado tu pedido, te enviamos un email con el número de tracking y el enlace directo para seguir el paquete en tiempo real.',
 'Envíos'),

('¿Hacen envíos internacionales?',
 'Por el momento solo enviamos dentro de Argentina. Estamos trabajando para expandir a países limítrofes próximamente.',
 'Envíos'),

('¿Qué pasa si no estoy en casa cuando llega el pedido?',
 'El transportista deja un aviso y hace un segundo intento al día siguiente. Si tampoco podés recibirlo, el paquete queda disponible para retiro en la sucursal más cercana por 5 días hábiles.',
 'Envíos'),

-- DEVOLUCIONES
('¿Cuál es la política de cambios?',
 'Podés cambiar un producto dentro de los 30 días de recibido, siempre que esté en su embalaje original y sin uso. Los gastos de envío del cambio corren por nuestra cuenta si el error fue nuestro.',
 'Devoluciones'),

('¿Cómo inicio una devolución?',
 'Escribinos por este chat o al email devoluciones@techstore.com.ar con tu número de pedido y el motivo. Te enviamos una etiqueta prepaga para el retiro en 24hs hábiles.',
 'Devoluciones'),

-- GARANTÍA
('¿Qué cubre la garantía?',
 'La garantía cubre defectos de fabricación. NO cubre daños por mal uso, caídas, líquidos o modificaciones no autorizadas. Ante cualquier falla, contactanos y gestionamos el service con el fabricante.',
 'Garantía'),

('¿Cómo hago válida la garantía?',
 'Guardá el comprobante de compra (te lo enviamos por email). Si el producto falla, escribinos con foto o video del problema y tu número de pedido. Nos encargamos de todo el proceso de garantía.',
 'Garantía'),

-- PRODUCTOS
('¿Los productos son originales?',
 'Sí, todos nuestros productos son 100% originales con garantía oficial del fabricante. Somos distribuidores autorizados de todas las marcas que comercializamos.',
 'Productos'),

('¿Tienen stock en físico para retirar?',
 'Por el momento somos una tienda 100% online y no contamos con local a la calle. Todos los pedidos se despachan desde nuestro depósito en Mendoza.',
 'Productos'),

('¿Cómo sé si un producto tiene stock?',
 'Si podés agregarlo al carrito, hay stock disponible. Si aparece como "Sin stock", podés anotarte en la lista de espera y te avisamos cuando vuelva a estar disponible.',
 'Productos'),

-- FACTURACIÓN
('¿Hacen factura A para empresas?',
 'Sí, emitimos factura A para responsables inscriptos. Durante el checkout elegís el tipo de comprobante e ingresás el CUIT y razón social de tu empresa.',
 'Facturación'),

('¿Cuándo recibo la factura?',
 'La factura electrónica se genera automáticamente al confirmar el pago y te llega por email en minutos. Si no la recibís, revisá la carpeta de spam o escribinos.',
 'Facturación'),

-- PEDIDOS
('¿Puedo cancelar un pedido?',
 'Podés cancelar sin costo dentro de las 2 horas de realizado, siempre que no haya sido despachado. Después del despacho, el proceso es una devolución normal.',
 'Pedidos'),

('¿Cómo recibo el comprobante de compra?',
 'Te enviamos un email de confirmación inmediatamente después del pago con todos los detalles del pedido y la factura adjunta.',
 'Pedidos')

ON CONFLICT DO NOTHING;

-- ============================================================
-- AGREGAR 12 PRODUCTOS NUEVOS con más variedad
-- ============================================================
INSERT INTO products (sku, name, price, stock, stock_min, category) VALUES
    ('PROD-009', 'Tablet Samsung Galaxy Tab A9',         229.99, 12, 2, 'Tablets'),
    ('PROD-010', 'Impresora HP LaserJet Pro M15w',       189.99,  6, 2, 'Impresoras'),
    ('PROD-011', 'Router TP-Link AX3000 WiFi 6',         89.99, 18, 3, 'Redes'),
    ('PROD-012', 'Memoria RAM Kingston 16GB DDR4',        54.99, 22, 4, 'Componentes'),
    ('PROD-013', 'Notebook HP Victus 15 Gaming',         799.99,  5, 2, 'Notebooks'),
    ('PROD-014', 'Monitor LG 27" 4K UltraFine',         449.99,  3, 1, 'Monitores'),
    ('PROD-015', 'Silla Gamer DXRacer Formula',          349.99,  7, 2, 'Mobiliario'),
    ('PROD-016', 'Micrófono Blue Yeti USB',              129.99, 10, 2, 'Audio'),
    ('PROD-017', 'Disco Rígido Seagate 2TB HDD',          64.99, 20, 4, 'Almacenamiento'),
    ('PROD-018', 'Pendrive Kingston 64GB USB 3.2',         9.99, 80, 10, 'Almacenamiento'),
    ('PROD-019', 'Pad Mouse XL Antideslizante',            14.99, 60, 8, 'Accesorios'),
    ('PROD-020', 'Hub USB-C 7 en 1 Anker',                39.99, 25, 5, 'Accesorios')
ON CONFLICT (sku) DO NOTHING;

-- ============================================================
-- AGREGAR ÓRDENES HISTÓRICAS para métricas más ricas
-- ============================================================
INSERT INTO orders (order_number, customer_name, customer_email, customer_phone, product_id, quantity, total_amount, status, received_at, processed_at, notified_at) VALUES
    ('ORD-HIST-001', 'Martina Lopez',    'martina@gmail.com',   '5492614001001', 1, 1,  599.99, 'delivered',  NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days' + INTERVAL '8 seconds',  NOW() - INTERVAL '10 days' + INTERVAL '25 seconds'),
    ('ORD-HIST-002', 'Facundo Rios',     'facundo@hotmail.com', '5492614002002', 3, 2,  159.98, 'delivered',  NOW() - INTERVAL '9 days',  NOW() - INTERVAL '9 days'  + INTERVAL '5 seconds',  NOW() - INTERVAL '9 days'  + INTERVAL '18 seconds'),
    ('ORD-HIST-003', 'Camila Suarez',    'camila@yahoo.com',    '5492614003003', 5, 1,  349.99, 'shipped',    NOW() - INTERVAL '7 days',  NOW() - INTERVAL '7 days'  + INTERVAL '6 seconds',  NOW() - INTERVAL '7 days'  + INTERVAL '20 seconds'),
    ('ORD-HIST-004', 'Ignacio Blanco',   'ignacio@gmail.com',   '5492614004004', 2, 3,   89.97, 'delivered',  NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days'  + INTERVAL '4 seconds',  NOW() - INTERVAL '6 days'  + INTERVAL '15 seconds'),
    ('ORD-HIST-005', 'Valentina Cruz',   'vale@gmail.com',      '5492614005005', 7, 2,   89.98, 'confirmed',  NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days'  + INTERVAL '7 seconds',  NOW() - INTERVAL '5 days'  + INTERVAL '22 seconds'),
    ('ORD-HIST-006', 'Lucas Fernandez',  'lucas@outlook.com',   '5492614006006', 4, 1,  249.99, 'no_stock',   NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days'  + INTERVAL '3 seconds',  NULL),
    ('ORD-HIST-007', 'Agustina Moreno',  'agus@gmail.com',      '5492614007007', 6, 1,   69.99, 'delivered',  NOW() - INTERVAL '3 days',  NOW() - INTERVAL '3 days'  + INTERVAL '5 seconds',  NOW() - INTERVAL '3 days'  + INTERVAL '17 seconds'),
    ('ORD-HIST-008', 'Tomás Gutierrez',  'tomas@gmail.com',     '5492614008008', 8, 4,   99.96, 'shipped',    NOW() - INTERVAL '2 days',  NOW() - INTERVAL '2 days'  + INTERVAL '6 seconds',  NOW() - INTERVAL '2 days'  + INTERVAL '19 seconds'),
    ('ORD-HIST-009', 'Micaela Vargas',   'mica@hotmail.com',    '5492614009009', 1, 1,  599.99, 'confirmed',  NOW() - INTERVAL '1 day',   NOW() - INTERVAL '1 day'   + INTERVAL '9 seconds',  NOW() - INTERVAL '1 day'   + INTERVAL '28 seconds'),
    ('ORD-HIST-010', 'Bruno Herrera',    'bruno@gmail.com',     '5492614010010', 3, 1,   79.99, 'confirmed',  NOW() - INTERVAL '12 hours',NOW() - INTERVAL '12 hours'+ INTERVAL '4 seconds',  NOW() - INTERVAL '12 hours'+ INTERVAL '14 seconds')
ON CONFLICT (order_number) DO NOTHING;

-- ============================================================
-- AGREGAR INTERACCIONES HISTÓRICAS para métricas del chatbot
-- ============================================================
INSERT INTO interactions (channel, user_id, message, intent, ai_response, is_urgent, received_at, responded_at) VALUES
    ('whatsapp', '5492614001001', '¿Cuánto tarda el envío a Mendoza?',                          'FAQ',           'Los envíos a Mendoza tardan entre 1 y 3 días hábiles.',                    false, NOW() - INTERVAL '8 days',  NOW() - INTERVAL '8 days'  + INTERVAL '2 seconds'),
    ('whatsapp', '5492614002002', 'Quiero saber el estado de mi pedido ORD-HIST-002',            'ESTADO_PEDIDO', 'Tu pedido ORD-HIST-002 está confirmado y en camino.',                       false, NOW() - INTERVAL '7 days',  NOW() - INTERVAL '7 days'  + INTERVAL '3 seconds'),
    ('whatsapp', '5492614003003', 'Me llegó el producto equivocado, pedí auriculares negros',    'RECLAMO',       'Lamentamos el inconveniente, registramos tu reclamo.',                      false, NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days'  + INTERVAL '4 seconds'),
    ('whatsapp', '5492614004004', '¿Aceptan MercadoPago?',                                      'FAQ',           'Sí, aceptamos MercadoPago, tarjetas y transferencia.',                      false, NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days'  + INTERVAL '2 seconds'),
    ('whatsapp', '5492614005005', 'Mi pedido figura como confirmado pero no recibí el mail',    'ESTADO_PEDIDO', 'Tu pedido está confirmado, revisá spam o escribinos.',                      false, NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days'  + INTERVAL '3 seconds'),
    ('whatsapp', '5492614006006', 'Por qué me dicen sin stock si lo compré?',                   'RECLAMO',       'Lamentamos el problema con el stock, te contactamos a la brevedad.',        true,  NOW() - INTERVAL '3 days',  NOW() - INTERVAL '3 days'  + INTERVAL '2 seconds'),
    ('whatsapp', '5492614007007', '¿Tienen garantía las webcams?',                              'FAQ',           'Sí, todas las webcams tienen 12 meses de garantía oficial.',                false, NOW() - INTERVAL '2 days',  NOW() - INTERVAL '2 days'  + INTERVAL '3 seconds'),
    ('whatsapp', '5492614008008', 'Cuánto tarda en llegar a San Juan?',                         'FAQ',           'Los envíos a San Juan tardan entre 3 y 5 días hábiles.',                   false, NOW() - INTERVAL '1 day',   NOW() - INTERVAL '1 day'   + INTERVAL '2 seconds'),
    ('whatsapp', '5492614009009', 'Quiero cancelar mi pedido ORD-HIST-009',                     'RECLAMO',       'Entendemos, vamos a gestionar la cancelación de inmediato.',                false, NOW() - INTERVAL '20 hours',NOW() - INTERVAL '20 hours'+ INTERVAL '3 seconds'),
    ('whatsapp', '5492614010010', 'Excelente atención, recibí todo perfecto gracias!',          'GENERAL',       'Muchas gracias por tu mensaje, nos alegra que hayas tenido buena experiencia.', false, NOW() - INTERVAL '10 hours',NOW() - INTERVAL '10 hours'+ INTERVAL '2 seconds')
ON CONFLICT DO NOTHING;
