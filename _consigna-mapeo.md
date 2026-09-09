# Consigna común — Mapeo de wireframes a modelo de datos (Humos v2)

Trabajás sobre wireframes HTML ya generados en:
`C:\Users\AMD PC\Desktop\app de gestion gastronomica\wireframes\`

Fuente de verdad de producto:
`C:\Users\AMD PC\Desktop\app de gestion gastronomica\humos-doc-producto.md`

## Tarea
De los wireframes que te tocan, extraé el mapeo **elemento en pantalla → dato → tabla/campo → acción → endpoint**, y volcalo como secciones Markdown.

## Formato EXACTO de cada mapeo (respetá esto, es lo que se va a concatenar)

Por cada pantalla:

```
### <Nombre pantalla> (<archivo.html>)

| Elemento | Dato | Tabla/Campo | Acción | Endpoint |
|---|---|---|---|---|
| <elemento UI> | <qué dato captura> | `tabla.campo` | <crear/leer/editar/borrar> | `VERBO /ruta` |
```

Después de cada tabla, una subsección corta `**Reglas / validación:**` con los bullets naranjas (`.val`) de ese wireframe traducidos a reglas de backend: NOT NULL, FK, UNIQUE, validaciones, transacciones todo-o-nada, soft-delete, etc.

## Endpoints — inventá rutas REST coherentes, convención:
- Recurso en plural, en español: `/pedidos`, `/clientes`, `/caja/turno`
- Verbo: GET (leer) / POST (crear) / PUT o PATCH (editar) / DELETE (eliminar, salvo soft-delete que es PUT con campo activo=false)
- Formato por celda: `GET /pedidos` (solo verbo+ruta; los parámetros/respuesta van en la columna "Dato" o en las reglas si son importantes)
- Endpoints de config/bandera (`activa_fefo`, toggle salón) también se listan.

## Convenciones de nombres (OBLIGATORIO — consistentes entre subagentes)
- Tablas y columnas en **español**, **singular**, **snake_case minúsculas**.
- Tablas: `usuario`, `rol`, `cliente`, `pedido`, `pedido_detalle`, `producto` (receta), `producto_insumo`, `insumo`, `proveedor`, `lote`, `movimiento_caja`, `turno_caja`, `arqueo`, `metodo_pago`, `promocion`, `promocion_producto`, `auditoria`.
- Columnas comunes de auditoría en TODA tabla sensible: `usuario_id`, `fecha_hora`, `accion` (creó/editó/eliminó). Aplican a: producto, insumo, pedido, movimiento_caja, turno_caja, promocion, precio. Marcá cuáles las llevan.
- Soft-delete = columna `activo` (boolean) en: `proveedor`, `producto`, `insumo` (y `usuario` para desactivar empleados).
- Moneda = entero en centavos (nunca float). Marcá toda columna de dinero con `(centavos, entero)`.
- Fechas de vencimiento, ingreso: columnas `fecha_vencimiento`, `fecha_ingreso` en `lote`.
- FEFO = columna de configuración (flag) en una tabla `configuracion` o similar: `fefo_activo` (bool). Mismo para `salon_mozos_activo`, `modo_oscuro`, `font_size`.
- Teléfono normalizado en `cliente.telefono` (UNIQUE), acepta variantes al cargar, guarda normalizado.

## Decisiones de modelo YA tomadas en el doc (sección 9) que DEBÉS reflejar
1. Moneda entero (centavos).
2. Inventario por lote con FEFO obligatorio (off conserva lotes y alertas, solo no fuerza orden).
3. Soft-delete en Proveedores y Productos (e Insumos).
4. FK, NOT NULL, UNIQUE (la verdad vive en el backend).
5. Teléfono normalizado + no duplicar cliente en silencio.
6. Arqueo: no cerrar turno sin confirmar diferencia.
7. Transacciones todo-o-nada al confirmar pedido (pedido + detalle + stock FEFO + caja + auditoría).
8. IVA solo informativo en v1 (columna informativa, no cálculo impositivo).

## Salida
Devolvé SOLO el contenido Markdown de tus pantallas (sin encabezado general ni título de documento; yo concateno). Empezá directo en `## <Módulo>` y listá cada pantalla como `### <Nombre> (<archivo>.html)`.

NO inventes pantallas que no existan. Si en el wireframe hay un elemento que no encaja en ninguna tabla, marcalo como "pendiente de decisión" en las reglas, no lo fuerces.