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