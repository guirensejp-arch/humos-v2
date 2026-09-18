# Comanda — Humos v2

**Producto:** Comanda · **Empresa:** LeudAr Labs · **Repo:** github.com/guirensejp-arch/humos-v2

Sistema de gestión gastronómica multi-negocio (white-label). **Comanda** es el producto de **LeudAr Labs**; **Humos** (smoked meats / burgers) es el delivery propio de Juan — el primer cliente/caso de prueba, no el nombre del software. Reescritura planificada de una versión anterior hecha con *vibe coding* que quedó difícil de mantener.

> **Estado:** en desarrollo. Los 6 días del plan están implementados: branding white-label, Usuarios/Login/Sistema, Clientes, Proveedores/Insumos, Recetas/Productos, Inventario por lote (FEFO y conteo), Caja (turnos/arqueo/cierre Z), Pedidos (alta transaccional), Promociones y Dashboard.

## Filosofía

Planificar antes de programar: definir pantallas → mapear a modelo de datos → arquitectura → código. Errores humanos a prueba: moneda entera en centavos, inventario por lote con FEFO, soft-delete, auditoría de toda acción sensible.

## Estructura

```
.
├── run.py                           # Arranque (create_app)
├── config.py                        # Configuración por entorno
├── requirements.txt                 # Dependencias
├── branding.yaml                    # Branding editable por cliente (Día 0)
├── seed_dev.py                      # Datos de prueba (admin + cajero)
├── app/
│   ├── __init__.py                  # Application factory
│   ├── extensions.py                # db, login_manager, migrate, csrf
│   ├── decorators.py                # Permisos por rol
│   ├── cli.py                       # Comando `flask crear-admin`
│   ├── models/                      # usuario, sistema (configuración, auditoría)
│   ├── blueprints/                  # auth, main, sistema, usuarios
│   ├── services/                    # Lógica de negocio (próximos días)
│   ├── integraciones/               # Adapters de plataformas externas (futuro)
│   ├── utils/                       # branding, auditoría
│   ├── forms/                       # Formularios Flask-WTF (CSRF)
│   ├── templates/                   # Jinja2 + Bootstrap 5 (mobile-first)
│   └── static/                      # CSS + logos de branding
├── migrations/                      # Migraciones Alembic (Flask-Migrate)
├── humos-doc-producto.md            # Documento de producto (fuente de verdad)
├── _mapeo_consolidado.md            # Mapeo wireframe → modelo (11 módulos)
├── _arquitectura_modelo_datos.md    # Arquitectura y esquema de base de datos
├── _consigna-mapeo.md               # Consigna del proceso de mapeo
├── _mapeo_*.md                      # Mapeos parciales por módulo
└── wireframes/                      # Wireframes HTML (escala de grises, responsive)
```

## Cómo correrlo (desarrollo)

```bash
# 1. Entorno virtual (Python 3.13)
py -3.13 -m venv venv
source venv/Scripts/activate        # Git Bash en Windows

# 2. Dependencias
pip install -r requirements.txt

# 3. Base de datos (migraciones) + datos de prueba
flask db upgrade
python seed_dev.py

# 4. Arrancar
python run.py                       # http://localhost:5000
```

Credenciales de prueba: `admin@comanda.com` / `password123` (ADMIN) y
`cajero@comanda.com` / `password123` (CAJERO).


## Stack decidido

- **Flask 3** (Python 3.13) + SQLAlchemy + Flask-Migrate
- **Flask-Login** (roles: Admin, Cajero, Cadete)
- **Bootstrap 5**, mobile-first (celular y notebook por igual)
- Single-tenant: una instancia por cliente (SQLite en dev, migrable a PostgreSQL)
- Moneda como **entero en centavos**, nunca float

## Módulos

Pedidos · Clientes · Proveedores · Inventario · Recetas/Productos · Promociones · Caja · Usuarios · Sistema · Dashboard

## Branding / white-label

- Logo del cliente + nombre del negocio configurable (orden intercambiable, ej. "Humos ♨️" o "🥒 Pepinillo")
- Logo de LeudAr Labs semi-transparente como marca de agua en el footer
- Todo editable vía `branding.yaml` + dos imágenes, sin tocar templates
- **Humos cargado**: paleta de la marca (`primario #1C1815`, `secundario #DB423C`, `acento #A62B23`, `fondo #F2E6D2`), logo `app/static/branding/logo_cliente.jpg` y carta real (9 productos con descripción) en el seed

## Orden de construcción (6 días)

Por dependencias técnicas, no por importancia de negocio:

0. **Sistema de branding editable por cliente** — logo + colores por archivo de config, sin tocar código
1. **Usuarios / Login / Sistema** — base de autenticación y roles
2. **Clientes, Proveedores, Recetas/Productos** — datos maestros, fija el patrón CRUD (incluye "producto simple" vs "compuesto")
3. **Inventario** — con lógica de merma/FEFO
4. **Caja** — integrada con Inventario (compra → lote automático)
5. **Pedidos** — integra Clientes, Recetas y Caja
6. **Promociones + Dashboard + pulido final**

## Roadmap

Ver `humos-doc-producto.md` (secciones 6 y 8). Los 6 días del plan de construcción están completos. Próximos pasos posibles: integraciones externas (PedidosYa/Rappi), fiado/cuenta corriente, facturación y pulido de despliegue.

## Decisiones de implementación (Día 6)

- **Promociones**: `PORCENTAJE` guarda centésimos (20% → 2000), `MONTO_FIJO` centavos y `DOS_POR_UNO` sin valor. El descuento se calcula solo sobre los productos alcanzados (`promocion_producto`).
- **Aplicación**: las automáticas se resuelven solas al confirmar (se elige la de mayor descuento); las manuales las elige el cajero en el alta. Manual + promoción conviven.
- **Descuento de promoción persistido**: se agregó `pedido.descuento_promocion` (centavos) para que el histórico no dependa de cambios futuros en la promo.
- **Notificaciones**: se generan al abrir el Dashboard de forma idempotente (`STOCK_BAJO` ≤ 1 unidad, `POR_VENCER` ≤ 3 días, `BAJO_MARGEN` < 30%); se descartan individual o globalmente.
- **Dashboard**: KPIs y rankings por período (Día/Semana/Mes/Histórico) calculados como agregados; no se persisten.
- **Pulido**: tamaño de fuente configurable desde Sistema; contador de entregas por cadete; backup manual de la base SQLite desde Sistema. (El modo oscuro se removió: la app usa el tema claro de la marca.)
- **Exportaciones a Excel**: Inventario, Cierre Z, Recetas y Proveedores exportan `.xlsx` con `openpyxl` (encabezados con estilo, montos numéricos con formato de moneda, fechas reales). Reemplaza la exportación CSV anterior.

## Historial de caja

`/caja/historial` lista los turnos **cerrados** con fondo, ventas, ingresos, egresos, total caja, pedidos y diferencia, más una fila de **totales** del rango. Atajos de período (Hoy por defecto / Semana / Mes / Todo) y filtros manuales por fecha y cajero; vista móvil en tarjetas y **Exportar Excel** (`/caja/historial/exportar.xlsx`). El turno abierto se ve en `/caja/turno`.

## Decisiones de implementación (Día 2)

- **Auditoría centralizada**: las acciones sensibles se registran en la tabla `auditoria` vía `app/utils/auditoria.py` (patrón del Día 1), en lugar de repetir columnas `usuario_id`/`fecha_hora`/`accion` en cada tabla.
- **Teléfono normalizado**: `app/services/phone_normalizer.py` guarda siempre `+549` + 10 dígitos; evita duplicados silenciosos.
- **Moneda**: los formularios aceptan `$ 8.900`, `8900` o `8900,50` y se persisten como entero en centavos (`app/utils/moneda.py`).
- **Unidades**: `app/utils/unidades.py` convierte kg↔g y l↔ml; `app/services/food_cost.py` calcula costo y margen derivados.
- **Producto simple vs compuesto**: un producto sin líneas de receta es "simple" (se revende, food cost 0); con insumos es "compuesto". Ninguno distingue en Pedidos/Inventario/Caja.
- **Permisos**: ver los módulos requiere login; crear/editar/desactivar requiere rol ADMIN.

## Decisiones de implementación (Día 3)

- **Inventario por lote**: el stock no se guarda como total, se desglosa en `lote` (ingreso + vencimiento). El estado OK / Por vencer / Vencida es derivado; el lote vencido no se borra.
- **FEFO/FIFO**: `app/services/inventario_service.py` ordena el consumo por vencimiento (FEFO, `configuracion.fefo_activo`) o por antigüedad (FIFO si FEFO está OFF).
- **Cantidades en la unidad del insumo**: al cargar un lote la cantidad se convierte a la unidad del insumo (kg↔g, l↔ml) para que las sumas sean consistentes.
- **Tablas nuevas respecto del doc**: el doc mencionaba `conteo` y `movimiento_inventario` en las reglas de transacción pero no las definía en el esquema; se agregaron. `conteo` guarda una línea por insumo con diferencia y `movimiento_inventario` la traza de cada cambio (CARGA / AJUSTE / MERMA).
- **Conteo físico**: registra solo los insumos que difieren; si hay diferencia, el motivo es obligatorio. El faltante se consume por FEFO; el sobrante se suma al lote de vencimiento más lejano (o se crea uno de ajuste). Todo en una transacción con auditoría.

## Decisiones de implementación (Día 4)

- **Turno y arqueo**: `/caja/turno` abre con fondo inicial variable; `/caja/arqueo` registra el arqueo y cierra el turno en la misma transacción. Regla dura: si la diferencia no es 0, exige motivo + confirmación explícita.
- **Signo de la diferencia**: se guarda como `contado − esperado` (negativo = faltante), siguiendo la convención visual del wireframe. En el doc de arquitectura figuraba como `esperado − contado`; se unificó a favor del wireframe.
- **Ventas por método**: `movimiento_caja` guarda ventas, ingresos y egresos; los totales del turno son agregados (no se persisten). `metodo_pago.es_efectivo` marca el único método que impacta el arqueo (columna extra respecto del doc).
- **Compra → lote automático**: `/caja/compras` registra un egreso a proveedor y, en la misma transacción, da de alta los lotes de cada insumo (FEFO/vencimiento) y actualiza `insumo.costo` con el costo unitario de la compra. `movimiento_inventario.movimiento_caja_id` enlaza lote y egreso.
- **Métodos de pago configurables**: se administran en Sistema (agregar/desactivar).
- **Pedidos pendientes**: las ventas y el KPI de pedidos quedan en 0 hasta el Día 5; los métodos de pago y el arqueo ya los contemplan.

## Decisiones de implementación (Día 5)

- **Alta transaccional**: `POST /pedidos/nuevo` crea el pedido completo en una sola operación (pedido + detalle + stock + caja + auditoría). No hay borrador persistido; las líneas se arman en el navegador.
- **Estado inicial CONFIRMADO**: el alta equivale a confirmar (descuenta stock y registra la venta). El enum y las transiciones válidas están en `models/pedido.py`.
- **Stock por FEFO**: se valida el stock vendible (lotes **no vencidos**) y se descuenta por FEFO. Un lote vencido bloquea la venta y queda para conteo/merma. Se agregó `TipoMovimientoInventario.SALIDA` y `movimiento_inventario.pedido_id`.
- **Caja**: genera un `movimiento_caja` VENTA en el turno abierto; con `pago_procesado_externo` no genera asiento (plataformas que ya cobraron).
- **Cliente**: se autocompleta por teléfono normalizado (`GET /clientes/buscar`); si no existe y hay nombre, se crea el cliente en el mismo flujo (operativo para el cajero).
- **Precio congelado**: `pedido_detalle.precio_unitario` se guarda al momento de la venta.
- **Anular**: solo cambia a CANCELADO + auditoría. La reversión de stock/caja de un pedido anulado queda pendiente (el doc no la define).
- **Promociones**: `promocion_id` se agrega en el Día 6; por ahora solo descuento manual (monto o %).