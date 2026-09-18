# Humos v2 — Arquitectura y Modelo de Datos

*Documento generado a partir del mapeo `_mapeo_consolidado.md` (11 módulos) y el documento de producto `humos-doc-producto.md`. Paso 3 del plan: definir arquitectura y modelo de datos completo antes de programar.*

---

## 0. Decisiones de diseño pendientes — RESUELTAS

Estas cuatro quedaron marcadas como "pendiente de decisión" en el mapeo. Acá se cierran de forma explícita:

| # | Tema | Decisión | Justificación |
|---|---|---|---|
| 1 | Dominio de `pedido.estado` y `usuario.rol` | **Enum de SQLAlchemy** (no tabla catálogo) | Listas cerradas, cortas y estables. Una tabla FK solo suma fricción en consultas sin aportar, porque no se editan desde el sistema. |
| 2 | Fiado / cuenta corriente | **Tabla propia `movimiento_fiado`** + `cliente.saldo_adeudado` derivado por SUM | El fiado es deuda del cliente, no movimiento de caja. Mezclarlo con `movimiento_caja` contaminaría el arqueo y el cierre Z. |
| 3 | Tipo "2×1" en promociones | **Enum `tipo_descuento`**: `PORCENTAJE`, `MONTO_FIJO`, `DOS_POR_UNO` | La lógica de cálculo vive en la capa de servicio, no en el modelo. |
| 4 | Notificaciones del dashboard | **Tabla `notificacion` persistida** (estado `leida`/`descartada`) | El wireframe pide "descartar individualmente" y "descartar todas", lo que implica estado persistente. Se generan por un cálculo/revisión, no en vivo. |

---

## 1. Stack técnico

| Capa | Decisión |
|---|---|
| Backend | Flask 3.x (Python 3.13) |
| ORM | SQLAlchemy (con Flask-SQLAlchemy) |
| Migraciones | Flask-Migrate (Alembic) |
| Autenticación | Flask-Login + hash de contraseñas (werkzeug `generate_password_hash`) |
| Frontend | Jinja2 + Bootstrap 5, responsive/mobile-first |
| Base de datos | SQLite en dev (single-tenant, una instancia por cliente); migrable a PostgreSQL sin cambio destructivo |
| Moneda | **Entero en centavos** en toda columna de dinero (nunca float) |
| Despliegue | Single-tenant: una instancia propia por cliente/negocio |
| Branding / white-label | `branding.yaml` + imágenes en `static/` (logo_cliente, logo_leudar); editable sin tocar templates |

### Estructura de la aplicación (factory pattern)

```
humos_v2/
├── run.py
├── config.py
├── requirements.txt
├── branding.yaml              # logo, nombre, colores del cliente (Día 0)
├── app/
│   ├── __init__.py          # create_app + registro de blueprints
│   ├── extensions.py        # db, login_manager, migrate
│   ├── models/              # modelos (ver sección 3)
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── pedido.py
│   │   ├── cliente.py
│   │   ├── proveedor.py
│   │   ├── inventario.py
│   │   ├── receta.py
│   │   ├── promocion.py
│   │   ├── caja.py
│   │   └── sistema.py
│   ├── services/            # lógica de negocio (FEFO, transacciones, food cost)
│   │   ├── __init__.py
│   │   ├── pedido_service.py
│   │   ├── inventario_service.py
│   │   ├── caja_service.py
│   │   ├── food_cost.py
│   │   └── phone_normalizer.py
│   ├── blueprints/          # rutas por módulo
│   ├── integraciones/      # adapters de plataformas externas (a futuro): base.py con OrigenPedidoAdapter
│   ├── templates/
│   ├── static/
│   └── utils/               # CSV, térmica, auditoría
```

**Por qué `services/`:** las reglas duras (FEFO, transacción todo-o-nada del pedido, cierre de caja sin confirmar diferencia) no pueden vivir en las rutas. Una capa de servicio las centraliza y las hace testeables.

---

## 2. Convenciones de nombres (obligatorias)

- Tablas y columnas en **español**, **singular**, **snake_case en minúsculas**.
- Tablas: `usuario`, `rol`, `cliente`, `pedido`, `pedido_detalle`, `producto`, `producto_insumo`, `insumo`, `proveedor`, `lote`, `movimiento_caja`, `turno_caja`, `arqueo`, `metodo_pago`, `promocion`, `promocion_producto`, `auditoria`, `movimiento_fiado`, `notificacion`, `configuracion`.
- **Auditoría** en TODA tabla sensible: `usuario_id`, `fecha_hora`, `accion` (creó/editó/eliminó).
- **Soft-delete** = columna `activo` (boolean) en: `proveedor`, `producto`, `insumo`, `usuario`, `promocion`, `metodo_pago`.
- **Moneda** = entero en centavos. Marcada en cada columna.
- **Fechas de vencimiento/ingreso** en `lote.fecha_vencimiento`, `lote.fecha_ingreso`.

---

## 3. Modelo de datos (esquema completo)

Notación: `PK` clave primaria · `FK` clave foránea · `NN` not null · `UQ` unique · `(centavos)` moneda entera · `*act` soft-delete.

### 3.1 Usuario y roles

**tabla `usuario`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(100) | NN | |
| apellido | str(100) | NN | |
| email_personal | str(120) | NN, UQ | para login (o username) |
| password_hash | str(255) | NN | hasheada, nunca texto plano |
| rol | enum | NN | `ADMIN`, `CAJERO`, `CADETE` |
| debe_cambiar_clave | bool | default false | fuerza cambio en próximo login tras reset |
| activo | bool | default true | soft-delete (`*act`) |

**Observaciones:**
- `rol` es enum (decisión #1). Cadete no accede a la web; solo existe para asignar entregas y contar pedidos.
- Se contempla tabla `rol` a futuro solo si aparecen roles dinámicos; hoy no.
- Relaciones: `pedidos_cadete` (como cadete), `entregas` (pedidos entregados), `movimientos_caja`, `turnos_caja`, `auditorias`, `notificaciones`.

---

### 3.2 Cliente

**tabla `cliente`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(100) | NN | |
| apellido | str(100) | | |
| telefono | str(50) | NN, UQ | **normalizado** (regla 9.3) |
| direccion | str(200) | | |
| notas | texto | | |
| creado_en | datetime | default now | |
| activo | bool | default true | soft-delete |

**Observaciones:**
- **Teléfono normalizado**: acepta variantes (`11 1234 5678`, `+54 9 11...`, `15...`) y guarda SIEMPRE uno solo. El lookup previo evita duplicados en silencio.
- `saldo_adeudado` NO es columna: se calcula por SUM sobre `movimiento_fiado`.
- "Recurrente" y "Pedidos" y "Último" son derivados (COUNT/MAX sobre `pedido`), no columnas.

---

### 3.3 Insumo y Proveedor

**tabla `proveedor`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(100) | NN | |
| rubro | str(50) | NN | ej. Carnes, Lácteos |
| telefono | str(50) | | normalizado (misma regla que cliente) |
| notas | texto | | días/condiciones |
| activo | bool | default true | soft-delete (`*act`) |

**tabla `insumo`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| proveedor_id | int | FK → `proveedor.id`, NN | |
| nombre | str(100) | NN | |
| rubro | str(50) | | |
| costo | int | NN | `(centavos)` último costo unitario |
| unidad | str(20) | NN | kg, g, l, ml, ud |
| activo | bool | default true | soft-delete (`*act`) |

**Observaciones:**
- Ambos son tablas sensibles → columnas de auditoría `usuario_id`, `fecha_hora`, `accion`.
- Unidad compatible con conversión kg↔g / l↔ml.
- El cambio de `insumo.costo` dispara recálculo de food cost en las recetas que lo usan (no se guarda duplicado).

---

### 3.4 Inventario (por lote)

**tabla `lote`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| insumo_id | int | FK → `insumo.id`, NN | |
| numero | str(50) | | nº de lote (#41) |
| cantidad | decimal(12,3) | NN, >= 0 | stock restante, en unidad del insumo |
| unidad | str(20) | NN | unidad en que se mide la cantidad |
| fecha_ingreso | datetime | NN | |
| fecha_vencimiento | datetime | NN | **no en el pasado** al cargar |
| usuario_id | int | FK → `usuario.id` | auditoría |
| fecha_hora | datetime | default now | auditoría |
| accion | str(20) | | auditoría |

**Observaciones:**
- El stock NUNCA se ve como total: se desglosa por lote. El estado (OK / Por vencer / Vencida) es **derivado** comparando `fecha_vencimiento` con hoy.
- Lote vencido = bloqueo de venta. Stock "0,0" de lote vencido queda visible y auditado.
- **No** usa soft-delete: el lote queda como historial aunque se agote o venza.
- FEFO es un flag global (`configuracion.fefo_activo`), no algo por lote.

**tabla `movimiento_inventario`** (trazabilidad de cambios de stock ajenos a una venta)

| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| insumo_id | int | FK → `insumo.id`, NN | |
| lote_id | int | FK → `lote.id` | nullable |
| conteo_id | int | FK → `conteo.id` | nullable (si nace de un conteo) |
| movimiento_caja_id | int | FK → `movimiento_caja.id` | nullable (compra a proveedor) |
| pedido_id | int | FK → `pedido.id` | nullable (consumo por venta) |
| tipo | enum | NN | `CARGA`, `AJUSTE`, `MERMA`, `SALIDA` (venta) |
| cantidad | decimal(12,3) | NN | delta aplicado (+/−) |
| motivo | str(255) | | obligatorio en ajustes con diferencia |
| usuario_id | int | FK → `usuario.id`, NN | auditoría |
| fecha_hora | datetime | default now | auditoría |

**tabla `conteo`** (línea de conteo físico, una por insumo con diferencia)

| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| insumo_id | int | FK → `insumo.id`, NN | |
| cantidad_sistema | decimal(12,3) | NN | stock teórico al momento |
| cantidad_contada | decimal(12,3) | NN | stock real tipeado |
| diferencia | decimal(12,3) | NN | sistema − contado (+ = falta) |
| motivo | str(255) | | obligatorio si `diferencia != 0` |
| usuario_id | int | FK → `usuario.id`, NN | auditoría |
| fecha_hora | datetime | default now | auditoría |

**Observaciones (Día 3):**
- El doc mencionaba `conteo` y `movimiento_inventario` en las reglas de transacción (sección 4) pero no las definía; se incorporan acá.
- Aplicar un conteo: el faltante se consume por FEFO/FIFO (`MERMA`); el sobrante se suma al lote de vencimiento más lejano o a un lote `AJUSTE` (`AJUSTE`). La cantidad de los lotes se actualiza; la diferencia queda como movimiento, nunca se sobreescribe en silencio.

---

### 3.5 Producto / Receta

**tabla `producto`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(100) | NN | |
| categoria | str(50) | | Hamburguesas, etc. |
| precio_venta | int | NN | `(centavos)` |
| margen_objetivo | int | | porcentaje objetivo (informativo) |
| activo | bool | default true | soft-delete (`*act`) |

**tabla `producto_insumo`** (unión producto ↔ insumo)
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| producto_id | int | FK → `producto.id`, NN | |
| insumo_id | int | FK → `insumo.id`, NN | |
| cantidad | decimal(12,3) | NN, > 0 | en la unidad indicada |
| unidad | str(20) | NN | g, kg, ml, l |

**Observaciones:**
- Food cost (costo total insumos) = SUM(`producto_insumo.cantidad` × `insumo.costo` con conversión de unidades). Margen = `(precio − costo) / precio`. Ambos **derivados**, no persistidos.
- Receta con insumo inactivo/inexistente o cantidades que no cierran → no se guarda (sección 9.2).
- `producto` y `producto_insumo` son sensibles (precios) → auditoría.
- Nota de arquitectura (doc 3.6): no cerrar el modelo tan rígido que sea imposible el modo simple "producto = insumo a reventa" a futuro.
- **Decisión (Día 2):** "producto simple" = `producto` con UN solo `producto_insumo` 1:1 y sin receta (caso válido), además del "producto compuesto" con varios insumos. La parte gastronómica queda contenida en Recetas; Pedidos/Caja/Inventario no distinguen entre ambos.

---

### 3.6 Pedido

**tabla `pedido`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| numero | int/str | NN | nº interno del pedido |
| origen | enum | NN, default `MOSTRADOR` | `MOSTRADOR`, `WHATSAPP`, `PEDIDOSYA`, `RAPPI`, `OTRO` |
| id_externo | str(100) | nullable | ID del pedido en la plataforma externa (idempotencia + sync de estado) |
| cliente_id | int | FK → `cliente.id` | nullable (cliente anónimo/ocasional; también en plataformas externas) |
| usuario_id | int | FK → `usuario.id`, NN | quién lo creó (auditoría) |
| metodo_pago_id | int | FK → `metodo_pago.id`, NN salvo `pago_procesado_externo=true` | requerido para cobro en caja |
| pago_procesado_externo | bool | default false | true = la plataforma ya cobró; no genera `movimiento_caja` VENTA |
| tipo_entrega | enum | NN | `RETIRO`, `DELIVERY`, `MOZO` |
| cadete_id | int | FK → `usuario.id` | nullable; solo si entrega=delivery |
| direccion | str(200) | | |
| notas | texto | | |
| estado | enum | NN, default `PENDIENTE` | `PENDIENTE`, `CONFIRMADO`, `EN_PREPARACION`, `LISTO`, `ENTREGADO`, `CANCELADO` |
| descuento | int | default 0 | `(centavos)` descuento manual |
| subtotal | int | default 0 | `(centavos)` suma de líneas |
| total | int | default 0 | `(centavos)` subtotal − descuentos |
| promocion_id | int | FK → `promocion.id` | nullable |
| turno_caja_id | int | FK → `turno_caja.id` | turno en que se vendió |
| fecha_hora | datetime | default now | |

**tabla `pedido_detalle`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| pedido_id | int | FK → `pedido.id`, NN | |
| producto_id | int | FK → `producto.id`, NN | |
| cantidad | int | NN, > 0 | |
| precio_unitario | int | NN | `(centavos)` congelado al momento de venta |
| subtotal | int | NN | `(centavos)` cantidad × precio |

**Observaciones:**
- El `subtotal` de cada línea se **congela** al confirmar (no se re-calc con precio actual), para que el histórico no cambie si después sube el precio.
- Soft-delete NO aplica a `pedido`: queda historial. "Anular" = cambio de estado a `CANCELADO` + auditoría (nunca borrado físico).
- `descuento` (manual) y `promocion` conviven; ambos quedan en `auditoria`.
- **Transacción todo-o-nada** al confirmar (ver sección 4).
- `origen` + `id_externo`: `id_externo` nullable habilita pedidos de plataformas externas (PedidosYa/Rappi/agregador) con idempotencia por `(origen, id_externo)` único cuando `id_externo` no es nulo. La capa de integraciones usa `app/integraciones/base.py` (`OrigenPedidoAdapter`) — **a futuro, no implementado hoy** (doc de producto 3.2.1).
- `pago_procesado_externo = true`: la plataforma ya cobró al cliente; **no** se crea `movimiento_caja` tipo VENTA y no impacta arqueo/cierre Z. Con `false` (default), el cobro entra por Caja como siempre.
- `cliente_id` nullable cubre el cliente anónimo/ocasional (mostrador sin datos) y los pedidos de plataformas sin cliente registrado.
- Los estados son **centralizados y desacoplados del origen** (`PENDIENTE` → `CONFIRMADO` → `EN_PREPARACION` → `LISTO` → `ENTREGADO` / `CANCELADO`): un único enum vale para mostrador, WhatsApp y plataformas externas.

**Observaciones (Día 5):**
- **Estado inicial implementado:** el alta crea el pedido directamente en `CONFIRMADO` (el botón "Confirmar pedido" descuenta stock y registra la venta). Las transiciones válidas viven en `app/models/pedido.py` (`TRANSICIONES`).
- **Consumo de stock:** `movimiento_inventario.tipo = SALIDA` con `pedido_id`; se descuenta por FEFO entre lotes **vigentes** (los vencidos no se venden y quedan para conteo/merma).
- **`promocion_id`:** la columna se agrega en el Día 6 (Promociones); hoy solo hay `descuento` manual (monto o %).
- **Anular** cambia a `CANCELADO` + auditoría; la reversión automática de stock/caja no está definida en el doc y queda pendiente.

---

### 3.7 Caja

**tabla `turno_caja`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| usuario_id | int | FK → `usuario.id`, NN | cajero que abre |
| fondo_inicial | int | NN | `(centavos)` monto variable tipeado al abrir |
| estado | enum | NN | `ABIERTO`, `CERRADO` |
| fecha_apertura | datetime | NN | |
| fecha_cierre | datetime | | null hasta cerrar |

**tabla `movimiento_caja`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| turno_caja_id | int | FK → `turno_caja.id`, NN | |
| tipo | enum | NN | `INGRESO`, `EGRESO`, `VENTA` |
| categoria | enum | | `PROVEEDOR`, `GASTO`, `RETIRO_DUENO`, `VUELTO`, `OTRO` |
| metodo_pago_id | int | FK → `metodo_pago.id` | solo para ventas |
| proveedor_id | int | FK → `proveedor.id` | nullable |
| monto | int | NN, > 0 | `(centavos)` siempre positivo; el tipo define signo |
| motivo | str(255) | NN (para no-ventas) | |
| usuario_id | int | FK → `usuario.id`, NN | auditoría |
| fecha_hora | datetime | default now | auditoría |

**tabla `arqueo`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| turno_caja_id | int | FK → `turno_caja.id`, NN, UQ | un arqueo por turno |
| efectivo_contado | int | NN, >= 0 | `(centavos)` |
| desglose | json | | conteo por billete (opcional) |
| diferencia | int | NN | `(centavos)`. Implementado como **contado − esperado** (negativo = faltante); el wireframe usa esa convención |
| motivo_diferencia | text | | obligatorio si diferencia ≠ 0 |
| diferencia_confirmada | bool | default false | check obligatorio si hay diferencia |
| usuario_id | int | FK → `usuario.id`, NN | auditoría |
| fecha_hora | datetime | default now | |

**tabla `metodo_pago`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(50) | NN | Efectivo, QR/Transferencia, Débito, Crédito, MercadoPago |
| es_efectivo | bool | default false | **agregado Día 4**: único método que impacta el arqueo |
| activo | bool | default true | soft-disable (`*act`) |

**Observaciones:**
- **Regla dura de arqueo**: si `diferencia != 0`, NO se cierra sin `motivo_diferencia` + `diferencia_confirmada = true`.
- Ventas, egresos, ingresos extra y cierre Z son **agregados** sobre `movimiento_caja`/`pedido`, nunca columnas duplicadas.
- IVA (21%) es línea **informativa** en v1; no hay columna impositiva aún.
- Los métodos de pago son configurables en Sistema (tabla, no enum) porque el dueño agrega/quita.

---

### 3.8 Promoción

**tabla `promocion`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| nombre | str(100) | NN | |
| tipo_descuento | enum | NN | `PORCENTAJE`, `MONTO_FIJO`, `DOS_POR_UNO` |
| valor | int | NN (salvo 2×1) | ver semántica abajo |
| aplicacion | enum | NN | `AUTOMATICA`, `MANUAL` |
| vigencia_desde | datetime | NN | |
| vigencia_hasta | datetime | NN | no en el pasado al crear |
| activo | bool | default true | soft-delete (`*act`) |

**tabla `promocion_producto`** (unión promoción ↔ producto)
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| promocion_id | int | FK → `promocion.id`, NN | |
| producto_id | int | FK → `producto.id`, NN | UQ conjunto (promocion_id, producto_id) |

**Semántica de `valor` según `tipo_descuento`** (importante para el cálculo):
- `PORCENTAJE` → `valor` = porcentaje en **centésimos** (consistente con la lógica de centavos de la moneda). Ej. 20% → `valor = 2000` (20.00%); 12,5% → `valor = 1250` (12.50%); 33,33% → `valor = 3333`. Sin float.
- `MONTO_FIJO` → `valor` = centavos. Ej. $1.500 → `valor = 150000`.
- `DOS_POR_UNO` → `valor = NULL` (la lógica "llevás 2 pagás 1" aplica sobre 2 ítems del producto alcanzado).

**Observaciones (Día 6):**
- El descuento se calcula solo sobre los productos alcanzados (`promocion_producto`) y se topa al subtotal de esos productos.
- Las promociones `AUTOMATICA` se resuelven solas al confirmar (se elige la de mayor descuento); las `MANUAL` las selecciona el cajero.
- Se agregó `pedido.descuento_promocion` (centavos) para persistir el descuento aplicado; el descuento manual sigue en `pedido.descuento`.

---

### 3.9 Auditoría y Notificaciones

**tabla `auditoria`** (transversal, sección 4 del doc)
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| usuario_id | int | FK → `usuario.id`, NN | |
| accion | str(100) | NN | `CREAR_PEDIDO`, `CAMBIAR_ESTADO`, `DESCUENTO`, `ABRIR_TURNO`, etc. |
| entidad | str(50) | NN | `pedido`, `movimiento_caja`, `producto`, ... |
| entidad_id | int | | id del registro afectado |
| detalles | json | | quién/cuánto/por qué |
| fecha_hora | datetime | default now | |

**tabla `notificacion`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| tipo | enum | NN | `STOCK_BAJO`, `POR_VENCER`, `BAJO_MARGEN` |
| mensaje | str(255) | NN | |
| entidad | str(50) | | `lote`, `producto` |
| entidad_id | int | | |
| leida | bool | default false | |
| descartada | bool | default false | |
| usuario_id | int | FK → `usuario.id` | nullable (notificación global) |
| fecha_hora | datetime | default now | |

**Observaciones:**
- `auditoria` es la fuente del "historial del pedido" (cada transición de estado escribe una fila), no un campo propio.
- `notificacion` se genera al detectar stock bajo / vencimiento próximo / margen bajo; el descarte es individual o global.
- **Implementado (Día 6):** generación idempotente al abrir el Dashboard (`app/services/notificacion_service.py`); umbrales: stock ≤ 1 unidad, por vencer ≤ 3 días, margen < 30%. No se vuelve a crear una notificación no descartada para la misma entidad.

---

### 3.10 Configuración

**tabla `configuracion`** (flags globales, una sola fila por instancia)
| Campo | Tipo | Default | Notas |
|---|---|---|---|
| id | int (PK) | | |
| fefo_activo | bool | true | toggle on/off (recomendado on) |
| salon_mozos_activo | bool | false | habilita tipo entrega `MOZO` |
| vista_pedidos | str(20) | `LISTA` | `LISTA` o `CUADRICULA` |
| modo_oscuro | bool | false | **no usado**: el modo oscuro se removió (la app usa el tema claro de la marca); la columna se conserva |
| font_size | str(20) | `MEDIANO` | |
| impresora_termica | str(100) | | nombre/dispositivo |

**Observaciones:**
- Togglear FEFO a OFF **no elimina lotes ni alertas**: solo cambia el orden de descuento.
- `salon_mozos_activo` habilita/oculta el tipo de entrega "mozo".

---

### 3.11 Fiado / cuenta corriente

**tabla `movimiento_fiado`**
| Campo | Tipo | Restricciones | Notas |
|---|---|---|---|
| id | int | PK | |
| cliente_id | int | FK → `cliente.id`, NN | |
| tipo | enum | NN | `DEBE` (compra fiada), `PAGA` (pago del cliente) |
| monto | int | NN, > 0 | `(centavos)` |
| pedido_id | int | FK → `pedido.id` | nullable (si nace de un pedido fiado) |
| usuario_id | int | FK → `usuario.id`, NN | auditoría |
| fecha_hora | datetime | default now | |

**Observaciones:**
- `cliente.saldo_adeudado` = SUM(`DEBE`) − SUM(`PAGA`) — **derivado**, no columna.
- No prioritario para Humos hoy; central para vender a almacenes (sección 3.3).

---

## 4. Reglas de transacción (todo-o-nada)

Las secciones que tocan varias tablas se ejecutan en una única transacción con rollback ante cualquier fallo:

1. **Confirmar pedido** → `pedido` + `pedido_detalle` + descuento de stock por FEFO (`lote`) + `movimiento_caja` (venta) + `auditoria`. Si el producto está sin stock o su lote vence hoy → bloqueo/aviso antes de confirmar.
2. **Cerrar turno (arqueo)** → `arqueo` + `turno_caja.estado = CERRADO` + `auditoria`. Si `diferencia != 0` y no hay motivo + confirmación → abortar.
3. **Conteo físico (ajuste)** → `conteo` + actualización de `lote.cantidad` + `movimiento_inventario` + ticket de merma + `auditoria`. La diferencia se registra como movimiento, nunca se sobreescribe en silencio.

---

## 5. Normalización de teléfono (regla 9.3)

- Una función única `normalize_phone()` en `services/phone_normalizer.py`.
- Acepta: `11 1234 5678`, `11-1234-5678`, `+54 9 11 1234 5678`, `+54 11 1234 5678`, `15 1234 5678`, `011 1234 5678`.
- Guarda SIEMPRE el mismo formato canónico (ej. `+5491112345678`).
- Lookup previo en Pedidos/Clientes: si el teléfono normalizado ya existe, traer el cliente existente (nunca duplicar en silencio).

---

## 6. Prioridad de implementación (orden del doc, sección 9.6)

1. Moneda como entero (centavos) — base de todo.
2. Lote validado (vencimiento no en el pasado; FEFO automático).
3. Soft-delete en Proveedores/Productos/Insumos.
4. Arqueo de caja con confirmación de diferencias.
5. Normalización de teléfono + no duplicar clientes.