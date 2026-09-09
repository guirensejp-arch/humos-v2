## Pedidos

### Lista (pedidos_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título «Pedidos» + toggle Lista/Cuadrícula | preferencia de vista (Lista vs Cuadrícula) | `configuracion.vista_pedidos` | leer/editar | `GET /pedidos`, `PUT /configuracion` |
| Botón «+ Nuevo pedido» | navegación a alta | — | leer | `GET /pedidos/nuevo` |
| Filtro «Estado» | estado del pedido (todos/pendiente/en preparación/en camino/entregado/anulado) | `pedido.estado` | leer (query param) | `GET /pedidos?estado=` |
| Filtro «Método de pago» | medio de pago | `pedido.metodo_pago_id` | leer (query param) | `GET /pedidos?metodo_pago=` |
| Filtro «Cadete» | cadete asignado | `pedido.cadete_id` | leer (query param) | `GET /pedidos?cadete=` |
| Filtro «Desde / Hasta» | rango de fechas | `pedido.fecha_hora` | leer (query param) | `GET /pedidos?desde=&hasta=` |
| Columna/fila «#» (Nº interno) | número de pedido | `pedido.numero` | leer | `GET /pedidos` |
| Columna «Hora» | hora de creación | `pedido.fecha_hora` | leer | `GET /pedidos` |
| Columna «Cliente» (nombre + teléfono) | cliente asociado | `cliente.nombre`, `cliente.apellido`, `cliente.telefono` (JOIN) | leer | `GET /pedidos` |
| Columna «Items» | cantidad de líneas | `pedido_detalle` (COUNT agregado) | leer | `GET /pedidos` |
| Columna «Total» | monto total | `pedido.total` (centavos, entero) | leer | `GET /pedidos` |
| Columna «Pago» | medio de pago | `metodo_pago.nombre` (JOIN) | leer | `GET /pedidos` |
| Columna «Cadete» / «— (retiro)» | cadete o entrega por retiro | `pedido.cadete_id`, `pedido.tipo_entrega` | leer | `GET /pedidos` |
| Columna «Estado» (chip) | estado del pedido | `pedido.estado` | leer | `GET /pedidos` |
| Botón «Ver» (fila) / tap en tarjeta | abrir detalle | `pedido.id` | leer | `GET /pedidos/:id` |
| Tarjetas móviles (celular) | mismos datos reagrupados, sin pérdida | mismas columnas de arriba | leer | `GET /pedidos` |

**Reglas / validación:**
- La vista Lista/Cuadrícula es un toggle de presentación, no dos endpoints; mismo `GET /pedidos`.
- «Nuevo cliente» en la columna Cliente corresponde a un pedido con cliente no registrado (teléfono raw sin `cliente_id` asociado); marcar en reglas como cliente "anónimo/ocasional" si no hay match telefónico.
- Los filtros se aplican en vivo (server-side query params en el `GET /pedidos`).
- `pedido.estado` toma valores de una lista cerrada: pendiente, en preparación, en camino, entregado, anulado.
- **pendiente de decisión:** dominio de valores del campo `estado` (ENUM en tabla vs catálogo) — confirmar con el doc de producto.

### Cuadrícula (pedidos_cuadricula.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Toggle Lista/Cuadrícula | preferencia de vista | `configuracion.vista_pedidos` | leer/editar | `PUT /configuracion` |
| Botón «+ Nuevo pedido» | navegación a alta | — | leer | `GET /pedidos/nuevo` |
| Cabecera tarjeta «#» | número de pedido | `pedido.numero` | leer | `GET /pedidos` |
| Chip «Estado» | estado | `pedido.estado` | leer | `GET /pedidos` |
| Línea «Hora · Cliente» | hora y cliente | `pedido.fecha_hora`, `cliente.nombre`, `cliente.apellido` | leer | `GET /pedidos` |
| Línea «N items — Total» | cantidad líneas y total | `pedido_detalle` (COUNT), `pedido.total` (centavos, entero) | leer | `GET /pedidos` |
| Línea «Pago · Cadete» | medio de pago y cadete/retiro | `metodo_pago.nombre`, `pedido.cadete_id`, `pedido.tipo_entrega` | leer | `GET /pedidos` |
| Tap/clic en tarjeta | abrir detalle | `pedido.id` | leer | `GET /pedidos/:id` |

**Reglas / validación:**
- Mismas reglas de filtrado y de datos que la vista Lista; solo cambia la densidad del layout (tarjetas).
- Usa las mismas tarjetas que la vista móvil de Lista: un único origen de datos `GET /pedidos`.

### Nuevo pedido (pedido_nuevo.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Campo «Teléfono (dato clave)» | teléfono del cliente | `cliente.telefono` (normalizado, UNIQUE) | leer/crear (lookup+autocarga) | `GET /clientes/buscar?telefono=` |
| Autocompletado de cliente por teléfono existente | match de cliente | `cliente` (id devuelto) | leer | `GET /clientes/buscar?telefono=` |
| Campo «Nombre» | nombre | `cliente.nombre` | crear | `POST /clientes` |
| Campo «Apellido» | apellido | `cliente.apellido` | crear | `POST /clientes` |
| Campo «Dirección» | dirección de entrega | `pedido.direccion` (o `cliente.direccion`) | crear | `POST /pedidos` |
| Campo «Notas del cliente» | notas de entrega | `pedido.notas` | crear | `POST /pedidos` |
| Botón «+ Agregar producto» (buscador) | selección de producto | `producto` (lookup) | leer | `GET /productos?q=` |
| Fila de tabla «Producto» | producto del pedido | `pedido_detalle.producto_id` | crear | `POST /pedidos/:id/detalle` |
| Fila de tabla «Cant.» | cantidad | `pedido_detalle.cantidad` | crear | `POST /pedidos/:id/detalle` |
| Fila de tabla «Subtotal» | subtotal por línea | `pedido_detalle.subtotal` (centavos, entero) | crear | `POST /pedidos/:id/detalle` |
| Icono «✕» por línea | quitar línea | `pedido_detalle` | borrar | `DELETE /pedidos/:id/detalle/:detalle_id` |
| «Subtotal» | subtotal acumulado | `pedido.subtotal` (centavos, entero) | calcular | — |
| Campo «Descuento manual» | monto o % de descuento | `pedido.descuento` (centavos, entero) | crear/editar | `POST /pedidos` |
| Select «Promoción» | promoción aplicada | `pedido.promocion_id` | crear/editar | `POST /pedidos` |
| Bloqueo/aviso de stock o lote que vence hoy | validación FEFO/stock | `pedido_detalle`, `lote`, `configuracion.fefo_activo` | leer (validación) | `GET /productos/:id/stock` |
| «Total» | total final | `pedido.total` (centavos, entero) | calcular | — |
| Select «Método de pago *» | medio de pago (obligatorio) | `pedido.metodo_pago_id` (FK `metodo_pago`, NOT NULL) | crear | `POST /pedidos` |
| Select «Tipo de entrega» | retiro vs delivery | `pedido.tipo_entrega` | crear | `POST /pedidos` |
| Select «Cadete» | cadete asignado (solo activos) | `pedido.cadete_id` (FK `usuario`) | crear | `POST /pedidos` |
| Botón «Confirmar pedido» | alta completa transaccional | `pedido` + `pedido_detalle` + `lote` + `movimiento_caja` + `auditoria` | crear (todo-o-nada) | `POST /pedidos` |
| Botón «Cancelar» | descartar borrador | — | — | `GET /pedidos` |

**Reglas / validación:**
- **Teléfono normalizado** (`cliente.telefono`, UNIQUE): acepta «11…», «+54 9 11…», «15…» y guarda formato único. Si ya existe, autocompleta cliente **sin duplicar en silencio** (lookup previo `GET /clientes/buscar`).
- **Método de pago** obligatorio (NOT NULL); el monto debe coincidir con el total.
- **Cadete**: solo cadetes activos (`usuario.activo = true`); el campo se oculta cuando tipo de entrega es «retiro».
- **Stock/FEFO**: si un producto sin stock o su lote vence hoy, se bloquea o advierte antes de confirmar; validación leída de `lote` + `configuracion.fefo_activo`.
- **Descuento manual + promoción** conviven: se aplican en orden y el total se recalcula. Todo descuento queda en `auditoria` (quién y cuánto).
- **Transacción todo-o-nada** al confirmar: pedido + detalle + descuento de stock por FEFO + asiento en caja (`movimiento_caja`) + `auditoria`. Si algo falla, rollback sin estado a medias.
- Columnas de auditoría (`usuario_id`, `fecha_hora`, `accion`) en `pedido`, `pedido_detalle` y `movimiento_caja`.

### Detalle (pedido_detalle.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Cabecera «Pedido #» | número de pedido | `pedido.numero` | leer | `GET /pedidos/:id` |
| Chip «Estado» | estado actual | `pedido.estado` | leer | `GET /pedidos/:id` |
| Línea «Creado … por cajero A» | origen/auditoría de creación | `pedido.usuario_id`, `pedido.fecha_hora` | leer | `GET /pedidos/:id` |
| Botón «Cambiar estado ▾» | transición de estado | `pedido.estado` | editar | `PATCH /pedidos/:id` |
| Botón «Anular» | anulación (no borra) | `pedido.estado` = anulado + `auditoria` | editar | `PATCH /pedidos/:id/anular` |
| Tabla «Productos» (× cantidad) | líneas del pedido | `pedido_detalle` (producto_id, cantidad, subtotal) | leer | `GET /pedidos/:id` |
| Fila «Total» | total | `pedido.total` (centavos, entero) | leer | `GET /pedidos/:id` |
| «Método» (Pago & entrega) | medio de pago | `metodo_pago.nombre` (JOIN) | leer | `GET /pedidos/:id` |
| «Entrega» | tipo y cadete | `pedido.tipo_entrega`, `pedido.cadete_id` | leer | `GET /pedidos/:id` |
| «Dirección» | dirección de entrega | `pedido.direccion` | leer | `GET /pedidos/:id` |
| «Notas» | notas de entrega | `pedido.notas` | leer | `GET /pedidos/:id` |
| «Nombre» / «Teléfono» (Cliente) | datos del cliente | `cliente.nombre`, `cliente.apellido`, `cliente.telefono` | leer | `GET /pedidos/:id` |
| «Pedidos previos: 4» | conteo histórico del cliente | `pedido` (COUNT por `cliente_id`) | leer | `GET /clientes/:id/historial` |
| Botón «Ver historial de cliente» | historial de pedidos del cliente | `pedido` (JOIN cliente) | leer | `GET /clientes/:id/pedidos` |
| Timeline «Historial del pedido» | cambios de estado con hh:mm y usuario | `auditoria` (`accion`, `usuario_id`, `fecha_hora`) | leer | `GET /pedidos/:id/historial` |

**Reglas / validación:**
- **«Anular» no borra** el registro: marca `pedido.estado = 'anulado'` y guarda quién/cuándo en `auditoria`. Las acciones irreversibles piden confirmación en el UI antes de disparar el endpoint.
- El «Historial del pedido» se alimenta de `auditoria` (no de un campo propio): cada transición de estado escribe una fila `(usuario_id, fecha_hora, accion)`.
- «Pedidos previos» es un conteo agregado (`pedido` por `cliente_id`), no un campo persistido en `cliente`.
- Soft-delete NO aplica a `pedido` (queda historial); la anulación es por cambio de estado, no por borrado físico ni `activo=false`.