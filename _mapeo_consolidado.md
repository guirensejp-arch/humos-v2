## Pedidos

### Lista (pedidos_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título «Pedidos» + toggle Lista/Cuadrícula | preferencia de vista (Lista vs Cuadrícula) | `configuracion.vista_pedidos` | leer/editar | `GET /pedidos`, `PUT /configuracion` |
| Botón «+ Nuevo pedido» | navegación a alta | — | leer | `GET /pedidos/nuevo` |
| Filtro «Estado» | estado del pedido (todos/pendiente/confirmado/en preparación/listo/entregado/cancelado) | `pedido.estado` | leer (query param) | `GET /pedidos?estado=` |
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
- `pedido.estado` toma valores de una lista cerrada (enum centralizado, desacoplado del origen): pendiente, confirmado, en preparación, listo, entregado, cancelado.
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
| Botón «Anular» | anulación (no borra) | `pedido.estado` = cancelado + `auditoria` | editar | `PATCH /pedidos/:id/anular` |
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
- **«Anular» no borra** el registro: marca `pedido.estado = 'cancelado'` y guarda quién/cuándo en `auditoria`. Las acciones irreversibles piden confirmación en el UI antes de disparar el endpoint.
- El «Historial del pedido» se alimenta de `auditoria` (no de un campo propio): cada transición de estado escribe una fila `(usuario_id, fecha_hora, accion)`.
- «Pedidos previos» es un conteo agregado (`pedido` por `cliente_id`), no un campo persistido en `cliente`.
- Soft-delete NO aplica a `pedido` (queda historial); la anulación es por cambio de estado, no por borrado físico ni `activo=false`.

## Caja

### Turno (caja_turno.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título «Caja» + chip «Turno abierto/cerrado» | estado del turno en curso | `turno_caja.estado` (abierto/cerrado) | leer | `GET /caja/turno` |
| Subtítulo «desde 09:00 · cajero A» | hora de apertura y cajero | `turno_caja.fecha_apertura`, `turno_caja.usuario_id` (JOIN `usuario`) | leer | `GET /caja/turno` |
| Botón «Abrir turno» (si no hay turno) + campo «fondo inicial» | monto de fondo tipeado por el cajero al abrir | `turno_caja.fondo_inicial` (centavos, entero) | crear | `POST /caja/turno` |
| Botón «Arqueo» | navega al arqueo | — | leer | `GET /caja/arqueo` |
| Botón «Cerrar turno» (solo habilitado tras arqueo) | cierra el turno | `turno_caja.estado` = cerrado, `turno_caja.fecha_cierre` | editar | `POST /caja/turno/cerrar` |
| KPI «Ventas del turno» | suma de ventas del turno | `movimiento_caja.monto` (SUM por tipo=venta, `turno_caja_id`) | leer | `GET /caja/turno` |
| KPI «Pedidos» | cantidad de pedidos del turno | `pedido` (COUNT por `turno_caja_id` y fecha) | leer | `GET /caja/turno` |
| KPI «Ingresos extra» | suma de ingresos no-venta | `movimiento_caja.monto` (SUM por tipo=ingreso) | leer | `GET /caja/turno` |
| KPI «Egresos» | suma de egresos | `movimiento_caja.monto` (SUM por tipo=egreso) | leer | `GET /caja/turno` |
| Panel «Ventas del día por método de pago» (Método / Ventas / Monto) | ventas agrupadas por medio de pago | `movimiento_caja` GROUP BY `metodo_pago_id`, con `pedido.metodo_pago_id` | leer | `GET /caja/turno` |
| Panel «Últimos movimientos» | movimientos recientes | `movimiento_caja` (últimos N, con `usuario_id` y `fecha_hora`) | leer | `GET /caja/turno` |
| Botón «+ Movimiento» | abre carga de ingreso/egreso | — | leer | `GET /caja/movimientos` |

**Reglas / validación:**
- El turno tiene dos estados: abierto/cerrado. Sin turno abierto, la pantalla muestra solo «Abrir turno» con campo de **fondo inicial** que tipea el cajero (monto variable, no fijo).
- «Cerrar turno» **no se habilita** hasta completar el arqueo (Sección 9 del doc). El cierre es una acción irreversible que pide confirmación.
- `turno_caja.usuario_id` (cajero que abre) NOT NULL, FK `usuario.id`. Columnas de auditoría (`usuario_id`, `fecha_hora`, `accion`) en `turno_caja` y `movimiento_caja`.
- Métodos de pago configurables en Sistema (FK `metodo_pago`); las ventas por método se agregan solas con cada pedido confirmado.
- Ventas, ingresos extra y egresos son **agregados** (SUM/COUNT sobre `movimiento_caja` y `pedido`), no columnas persistidas en `turno_caja`.

### Arqueo (caja_arqueo.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| «Efectivo esperado (sistema)» | efectivo calculado por ventas | `movimiento_caja` (SUM por método=efectivo del turno) | leer (calc) | `GET /caja/arqueo` |
| «Efectivo contado (manual)» | monto tipeado por el cajero | `arqueo.efectivo_contado` (centavos, entero) | crear | `POST /caja/arqueo` |
| Conteo por billete/moneda (opcional) | desglose de billetes | `arqueo.desglose` (JSON, opcional) | crear | `POST /caja/arqueo` |
| «Otros métodos» (QR, débito, crédito) | montos no-efectivo (informativo) | `movimiento_caja` (SUM por método != efectivo) | leer | `GET /caja/arqueo` |
| «Diferencia» | efectivo esperado − contado | `arqueo.diferencia` (centavos, entero, calculado) | leer (calc) | `GET /caja/arqueo` |
| Campo «Motivo de la diferencia» (obligatorio si hay diferencia) | justificación | `arqueo.motivo_diferencia` | crear | `POST /caja/arqueo` |
| Check «Confirmo la diferencia y asumo la responsabilidad» | confirmación explícita | `arqueo.diferencia_confirmada` (bool) | crear | `POST /caja/arqueo` |
| Botón «Guardar arqueo y cerrar turno» | persiste arqueo + cierra turno | `arqueo` + `turno_caja` | crear/editar (todo-o-nada) | `POST /caja/arqueo` |
| Botón «Cancelar» | descarta | — | — | `GET /caja/turno` |

**Reglas / validación:**
- Regla dura: si `diferencia != 0`, **NO se puede cerrar** sin `motivo_diferencia` completado y `diferencia_confirmada = true` (Sección 9.2 Caja).
- `arqueo.turno_caja_id` FK → `turno_caja.id` NOT NULL, UNIQUE (un arqueo por turno).
- `arqueo.efectivo_contado` obligatorio y >= 0; moneda entera en centavos (nunca float).
- La diferencia y el motivo quedan en `auditoria` (quién, cuándo, cuánto) y se muestran en el cierre Z.
- Transacción todo-o-nada: guardar arqueo + cerrar turno (+ auditoría) en un único commit; si algo falla, rollback.

### Cierre Z (caja_cierre_z.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Cabecera «Cierre Z — Turno 09:00–14:00» | resumen del turno cerrado | `turno_caja` (fecha_apertura, fecha_cierre, usuario) | leer | `GET /caja/cierre-z/:turno_id` |
| Líneas «Ventas por método (Efectivo/QR/Débito/Crédito)» | desglose de ventas | `movimiento_caja` GROUP BY `metodo_pago_id` | leer | `GET /caja/cierre-z/:turno_id` |
| «Total ventas» | suma de ventas | `movimiento_caja.monto` (SUM ventas) | leer (calc) | `GET /caja/cierre-z/:turno_id` |
| «Descuentos (cantidad y monto)» | total y conteo de descuentos | `pedido.descuento` (SUM + COUNT del turno) | leer (calc) | `GET /caja/cierre-z/:turno_id` |
| «IVA (21%)» | línea informativa | sin columna impositiva en v1 | leer (informativo) | `GET /caja/cierre-z/:turno_id` |
| «Ingresos extra» | suma ingresos no-venta | `movimiento_caja` (SUM tipo=ingreso) | leer (calc) | `GET /caja/cierre-z/:turno_id` |
| «Egresos» | suma egresos | `movimiento_caja` (SUM tipo=egreso) | leer (calc) | `GET /caja/cierre-z/:turno_id` |
| «TOTAL CAJA» | total consolidado | cálculo: ventas + ingresos − egresos (centavos, entero) | leer (calc) | `GET /caja/cierre-z/:turno_id` |
| «Diferencia arqueo» | diferencia registrada del turno | `arqueo.diferencia` | leer | `GET /caja/cierre-z/:turno_id` |
| Botón «Imprimir (térmica)» | imprime ticket 80mm | — | leer | `GET /caja/cierre-z/:turno_id/imprimir` |
| Botón «Exportar CSV» | descarga versión extendida | `turno_caja` + `movimiento_caja` | leer | `GET /caja/cierre-z/:turno_id/exportar.csv` |

**Reglas / validación:**
- El cierre Z se **genera al cerrar el turno** y queda guardado en el historial (no se recalcula suelto).
- Ticket térmico 80mm = versión acotada. Versión completa/extensa (historial largo) se exporta CSV/PDF (Sección 5).
- IVA (21%) es **línea informativa** en v1, no cálculo impositivo (Sección 3.8); el modelo de precios queda abierto a alícuotas reales a futuro sin cambio destructivo.
- Todos los montos del ticket salen de agregados sobre `movimiento_caja`/`pedido` para el `turno_caja_id`, nunca se persisten duplicados.

### Ingresos / Egresos (caja_movimientos.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Movimiento» | abre formulario de carga | — | leer | `GET /caja/movimientos` |
| Select «Tipo *» (Ingreso/Egreso) | sentido del movimiento | `movimiento_caja.tipo` | crear | `POST /caja/movimientos` |
| Campo «Monto *» | monto (acepta coma decimal) | `movimiento_caja.monto` (centavos, entero) | crear | `POST /caja/movimientos` |
| Select «Categoría» (Proveedor/Gasto/Retiro dueño/Vuelto/Otro) | categoría del movimiento | `movimiento_caja.categoria` | crear | `POST /caja/movimientos` |
| Select «Vincular a proveedor» (opcional) | proveedor asociado | `movimiento_caja.proveedor_id` (FK `proveedor.id`, nullable) | crear | `POST /caja/movimientos` |
| Campo «Motivo / descripción *» | texto libre | `movimiento_caja.motivo` | crear | `POST /caja/movimientos` |
| Botón «Guardar movimiento» | persiste | `movimiento_caja` | crear | `POST /caja/movimientos` |
| Lista «Movimientos del turno» | movimientos con hora y usuario | `movimiento_caja` (JOIN `usuario`, `proveedor`) | leer | `GET /caja/movimientos` |

**Reglas / validación:**
- Tipo, monto y motivo **obligatorios** (NOT NULL). Monto siempre **positivo**; el tipo define si suma o resta.
- Egreso sin monto o sin motivo: **bloquear** (Sección 9.2 Caja).
- Aceptar formato decimal argentino (coma) sin ambigüedad → se convierte a centavos entero.
- Si se vincula un proveedor, alimenta el módulo Proveedores (genera ticket de carga/merma, Sección 3.4).
- Todo movimiento externo a una venta queda en `auditoria` (usuario, hora, motivo) — columnas `usuario_id`, `fecha_hora`, `accion` en `movimiento_caja`.
- `movimiento_caja.turno_caja_id` FK → `turno_caja.id` NOT NULL (todo movimiento pertenece a un turno abierto).

### Historial (caja_historial.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Filtro «Desde / Hasta» | rango de fechas | `turno_caja.fecha_cierre` (o fecha_apertura) | leer (query param) | `GET /caja/historial?desde=&hasta=` |
| Filtro «Cajero» | filtra por cajero | `turno_caja.usuario_id` | leer (query param) | `GET /caja/historial?cajero=` |
| Columna «Fecha» | fecha del turno | `turno_caja.fecha_apertura` (fecha) | leer | `GET /caja/historial` |
| Columna «Turno» | rango horario | `turno_caja.fecha_apertura`–`fecha_cierre` | leer | `GET /caja/historial` |
| Columna «Cajero» | usuario del turno | `turno_caja.usuario_id` (JOIN `usuario`) | leer | `GET /caja/historial` |
| Columna «Ventas» | total ventas del turno | `movimiento_caja` (SUM ventas por turno) | leer (calc) | `GET /caja/historial` |
| Columna «Pedidos» | cantidad de pedidos | `pedido` (COUNT por turno) | leer (calc) | `GET /caja/historial` |
| Columna «Diferencia» | diferencia de arqueo | `arqueo.diferencia` (JOIN) | leer | `GET /caja/historial` |
| Botón «Ver Z» | reabre cierre Z del turno | `turno_caja.id` | leer | `GET /caja/cierre-z/:turno_id` |

**Reglas / validación:**
- Solo lista **turnos cerrados**; los turnos abiertos no aparecen acá (viven en `GET /caja/turno`).
- Ventas, pedidos y diferencia son agregados/joins, no columnas persistidas en `turno_caja`.
- El historial completo (largo) se exporta CSV/PDF, nunca ticket térmico (Sección 5).

## Clientes

### Lista (clientes_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Nuevo cliente» | alta manual (rara vez) | — | crear | `GET /clientes/nuevo` |
| Campo «Buscar (nombre/teléfono)» | búsqueda | `cliente.nombre`, `cliente.telefono` | leer (query param) | `GET /clientes?q=` |
| Botón «Buscar» | aplica búsqueda | — | leer | `GET /clientes` |
| Columna «Nombre» | apellido, nombre | `cliente.apellido`, `cliente.nombre` | leer | `GET /clientes` |
| Columna «Teléfono» | teléfono normalizado | `cliente.telefono` (normalizado, UNIQUE) | leer | `GET /clientes` |
| Columna «Pedidos» | cantidad de pedidos | `pedido` (COUNT por `cliente_id`) | leer (calc) | `GET /clientes` |
| Columna «Último» | fecha del último pedido | `pedido.fecha_hora` (MAX) | leer (calc) | `GET /clientes` |
| Columna/chiip «Recurrente» | flag de cliente recurrente | `cliente` (derivado del conteo de pedidos) | leer (calc) | `GET /clientes` |
| Botón «Ver» | abre detalle | `cliente.id` | leer | `GET /clientes/:id` |

**Reglas / validación:**
- La lista se **puebla automáticamente desde Pedidos**; rara vez se carga a mano (Sección 3.3).
- **Teléfono normalizado** (`cliente.telefono` UNIQUE): acepta variantes (11…, +54 9 11…, 15…) y guarda formato único. La búsqueda matchea el mismo cliente aunque se tipeara distinto.
- «Recurrente» es derivado: cliente con >= N pedidos previos (umbral a definir); **no es columna persistida** — se calcula por conteo para evitar dato stale.
- «Pedidos» y «Último» son agregados (COUNT/MAX sobre `pedido`), no columnas en `cliente`.

### Detalle (cliente_detalle.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título «Apellido, Nombre» | nombre del cliente | `cliente.apellido`, `cliente.nombre` | leer | `GET /clientes/:id` |
| Subtítulo «teléfono · dirección» | contacto | `cliente.telefono`, `cliente.direccion` | leer | `GET /clientes/:id` |
| Botón «Editar» | edita datos | `cliente` | editar | `GET /clientes/:id/editar` |
| Datos: teléfono, dirección, notas | datos de contacto | `cliente.telefono`, `cliente.direccion`, `cliente.notas` | leer | `GET /clientes/:id` |
| Panel «Cuenta corriente / fiado»: «Saldo adeudado» | saldo de fiado | `cliente.saldo_adeudado` (centavos, entero) | leer | `GET /clientes/:id` |
| «Historial de pagos» | movimientos de fiado | `fiado` (o `movimiento_fiado`) | leer | `GET /clientes/:id/fiado` |
| Tabla «Historial de pedidos» (#, Fecha, Total, Estado, Ver) | pedidos del cliente | `pedido` (JOIN `cliente_id`) | leer | `GET /clientes/:id/pedidos` |
| Botón «Ver» (por pedido) | abre pedido | `pedido.id` | leer | `GET /pedidos/:id` |

**Reglas / validación:**
- El fiado/cuenta corriente **no es prioritario hoy para Humos**, pero el modelo lo contempla (central si se vende a un almacén). Columna `saldo_adeudado` moneda entera en centavos.
- Historial de pagos de fiado: **pendiente de decisión** en el mapping — el doc no define si es tabla propia (`movimiento_fiado`) o se desprende de `pedido` + `movimiento_caja` (categoría "Vuelto"/pago). No forzar: marcar para confirmar en la etapa de modelo de datos.
- El historial de pedidos es `pedido` filtrado por `cliente_id`, no una tabla separada.
- Teléfono normalizado (misma regla que en lista).

## Proveedores

### Proveedores — Lista (proveedores_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Nuevo proveedor» | abre alta de proveedor | — | crear | `GET /proveedores/nuevo` |
| Campo «Buscar» (Nombre, rubro…) | texto de búsqueda | `proveedor.nombre`, `proveedor.rubro` | leer | `GET /proveedores?q=` |
| Filtro «Rubro» (Todos ▾) | filtro por rubro | `proveedor.rubro` | leer | `GET /proveedores?rubro=` |
| Botón «Filtrar» | aplica filtros | — | leer | `GET /proveedores` |
| Columna «Proveedor» | nombre | `proveedor.nombre` | leer | — |
| Columna «Rubro» | rubro | `proveedor.rubro` | leer | — |
| Columna «Insumos» (cantidad) | conteo de insumos asociados | `insumo` (COUNT FK `proveedor_id`) | leer | `GET /proveedores/:id` |
| Columna «Última compra» (fecha) | fecha de última compra | `lote.fecha_ingreso` (MAX) | leer | — |
| Columna «Estado» (Activo/Inactivo) | flag de borrado lógico | `proveedor.activo` | leer | — |
| Botón «Ver» | abre detalle | — | leer | `GET /proveedores/:id` |
| Botón «Editar» | abre edición | — | leer | `GET /proveedores/:id/editar` |
| Botón «Exportar CSV» | descarga listado | `proveedor` | leer | `GET /proveedores/exportar.csv` |
| (Acción eliminar implícita) | desactivar proveedor | `proveedor.activo` | editar | `PUT /proveedores/:id/desactivar` |

**Reglas / validación:**
- Columna «Estado» = soft-delete: la baja setea `proveedor.activo = false`, nunca DELETE físico. Los lotes/insumos ya cargados y los tickets históricos conservan la FK al proveedor (NO eliminar).
- `proveedor.rubro` NOT NULL (obligatorio al alta); `proveedor.nombre` NOT NULL.
- Auditoría: `proveedor` es tabla sensible → columnas `usuario_id`, `fecha_hora`, `accion`.
- Los tickets de carga/merma/desperdicio/consumo (que se generan desde Proveedores) consumen insumos y quedan en auditoría + ticket térmico 80mm.
- Los insumos asociados se descuentan por lote en Inventario (FK `insumo.proveedor_id` → `proveedor.id`).

### Proveedor — Detalle (proveedor_detalle.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título «Distribuidora La Estancia» | nombre del proveedor | `proveedor.nombre` | leer | `GET /proveedores/:id` |
| Subtítulo «Rubro: Carnes» | rubro | `proveedor.rubro` | leer | — |
| Subtítulo «Contacto: 11 5555 6666» | teléfono | `proveedor.telefono` | leer | — |
| Subtítulo «Estado: Activo» | flag | `proveedor.activo` | leer | — |
| Botón «Atrás» | navega a lista | — | leer | `GET /proveedores` |
| Botón «Editar» | habilita edición | — | leer | `GET /proveedores/:id/editar` |
| Campo «Nombre *» | nombre | `proveedor.nombre` | editar | `PUT /proveedores/:id` |
| Campo «Rubro *» (ddl) | rubro | `proveedor.rubro` | editar | `PUT /proveedores/:id` |
| Campo «Teléfono» | teléfono | `proveedor.telefono` | editar | `PUT /proveedores/:id` |
| Campo «Notas» (días/condiciones) | notas libres | `proveedor.notas` | editar | `PUT /proveedores/:id` |
| Botón «Guardar» | persiste cambios | `proveedor` | editar | `PUT /proveedores/:id` |
| Botón «Desactivar» | soft-delete | `proveedor.activo` | editar | `PUT /proveedores/:id/desactivar` |
| Botón «+ Cargar insumo» | alta de insumo asociado | `insumo` | crear | `POST /insumos` |
| Columna «Insumo» | nombre insumo | `insumo.nombre` | leer | `GET /proveedores/:id/insumos` |
| Columna «Rubro» | rubro insumo | `insumo.rubro` | leer | — |
| Columna «Último costo» ($7.000) | costo unitario | `insumo.costo` `(centavos, entero)` | leer | — |
| Columna «Unidad» (kg) | unidad de medida | `insumo.unidad` | leer | — |
| Botón «Editar» (por insumo) | edita insumo | `insumo` | editar | `PUT /insumos/:id` |

**Reglas / validación:**
- Desactivar = soft-delete: `proveedor.activo = false`; deja de aparecer en cargas nuevas, insumos y tickets históricos intactos.
- `proveedor.nombre` y `proveedor.rubro` NOT NULL. Teléfono normalizado (misma regla que `cliente.telefono`).
- `insumo.proveedor_id` FK → `proveedor.id`; `insumo` es tablet sensitive → auditoría `usuario_id`, `fecha_hora`, `accion`. Soft-delete via `insumo.activo`.
- `insumo.costo` moneda entera en centavos (nunca float). El cambio de «último costo» se refleja en vivo en el food cost de las recetas que usan ese insumo (recalcular margen tras `PUT /insumos/:id`).
- Unidad de medida compatible con la conversión (kg↔g, l↔ml) — no cargar «kg» donde va «litros».


## Recetas / Productos

### Lista (recetas_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Nueva receta» | alta de producto/receta | — | crear | `GET /recetas/nuevo` |
| Filtro «Buscar» | búsqueda por nombre | `producto.nombre` | leer (query param) | `GET /recetas?q=` |
| Filtro «Categoría» | filtro por categoría | `producto.categoria` | leer (query param) | `GET /recetas?categoria=` |
| Columna «Producto» | nombre del producto | `producto.nombre` | leer | `GET /recetas` |
| Columna «Precio venta» | precio al público | `producto.precio_venta` (centavos, entero) | leer | `GET /recetas` |
| Columna «Costo insumos» | food cost (suma de insumos) | `producto_insumo` (SUM costo por cantidad) | leer (calc) | `GET /recetas` |
| Columna «Margen» | porcentaje de margen | cálculo: (precio − costo) / precio | leer (calc) | `GET /recetas` |
| Columna/chiip «Estado» (Activo/Inactivo) | flag de borrado lógico | `producto.activo` | leer | `GET /recetas` |
| Botón «Editar» | abre edición | — | leer | `GET /recetas/:id/editar` |
| Botón «Exportar CSV» | descarga listado | `producto` | leer | `GET /recetas/exportar.csv` |

**Reglas / validación:**
- **Soft-delete**: «Eliminar» marca `producto.activo = false`, nunca DELETE físico; pedidos históricos siguen referenciando el producto. Inactivo no aparece en nuevas ventas (Sección 9.1).
- Margen < 30% se resalta (señal de subir precio o revisar receta). El **food cost se recalcula en vivo** si cambia el precio de un insumo (Sección 3.6).
- `producto.precio_venta` y costos como **entero en centavos** (nunca float). Margen es derivado (no persistido): `(precio − costo) / precio`.
- Columnas de auditoría (`usuario_id`, `fecha_hora`, `accion`) en `producto` y `producto_insumo` (tabla sensible, tabla de precios).
- «Costo insumos» es agregado sobre `producto_insumo` (cantidad × costo unitario del insumo), no una columna persistida en `producto`.

### Detalle / Edición (receta_detalle.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Título nombre + estado | nombre y flag | `producto.nombre`, `producto.activo` | leer | `GET /recetas/:id` |
| Campo «Nombre *» | nombre del producto | `producto.nombre` | editar | `PUT /recetas/:id` |
| Campo «Precio de venta *» | precio | `producto.precio_venta` (centavos, entero) | editar | `PUT /recetas/:id` |
| Campo «Categoría» | categoría | `producto.categoria` | editar | `PUT /recetas/:id` |
| Campo «Margen objetivo (%)» | margen deseado (informativo) | `producto.margen_objetivo` | editar | `PUT /recetas/:id` |
| Panel «Food cost» (costo total / precio / margen bruto) | cálculo en vivo | `producto_insumo` (SUM) + `producto.precio_venta` | leer (calc) | `GET /recetas/:id` |
| Botón «+ Agregar insumo» | agrega línea de receta | `producto_insumo` | crear | `POST /recetas/:id/insumos` |
| Tabla «Insumos de la receta» (Insumo / Cantidad / Unidad / Costo / Quitar) | composición del producto | `producto_insumo` (insumo_id, cantidad, unidad, costo) | leer/editar/borrar | `GET /recetas/:id`, `PUT /recetas/:id/insumos/:insumo_id`, `DELETE /recetas/:id/insumos/:insumo_id` |
| Botón «Guardar receta» | persiste | `producto` + `producto_insumo` | editar | `PUT /recetas/:id` |
| Botón «Volver» | navega a lista | — | leer | `GET /recetas` |

**Reglas / validación:**
- Los insumos usan **conversión de unidades** (kg↔g, l↔ml) para sumar insumos en unidades distintas en un mismo costo.
- `producto_insumo` = tabla de unión: `producto_id` FK → `producto.id`, `insumo_id` FK → `insumo.id`, `cantidad` (decimal), `unidad`.
- **Receta con insumo inactivo/inexistente o cantidades que no cierran: se advierte y no se guarda** (Sección 9.2 Recetas).
- Food cost y margen se **recalculan en vivo** con cada insumo agregado o precio cambiado; precios siempre centavos enteros (Sección 9.1).
- El cambio de «último costo» de un insumo (por `PUT /insumos/:id`) recalcula el food cost de las recetas que lo usan — no se almacena duplicado.

## Promociones

### Lista (promociones_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Nueva promoción» | alta de promoción | — | crear | `GET /promociones/nuevo` |
| Columna «Promoción» | nombre | `promocion.nombre` | leer | `GET /promociones` |
| Columna «Descuento» | tipo/valor del descuento | `promocion.tipo_descuento`, `promocion.valor` | leer | `GET /promociones` |
| Columna «Vigencia» | rango de fechas | `promocion.vigencia_desde`, `promocion.vigencia_hasta` | leer | `GET /promociones` |
| Columna/chiip «Estado» (Vigente/Futura/Vencida) | estado derivado de vigencia | `promocion.vigencia_desde`/`vigencia_hasta` (vs hoy) | leer (calc) | `GET /promociones` |
| Botón «Editar» | abre edición | — | leer | `GET /promociones/:id/editar` |
| Botón «Desactivar» | soft-delete | `promocion.activo` = false | editar | `PUT /promociones/:id/desactivar` |

**Reglas / validación:**
- Aplicación **automática vs manual** se define en la misma promoción.
- Descuento de promoción y descuento manual en un mismo pedido **conviven**, ambos en auditoría (Sección 3.2).
- Estado (vigente/futura/vencida) es derivado de comparar `vigencia_desde`/`vigencia_hasta` con hoy; no es columna persistida.
- Desactivar = **soft-delete** (`promocion.activo = false`); no se borra el histórico de uso en pedidos.
- Columnas de auditoría en `promocion` (tabla sensible, toca precios/margen).

### Nueva / Edición (promocion_nueva.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Campo «Nombre *» | nombre de la promoción | `promocion.nombre` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Select «Tipo de descuento *» (Porcentaje / Monto fijo / 2×1) | tipo | `promocion.tipo_descuento` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Campo «Valor *» | monto o porcentaje | `promocion.valor` (centavos, entero si monto) | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Select «Aplicación» (Automática/Manual) | modo de aplicación | `promocion.aplicacion` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Campo «Vigente desde *» | fecha inicial | `promocion.vigencia_desde` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Campo «Vigente hasta *» | fecha final | `promocion.vigencia_hasta` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Selector «Productos alcanzados» (pills) | productos incluidos | `promocion_producto` (JOIN) | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Botón «Guardar promoción» | persiste | `promocion` + `promocion_producto` | crear/editar | `POST /promociones`, `PUT /promociones/:id` |
| Botón «Cancelar» | descarta | — | — | `GET /promociones` |

**Reglas / validación:**
- Descuento como **entero en centavos** (nunca float); `vigencia_hasta` no puede ser pasada (fecha de vencimiento NOT NULL y en el futuro al crearla).
- «Automática» se aplica sola al cargar el pedido; «manual» requiere que el cajero la elija. Ambos descuentos (promo + manual) conviven y quedan auditados.
- `promocion_producto` = tabla de unión: `promocion_id` FK → `promocion.id`, `producto_id` FK → `producto.id` (UNIQUE conjunto).
- Tipo «2×1» es un caso especial de descuento; se recomienda modelarlo como `tipo_descuento` con lógica propia o como flag, **pendiente de decisión** en el modelo de datos.
- `promocion.nombre` y `tipo_descuento` NOT NULL; `valor` NOT NULL.

## Inventario

### Lista por lote (inventario_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Subtítulo «Nivel de stock por lote · FEFO ON» | flag de configuración | `configuracion.fefo_activo` (bool) | leer | `GET /inventario` |
| Botón «Conteo físico» | navega al conteo | — | leer | `GET /inventario/conteo` |
| Botón «+ Cargar lote» | alta de lote | — | crear | `GET /inventario/lote/nuevo` |
| Filtro «Buscar insumo» | búsqueda por nombre | `insumo.nombre` | leer (query param) | `GET /inventario?q=` |
| Filtro «Categoría» | filtro por categoría | `insumo.rubro` (o categoria) | leer (query param) | `GET /inventario?categoria=` |
| Filtro «Vencimiento» | por estado de vencimiento | `lote.fecha_vencimiento` | leer (query param) | `GET /inventario?vencimiento=` |
| Columna «Insumo» | nombre del insumo | `insumo.nombre` | leer | `GET /inventario` |
| Columna «Lote #» | número de lote | `lote.numero` (o id) | leer | `GET /inventario` |
| Columna «Ingresó» | fecha de ingreso | `lote.fecha_ingreso` | leer | `GET /inventario` |
| Columna «Vence» | fecha de vencimiento | `lote.fecha_vencimiento` | leer | `GET /inventario` |
| Columna/chiip «Estado» (OK / Por vencer / Vencida) | estado derivado del vencimiento | `lote.fecha_vencimiento` (comparado con hoy) | leer (calc) | `GET /inventario` |
| Columna «Stock» | cantidad restante del lote | `lote.cantidad` (decimal en unidad del insumo) | leer | `GET /inventario` |
| Columna «Unidad» | unidad de medida | `insumo.unidad` | leer | `GET /inventario` |
| Botón «Exportar CSV» | descarga listado | `insumo` + `lote` | leer | `GET /inventario/exportar.csv` |

**Reglas / validación:**
- El stock **NO se ve como total**: se desglosa por `lote` (fecha_ingreso + fecha_vencimiento), base del alerta de vencimiento y de FEFO.
- `lote.fecha_vencimiento` NOT NULL y **no en el pasado** al cargar (Sección 9.2). Estado "OK/Por vencer/Vencida" es derivado de comparar `fecha_vencimiento` con hoy, no persistido.
- **FEFO**: con `configuracion.fefo_activo = true`, la venta consume primero el lote que vence antes. El campo "Consumir manual" aparece solo con FEFO OFF. OFF **conserva** lotes y alertas, solo no fuerza el orden.
- Lote vencido = **bloqueo de venta** (Sección 9.2 Pedidos).
- El descuento de lote al confirmar pedido es **todo-o-nada** (junto con caja y auditoría).
- Stock "0,0" de lote vencido queda visible y auditado: el lote **no se borra** (sin soft-delete en lote, queda historial).
- `lote.insumo_id` FK → `insumo.id` NOT NULL. Columnas de auditoría (`usuario_id`, `fecha_hora`, `accion`) en `lote` e `insumo`.
- Unidades compatibles con conversión kg↔g / l↔ml (Sección 5); `insumo.unidad` define la unidad de carga.

### Conteo físico (inventario_conteo.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Selector de alcance «Conteo total / Por categoría / Por insumo» | alcance del conteo | — (filtro de vista) | leer | `GET /inventario/conteo?alcance=` |
| Columna «Insumo» | insumo a contar | `insumo.nombre` | leer | `GET /inventario/conteo` |
| Columna «Sistema (kg/l/ud)» | stock teórico del sistema | `lote.cantidad` (SUM por insumo) | leer | `GET /inventario/conteo` |
| Campo «Contado» | stock real tipeado | `conteo.cantidad_contada` (decimal, unidad del insumo) | crear | `POST /inventario/conteo` |
| Columna «Dif.» | diferencia sistema − contado | cálculo: teórico − contado | leer (calc) | `GET /inventario/conteo` |
| Resumen «Items con diferencia» / «Diferencia total» | agregado del conteo | `conteo` (COUNT/SUM de diferencias) | leer (calc) | `GET /inventario/conteo` |
| Campo «Motivo del ajuste» (obligatorio si hay diferencias) | justificación | `conteo.motivo` | crear | `POST /inventario/conteo` |
| Botón «Aplicar ajuste» | persiste ajuste + ticket | `conteo` + `lote` + `movimiento_inventario` + `auditoria` | crear (todo-o-nada) | `POST /inventario/conteo` |
| Botón «Cancelar» | descarta | — | — | `GET /inventario` |

**Reglas / validación:**
- La celda «Contado» se tipea en la **unidad del insumo** (kg, l, ud); no hay conversión implícita en pantalla.
- Cualquier diferencia queda **auditada** y sugiere ticket de merma/desperdicio.
- «Aplicar ajuste» genera: movimiento en Inventario + ticket de merma/desperdicio + registro en `auditoria` (quién, cuándo, cuánto). Todo-o-nada.
- Motivo del ajuste **obligatorio si hay diferencias**; si todo cuadra (diferencia 0), el ajuste no requiere motivo.
- `conteo.usuario_id` FK → `usuario.id` NOT NULL; `conteo.fecha_hora` automática. Columnas de auditoría presentes.
- El ajuste actualiza `lote.cantidad` con el valor contado (reconcilia sistema contra real); la diferencia (merma/desperdicio) se registra como movimiento para trazabilidad, no se sobreescribe en silencio.

## Usuarios

### Lista (usuarios_lista.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Botón «+ Nuevo usuario» | alta de empleado | — | crear | `GET /usuarios/nuevo` |
| Columna «Nombre» | nombre del empleado | `usuario.nombre` (+ `apellido`) | leer | `GET /usuarios` |
| Columna/chiip «Rol» (Admin/Cajero/Cadete) | rol del usuario | `usuario.rol` (FK `rol` o enum) | leer | `GET /usuarios` |
| Columna «Pedidos entregados» | conteo de entregas (solo cadetes) | `pedido` (COUNT por `cadete_id`) | leer (calc) | `GET /usuarios` |
| Columna/chiip «Estado» (Activo/Inactivo) | flag | `usuario.activo` | leer | `GET /usuarios` |
| Botón «Editar» | edita usuario | — | leer | `GET /usuarios/:id/editar` |
| Botón «Reset contraseña» | genera clave temporal | `usuario.password_hash` (reset) | editar | `POST /usuarios/:id/reset-password` |
| Botón «Desactivar» | soft-delete de empleado | `usuario.activo` = false | editar | `PUT /usuarios/:id/desactivar` |

**Reglas / validación:**
- Rol **Cadete no accede a la web**: solo existe para asignar entregas y contar pedidos (útil si cobra por entrega). Roles posibles: Admin, Cajero, Cadete.
- «Reset contraseña» genera una **clave temporal** que el Admin pasa al empleado; el sistema **fuerza cambio en el próximo login** (sin mail automático en v1, Sección 3.9).
- Contraseñas siempre **hasheadas** (`usuario.password_hash`), nunca texto plano. Validación de hash en el login.
- Desactivar = **soft-delete** (`usuario.activo = false`); no se elimina para no romper auditoría/entregas históricas.
- «Pedidos entregados» es agregado (`pedido` COUNT por `cadete_id`), no columna persistida.
- `usuario.rol` NOT NULL; en v1 roles cerrados (Admin, Cajero, Cadete) — puede modelarse como tabla `rol` o enum; **pendiente de decisión** (consistencia con `_map_pedidos.md` que marcó lo mismo para `pedido.estado`).

## Sistema

### Configuración (sistema.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Toggle «FEFO (First Expired, First Out)» | flag de comportamiento de inventario | `configuracion.fefo_activo` (bool) | editar | `PUT /configuracion` |
| Toggle «Salón / Mozos» | habilita tipo entrega «mozo» | `configuracion.salon_mozos_activo` (bool) | editar | `PUT /configuracion` |
| Botón «Configurar» métodos de pago | agregar/desactivar medios de pago | `metodo_pago` (activo) | crear/editar | `GET /configuracion/metodos-pago`, `PUT /metodos-pago/:id` |
| Select «Modo oscuro / claro» | apariencia | `configuracion.modo_oscuro` (bool) | editar | `PUT /configuracion` |
| Select «Tamaño de fuente» | apariencia | `configuracion.font_size` | editar | `PUT /configuracion` |
| Botón «Buscar» impresora térmica | dispositivo/nombre de la térmica 80mm | `configuracion.impresora_termica` | editar | `PUT /configuracion` |
| Botón «Exportar base» | backup de la base | — (dump de DB) | leer | `GET /sistema/backup` |
| Botón «Cerrar sesión» | logout | — | — | `POST /logout` |

**Reglas / validación:**
- `configuracion` es una tabla de **flags/parámetros de comportamiento**, no un módulo: `fefo_activo`, `salon_mozos_activo`, `modo_oscuro`, `font_size`, `impresora_termica`.
- Togglear FEFO a OFF **no elimina lotes ni alertas** (Sección 3.5); solo cambia el orden de descuento.
- `salon_mozos_activo` habilita el tipo de entrega «mozo» en Pedidos (configurable on/off para locales sin salón, Sección 3.2).
- Métodos de pago configurables: tabla `metodo_pago` con `activo` (soft-disable; no borrar porque pedidos históricos la referencian).
- Backup de la base: botón manual para exportar toda la base (Sección 5); idealmente también automático.
- Fecha/hora: idealmente automática por internet (NTP), no manual (Sección 3.10).

## Login

### Login (login.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Campo «Usuario» | identificación | `usuario.email_personal` (o username) | leer | `POST /login` |
| Campo «Contraseña» | credencial | `usuario.password_hash` (verificación) | leer | `POST /login` |
| Botón «Ingresar» | autentica e inicia sesión | `usuario` (Flask-Login session) | crear (sesión) | `POST /login` |

**Reglas / validación:**
- Autenticación con contraseña **hasheada** (nunca texto plano), vía **Flask-Login** (Sección 1).
- Roles que pueden loguearse: **Admin y Cajero**. Cadete no accede a la web.
- Si el Admin reseteó la contraseña, al ingresar con la **temporal** el sistema **fuerza a cambiarla** en el próximo login (flag `usuario.debe_cambiar_clave`).
- `usuario.activo = false` impide el login (empleado desactivado no entra).
- El login registra sesión y puede auditarse (login/logout en `auditoria`).

## Inicio / Dashboard

### Dashboard (dashboard.html)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| Selector «Día / Semana / Mes / Histórico» | rango del dashboard | — (parámetro de agregación) | leer (query param) | `GET /dashboard?periodo=` |
| KPI «Ventas del día» | ventas del período | `movimiento_caja` (SUM ventas por período) | leer (calc) | `GET /dashboard` |
| KPI «Ticket promedio» | ventas / pedidos | `movimiento_caja` / `pedido` (agregado) | leer (calc) | `GET /dashboard` |
| KPI «Pedidos» | cantidad de pedidos | `pedido` (COUNT por período) | leer (calc) | `GET /dashboard` |
| KPI «Mayor margen» | producto de mayor margen | `producto` (margen por insumo) | leer (calc) | `GET /dashboard` |
| Panel «Más vendidos» | ranking de ventas | `pedido_detalle` GROUP BY `producto_id` (COUNT) | leer (calc) | `GET /dashboard` |
| Panel «Menos vendidos» | ranking inverso | `pedido_detalle` GROUP BY `producto_id` (COUNT ASC) | leer (calc) | `GET /dashboard` |
| Botón «Armar promoción →» | acceso rápido a Promociones | — | leer | `GET /promociones/nuevo` |
| Panel «Notificaciones» (stock bajo / por vencer / bajo margen) | alertas del sistema | `notificacion` (o derivadas de `lote` y `producto`) | leer | `GET /dashboard` |
| Botón «Descartar» (por notificación) | descarta notificación | `notificacion.leida` / `descartada` | editar | `PUT /notificaciones/:id/descartar` |
| «Descartar todas» | descarta de una vez | `notificacion` (batch) | editar | `PUT /notificaciones/descartar` |

**Reglas / validación:**
- Todos los KPIs y rankings son **agregados** (SUM/COUNT/AVG sobre `pedido`, `pedido_detalle`, `movimiento_caja`), no columnas persistidas.
- El selector Día/Semana/Mes/Histórico **recalcula** todo server-side (`GET /dashboard?periodo=`).
- «Producto menos vendido» es tan importante como el más vendido: señal de qué sacar o promocionar (Sección 3.1).
- «Ticket promedio» = total ventas / cantidad de pedidos (derivado).
- Notificaciones: stock bajo, bajo margen, productos por vencer — derivadas de `lote.fecha_vencimiento` y `producto` margen, con opción de descartar (Sección 3.1). **Pendiente de decisión**: si se persisten en tabla `notificacion` (con estado leída/descartada) o se calculan en vivo y el descarte es preferencia del usuario.
- «Mayor margen» sale del food cost de `producto_insumo`, mismo cálculo que Recetas.