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