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