# Spec — client-dashboard/orders

## ADDED Requirements

### Requirement: Listado de pedidos con paginado y filtros
El sistema SHALL exponer `GET /orders?status=&page=` (JWT) sobre la tabla real `orders`, con paginado (por defecto tamaño de página 20), filtro opcional por `status` (valores del CHECK real: `pending, processing, confirmed, shipped, delivered, no_stock, cancelled, error`) y el nombre del producto vía `JOIN products` por `orders.product_id` (equivalente hoy a `order_items` por ser mono-producto). Orden por `received_at DESC`.

#### Scenario: Página inicial de pedidos
- **WHEN** se envía `GET /orders` con JWT válido sin filtros
- **THEN** el sistema responde 200 con la primera página de órdenes (20 por página) ordenadas por `received_at` descendente, incluyendo `order_number`, `customer_name`, `status`, `total_amount`, fechas del pipeline y nombre/SKU del producto

#### Scenario: Filtro por estado
- **WHEN** se envía `GET /orders?status=no_stock`
- **THEN** el sistema responde solo órdenes con `status='no_stock'`

#### Scenario: Navegación de páginas
- **WHEN** se envía `GET /orders?page=2`
- **THEN** el sistema responde la página siguiente con el mismo orden y total de páginas disponible para el front

### Requirement: Detalle de una orden
El sistema SHALL exponer `GET /orders/{id}` (JWT) que devuelva la orden completa, sus ítems desde `order_items` (cantidad, precio unitario, subtotal) cuando existan, y el `raw_payload` JSONB original del webhook para trazabilidad. Si el id no existe, responde 404.

#### Scenario: Detalle con payload original
- **WHEN** se envía `GET /orders/{id}` con un id existente
- **THEN** el sistema responde la orden con sus `order_items` y el `raw_payload` sin transformar

#### Scenario: Orden inexistente
- **WHEN** se envía `GET /orders/{id}` con un id que no existe
- **THEN** el sistema responde 404

### Requirement: Listado de tickets con paginado
El sistema SHALL exponer `GET /tickets?status=&page=` (JWT) sobre la tabla real `tickets`, con paginado (20 por página) y filtro por `status` (`open, in_progress, resolved, closed`). El estado "resuelto" SHALL derivarse de `status='resolved'`, nunca de `resolved_at` (el workflow de n8n no lo actualiza y queda NULL).

#### Scenario: Tickets abiertos
- **WHEN** se envía `GET /tickets?status=open`
- **THEN** el sistema responde los tickets con `status='open'` con `channel`, `user_id`, `subject`, `priority` y `created_at`

#### Scenario: Deriva "resuelto" del estado
- **WHEN** un ticket tiene `status='resolved'` y `resolved_at=NULL`
- **THEN** el sistema lo presenta como resuelto y el front no muestra una fecha de resolución vacía como si fuera un error

### Requirement: Detalle de un ticket
El sistema SHALL exponer `GET /tickets/{id}` (JWT) con el ticket y su `interaction_id` de respaldo. Si no existe, 404.

#### Scenario: Detalle de ticket con interacción
- **WHEN** se envía `GET /tickets/{id}` con un id existente
- **THEN** el sistema responde el ticket completo y referencia la interacción que lo originó

### Requirement: Catálogo con búsqueda
El sistema SHALL exponer `GET /products?search=&page=` (JWT) sobre la tabla real `products`, con búsqueda `ILIKE` por `sku`/`name` y paginado (20 por página). El listado SHALL incluir `sku`, `name`, `price`, `stock`, `stock_min`, `category`.

#### Scenario: Búsqueda por nombre
- **WHEN** se envía `GET /products?search=auriculares`
- **THEN** el sistema responde los productos cuyo `name` o `sku` contienen el término

#### Scenario: Listado inicial
- **WHEN** se envía `GET /products` sin búsqueda
- **THEN** el sistema responde la primera página del catálogo completo ordenada por `name`

### Requirement: Páginas de lectura en el front
El front SHALL exponer las páginas Pedidos, Tickets y Catálogo que consuman los endpoints de lectura con estados de carga, error y vacío, con datos seed realistas (nombres de empresas/órdenes reales, sin "Test123" ni "Lorem ipsum").

#### Scenario: Tabla con datos
- **WHEN** la página Pedidos/Tickets/Catálogo recibe datos
- **THEN** renderiza filas con formato apropiado para la demo (fechas en formato local, montos con dos decimales)

#### Scenario: Sin resultados
- **WHEN** un filtro/página no devuelve filas
- **THEN** la UI muestra un estado vacío claro en lugar de una tabla vacía cruda