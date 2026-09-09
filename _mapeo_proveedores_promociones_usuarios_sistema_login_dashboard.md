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