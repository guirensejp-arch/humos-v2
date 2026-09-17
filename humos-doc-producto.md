# Sistema Humos v2 — Documento de Producto

*Última actualización: 23/08/2026 — Documento vivo, se actualiza a medida que avanza el proyecto.*

## 0. Contexto y objetivo

Reescritura completa del sistema de gestión de Humos (negocio de smoked meats/burgers), partiendo de una versión anterior hecha con vibe coding que quedó difícil de mantener. El objetivo de esta v2 es planificar antes de programar: definir pantallas, modelo de datos y arquitectura a partir de wireframes, en vez de ir agregando funciones sobre la marcha.

**Visión a mediano plazo:** este sistema también es la base de **LeudAr**, un producto para vender a otros negocios gastronómicos y comercios chicos (kioscos, almacenes, vinotecas). Cada decisión de este documento marca cuándo conviene diseñar pensando en eso y cuándo es mejor no complicarse todavía.

**Nombre del producto:** **Comanda** (LeudAr Labs). "Humos" es el delivery propio de Juan — el primer cliente/caso de prueba del sistema, no el nombre del software.

---

## 1. Stack y decisiones de arquitectura ya tomadas

| Decisión | Definición |
|---|---|
| Backend | Flask (Python) |
| Modelo de despliegue | **Single-tenant**: una instancia propia por cliente/negocio, no una base compartida multi-empresa. Se revisa si el negocio escala mucho (tipo Fudo). |
| Autenticación | Login por navegador, usuario y contraseña elegidos por cada usuario. Recomendado: Flask-Login + hash de contraseñas (nunca texto plano). |
| Roles (versión inicial) | **Admin/Dueño** y **Cajero**. Cadetes viven dentro de Usuarios, no como pantalla separada. |
| Hosting | Sin definir todavía (no bloquea el desarrollo). |

---

## 2. Lista de pantallas (definitiva por ahora)

1. Inicio (Dashboard)
2. Pedidos
3. Clientes
4. Proveedores
5. Inventario
6. Recetas/Productos
7. Promociones
8. Caja
9. Usuarios (incluye roles y Cadetes)
10. Sistema (configuración)

---

## 3. Detalle por módulo

### 3.1 Inicio (Dashboard)
- KPIs: producto más vendido y **menos vendido**, discriminados por **día / semana / mes / histórico**
- Producto con mayor margen
- Ticket promedio
- Ventana de notificaciones (stock bajo, bajo margen, productos por vencer), con opción de descartarlas
- Acceso rápido para armar una promoción

**Por qué "producto menos vendido" importa, no solo el más vendido:** ayuda a decidir qué sacar de la carta o qué necesita una promo para no quedar como stock muerto — es la misma lógica de "detectar productos que no se venden" que aplican sistemas POS comerciales como referencia de mercado.

### 3.2 Pedidos
El módulo más importante. Vista en lista y en cuadrícula. Al crear un pedido: producto, método de pago, datos del cliente (autocompletados desde el módulo Clientes), notas, cadete asignado, y tipo de entrega (retiro en local / delivery / mozo si el negocio tiene salón — configurable on/off en Sistema, pensado para poder vender el sistema a locales sin salón).

**Descuento manual además de promociones:** en el pedido se puede aplicar un descuento manual (monto fijo o porcentaje) además de una promoción. Ambos conviven y se aplican en orden; todo descuento queda registrado en auditoría (quién lo hizo y cuánto), para que no sea una vía de fuga de plata sin control.

**Estados del pedido:** Pendiente → En preparación → En camino → Entregado (más Anulado). Los cambios de estado quedan registrados con quién y cuándo (auditoría).

### 3.3 Clientes *(módulo agregado)*
Se autocompleta desde Pedidos: si el teléfono ya existe, trae los datos; si no, se crea. Permite ver historial de pedidos por cliente y detectar clientes recurrentes. Campo opcional de **cuenta corriente / fiado** (saldo adeudado + historial de pagos) — no prioritario para Humos hoy, pero central si el sistema se vende a un almacén.

### 3.4 Proveedores
Alta/baja (soft-delete) de proveedores e insumos, organizados por rubro y proveedor. Generación de tickets automáticos para carga de insumos, merma, desperdicio o consumo de personal.

### 3.5 Inventario
Estado y cantidad de materia prima, descartables y artículos de limpieza. Control físico de stock (conteo manual que reconcilia contra el sistema). Interactúa con Proveedores y Caja.

**Cambio de modelo importante: manejo por lote.** Para que el dashboard pueda avisar "producto por vencer", el inventario no puede guardar solo "cantidad total de X insumo" — necesita registrar **lotes**: mismo insumo, distintas fechas de ingreso y vencimiento. Esta es una práctica estándar en gestión de inventario de alimentos: permite alertas automáticas de vencimiento próximo, aplicar lógica **FEFO** (First Expired, First Out — usar primero lo que vence antes) para reducir desperdicio, y saber exactamente qué lote se agotó o venció, en vez de manejar todo como un número único. Es un cambio que conviene definir ahora, en el modelo de datos, antes de escribir código — cambiarlo después implica tocar todo lo que ya dependa de Inventario.

**FEFO configurable on/off (igual que la opción de salón/mozos):** la lógica FEFO debe poder activarse/desactivarse desde Sistema, como una *configuración del comportamiento de inventario*, no como un módulo separado. Conviene definir el flag de configuración en el modelo desde el día uno para que el cambio sea coherente con el stock ya cargado.

| Modo | Qué hace |
|---|---|
| **FEFO on** (recomendado por defecto) | Al vender/consumir, descuenta automáticamente del lote que vence antes. Alerta de vencimiento. |
| **FEFO off** | Conserva los lotes y las alertas de vencimiento, pero no fuerza el orden de consumo — el stock se descuenta de forma manual (o "primero en entrar"). |

No se recomienda un "off" que elimine los lotes por completo: se perdería la alerta de vencimiento, que es uno de los mayores valores del sistema.

### 3.6 Recetas/Productos
Arma cada producto con la materia prima cargada en Proveedores. Calcula el margen de ganancia (food cost) cruzando con Caja/Inventario.

**Nota de arquitectura para el futuro (no programar ahora):** Humos necesita "producto = receta con insumos". Un kiosco o almacén (si algún día se vende esa versión) necesita simplemente "producto = insumo a reventa, sin receta". No hace falta programar el modo simple ahora — alcanza con no cerrar el modelo de Recetas de una forma tan rígida que después sea imposible simplificarlo.

**Decisión de diseño (Día 2):** tratar **"producto simple"** (1:1 con su insumo, sin receta) como caso válido además del **"producto compuesto"** (receta con varios insumos). Esto generaliza Pedidos/Caja/Inventario más allá de gastronomía (ej. una verdulería) sin tocar el resto del sistema — la parte específica de gastronomía queda contenida en Recetas, no en Pedidos.

### 3.7 Promociones *(elevado a módulo propio)*
Se arman con fecha de vigencia, se aplican en Pedidos (automático o manual), e impactan el cálculo de margen en Caja/Recetas. El acceso rápido para crear una sigue estando en el Dashboard.

### 3.8 Caja
Apertura/cierre de turno, arqueo, cierre Z, ingresos/egresos (interactúa con Proveedores), ventas del día discriminadas por método de pago, historial por fecha.

**Fondo inicial variable:** el cajero tipea el monto de fondo al abrir el turno (no es fijo).

**Categorías de ingreso/egreso:** Proveedor, Gasto, Retiro del dueño, Vuelto, Otro. Todo movimiento externo a una venta queda en auditoría (usuario, hora, motivo).

**Cierre Z (ticket térmico 80mm):** total ventas, descuentos (cantidad y monto), IVA, ingresos extra, egresos, total de caja y diferencia de arqueo. La versión extendida se exporta como CSV/PDF.

**IVA informativo (21%):** en la v1 el IVA es solo una línea informativa en el cierre Z, no un cálculo impositivo real. La mayoría de los negocios objetivo (bares, deliverys, comercios chicos) no están registrados para tributar, así que no es crítico hoy. Pero el modelo de precios/productos debe quedar abierto para sumar alícuotas reales a futuro, sin que sea un cambio destructivo (mismo criterio que la facturación electrónica del roadmap).

### 3.9 Usuarios *(módulo agregado, incluye Cadetes)*
- Alta/baja de empleados con rol **Admin** o **Cajero**
- Cadetes viven acá: alta/baja, y desglose de cuántos pedidos entregó cada uno (útil si cobran por entrega)
- Recuperación de contraseña: al menos de forma manual — el Admin resetea la del Cajero desde esta pantalla, sin necesidad de mail automático en la v1

### 3.10 Sistema
Cerrar sesión, tamaño de fuente, configuración de impresora térmica, fecha/hora (idealmente automática por internet), modo oscuro/claro, on/off de la opción "mozo" según si el local tiene salón.

---

## 4. Trazabilidad / auditoría

**Qué es:** un registro de quién hizo qué acción del sistema y cuándo, para poder reconstruir la historia si algo no cierra.

**Cómo se implementa:** no es una pantalla nueva en el menú. Cada tabla sensible (Producto, Pedido, MovimientoCaja, precios, etc.) suma tres campos: `usuario_id` (quién), `fecha_hora` (cuándo) y `acción` (creó/editó/eliminó).

**Ejemplos de uso real:**
- Quién eliminó un producto del inventario
- Quién cargó un egreso de caja sin factura clara
- Quién abrió/cerró un turno que no cuadró en el arqueo
- Historial de cambios de precio de un producto

**Por qué importa (no es solo paranoia):** en sistemas de punto de venta, un registro de auditoría es lo que permite detectar errores o uso indebido antes de que se conviertan en pérdidas grandes — es la misma lógica que usan comercios minoristas para revisar logs de transacciones y detectar irregularidades a tiempo, y es un argumento de venta directo si el sistema se ofrece a terceros: el dueño puede confiar en que cada movimiento de sus empleados queda identificado, sin depender de la memoria de nadie.

**Exportable/imprimible:** se suma a la lista general de reportes — versión acotada (ej. movimientos de un turno puntual) tiene sentido como ticket térmico junto al cierre Z; la versión completa/extensa, mejor como CSV o PDF.

---

## 5. Funcionalidades transversales

**Exportación CSV:** un componente único reutilizable (tabla → CSV), invocado desde cada pantalla, en vez de programar la exportación módulo por módulo.

**Impresión térmica (80mm):**
- *Sí, formato ticket:* comprobante de pedido, cierre Z, arqueo, tickets de carga/merma, historial de auditoría acotado
- *No, mejor PDF/CSV:* listado completo de inventario, listado de proveedores, historial de pedidos extenso, historial de auditoría completo

**Unidades de medida y conversión:** Inventario/Recetas necesitan convertir automáticamente entre unidades (kg↔g, l↔ml) para que el cálculo de food cost sea correcto.

**Backup de la base de datos:** automático, o al menos un botón manual en Sistema para exportar toda la base.

**Responsive / mobile-first (requisito de base):** el sistema se usa desde el mostrador, en la práctica desde celulares y tablets — no siempre en una PC de escritorio. Por eso toda la UI debe ser responsive desde el inicio (no es un retoque final). En la práctica se resuelve con Bootstrap, como ya se usa en otros proyectos del autor. Implicancias concretas:
- **Mobile-first** en las pantallas de uso intenso y rápido del cajero (Pedidos y Caja).
- **Botones y controles táctiles generosos**: un botón cómodo de escritorio no se toca bien con el dedo apurado.
- **Entradas numéricas** (cantidades, pesos) fáciles de tipear en teclado móvil, sin menús complejos.
- Impresión térmica y exportación CSV no dependen del tamaño de pantalla, así que no se ven afectadas.

**Branding / white-label (Día 0):**
- Logo del cliente + nombre del negocio configurable (orden intercambiable, ej. "Humos ♨️" o "🥒 Pepinillo")
- Logo de LeudAr Labs semi-transparente como marca de agua en el footer
- Todo editable vía archivo de config (`branding.yaml` + dos imágenes), sin tocar templates

---

## 6. Roadmap futuro (anotado, no se diseña todavía)

- **Facturación electrónica (ARCA/AFIP):** no se necesita hoy, pero probable pedido si se vende a otros negocios gastronómicos en Argentina
- **Integración con apps de delivery** (PedidosYa, Rappi): hoy el reparto es propio (cadete)
- **IA que compara precios contra el mercado y sugiere ajustes:** requiere una base de datos de precios de otros comercios que hoy no existe — alta complejidad para el valor actual
- **Carga de stock por foto de factura (OCR/visión):** atractivo, pero es un desarrollo aparte, para cuando el sistema base esté estable
- **Versión multi-rubro** (kioscos, almacenes, vinotecas): catálogo online y soporte para balanzas aplicarían recién ahí, no a Humos

---

## 7. Modelo de precios para LeudAr (referencia de mercado y cálculo propio)

**Contexto de mercado (Argentina, 2026):** Fudo, el sistema más grande del rubro, cobra entre USD 39 y USD 130/mes por sucursal según plan, más módulos adicionales por separado. Cobrando.app (orientado a kioscos/almacenes) plantea planes desde ~$12.000 ARS/mes con todo incluido, sin costo de setup. Ambos apuntan a un segmento con más presupuesto o más volumen que el target inicial de Humos/LeudAr (negocios chicos, sin salón).

**Esquema propio calculado:**
- Costo real estimado por hora de trabajo (10-12hs de implementación × USD 7/hora): USD 70-84
- **Precio de lanzamiento decidido:** USD 45-50 de setup + USD 20/mes — por debajo del costo real de las horas de implementación, como estrategia de entrada para los primeros clientes (baja la barrera de decisión, dado que aún no hay casos de referencia para mostrar)
- Revisar al alza una vez que haya 2-3 clientes reales y casos de uso comprobados para mostrar

---

## 8. Próximos pasos

1. Wireframes de cada pantalla (empezando por **Pedidos**, la más compleja)
2. De cada wireframe, sacar la tabla de datos necesarios + endpoints (método ya acordado: "elemento en pantalla → dato → tabla/campo → acción → endpoint")
3. Con todas las pantallas mapeadas, recién ahí se arma la arquitectura y el modelo de datos completo
4. Subir a un repo en GitHub
5. Devin Pro y/o Google Jules (Free) construyen sobre esa base ya planificada

**Orden de construcción (6 días)** — por dependencias técnicas, no por importancia de negocio:

0. **Sistema de branding editable por cliente** — logo + colores por archivo de config, sin tocar código
1. **Usuarios / Login / Sistema** — base de autenticación y roles
2. **Clientes, Proveedores, Recetas/Productos** — datos maestros, fija el patrón CRUD. Incluye la decisión de "producto simple" (1:1 sin receta) como caso válido además del "compuesto" (receta con varios insumos)
3. **Inventario** — con lógica de merma/FEFO
4. **Caja** — integrada con Inventario (compra → lote automático)
5. **Pedidos** — integra Clientes, Recetas y Caja
6. **Promociones + Dashboard + pulido final**

Plan detallado con los prompts exactos de cada día (artifact): https://claude.ai/artifact/4cH8aor5VP9nH8wmoqn1Cd

---

## 9. Robustez y validación de carga (a prueba de errores humanos)

**Objetivo:** el sistema lo usa gente apurada y bajo presión (cajeros, cocina). Un error de tipeo no puede romper datos ni quedar oculto. Esta sección define reglas de validación y decisiones de modelo para que la carga sea segura. Es complemento de las decisiones de Trazabilidad (sección 4): acá se define *qué se impide*, allá *qué se registra*.

### 9.1 Decisiones de modelo irrenunciables (definir desde el día uno)

| Regla | Por qué importa |
|---|---|
| **Moneda como entero (centavos), nunca float** | Los floats redondean mal la plata. Corregirlo después de tener caja/márgenes andando es caro y propenso a bugs. Se define al principio o se reescribe. |
| **Inventario por lote con FEFO obligatorio** | Ya decidido (sección 3.5). Reforzar acá: sin lote no hay alerta de vencimiento confiable. Cambiarlo después implica tocar Recetas, Pedidos y Caja. |
| **Soft-delete en Proveedores y Productos** | "Borrar" no puede romper pedidos históricos que referencian ese item. El registro se marca inactivo, no se elimina. |
| **Restricciones de integridad en la base (FK, NOT NULL, UNIQUE)** | La verdad vive en el backend, no en la pantalla. Una FK impide un pedido sin cliente aunque el front falle. |

### 9.2 Validación por pantalla

**Pedidos**
- Bloquear si un producto tiene stock insuficiente o lote vencido (advertir antes de confirmar).
- Método de pago obligatorio y monto consistente con el total.
- Teléfono normalizado (ver 9.3).
- Cadete asignado debe existir y estar activo.
- Límite de longitud en notas.

**Clientes**
- Nunca duplicar en silencio: si el teléfono ya existe, traer el cliente existente (refuerza el autocompletado de la sección 3.3).
- Teléfono y email con formato validado.

**Proveedores / Inventario**
- Cantidades no negativas y numéricas.
- Unidades compatibles (no cargar "kg" donde va "litros") — conecta con la conversión de la sección 5.
- Al cargar un lote, fecha de vencimiento obligatoria y no en el pasado.

**Caja**
- Arqueo que no cuadra: no permitir cerrar turno sin confirmar explícitamente la diferencia.
- Egreso sin monto o sin motivo: bloquear.
- Aceptar formato decimal argentino (coma) sin ambigüedad.

**Recetas**
- Receta cuyas cantidades no cierran o con insumo inactivo/inexistente: advertir o bloquear.

### 9.3 Normalización de teléfono (el dato que más se tipea mal)

Definir UNA regla al cargar (aceptar variantes `11 1234 5678`, `+54...`, `15...`) y guardar SIEMPRE normalizado. Es la clave para que el autocompletado de Clientes y la detección de recurrentes funcionen.

### 9.4 Red de seguridad en pantalla

- **Confirmar** antes de acciones irreversibles (cerrar caja, anular pedido, borrar insumo).
- **Deshacer** la última carga cuando sea barato de implementar.
- **Advertencias contextuales en el momento de cargar** (stock bajo, vencimiento próximo), no después.

### 9.5 Corolario técnico

- **Backup automático** (ya pedido en Sistema, sección 5): con eso, ningún error humano es fatal.
- **Validación idéntica en front y back**, pero la autoridad es el backend: nunca confiar solo en la pantalla.
- **Transacciones**: cargar un pedido toca varias tablas (pedido + detalle + stock + caja + auditoría). Debe ser todo-o-nada; si falla a mitad, no puede quedar a medias.

### 9.6 Orden de prioridad para implementar

1. Moneda como entero (base de Caja y margen).
2. Lote bien validado (vencimiento en el pasado = bloquear; FEFO automático).
3. Soft-delete en Proveedores/Productos.
4. Arqueo de caja con confirmación de diferencias.
5. Normalización de teléfono + evitar duplicados.

---

## Fuentes consultadas para este documento

- Fudo — planes y precios (Madi Rest, comparativa de mercado, 2026)
- Cobrando.app — cobrando.app/#pricing (planes, funcionalidades de referencia)
- Fishbowl Inventory — beneficios de gestión de inventario para restaurantes, lot/batch tracking y alertas de vencimiento
- NetSuite — guía de lot tracking y trazabilidad FEFO
- eloERP — guía de batch & expiry tracking en inventario (2026)
- Washburn POS / LLMerchantServices — importancia de auditoría en sistemas de punto de venta para detectar irregularidades y dar trazabilidad interna
