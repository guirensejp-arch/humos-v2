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