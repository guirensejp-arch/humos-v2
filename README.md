# Comanda — Humos v2

**Producto:** Comanda · **Empresa:** LeudAr Labs · **Repo:** github.com/guirensejp-arch/humos-v2

Sistema de gestión gastronómica multi-negocio (white-label). **Comanda** es el producto de **LeudAr Labs**; **Humos** (smoked meats / burgers) es el delivery propio de Juan — el primer cliente/caso de prueba, no el nombre del software. Reescritura planificada de una versión anterior hecha con *vibe coding* que quedó difícil de mantener.

> **Estado:** etapa de planificación. Wireframes y modelo de datos completos; sin código todavía.

## Filosofía

Planificar antes de programar: definir pantallas → mapear a modelo de datos → arquitectura → código. Errores humanos a prueba: moneda entera en centavos, inventario por lote con FEFO, soft-delete, auditoría de toda acción sensible.

## Estructura

```
.
├── humos-doc-producto.md            # Documento de producto (fuente de verdad)
├── _mapeo_consolidado.md            # Mapeo wireframe → modelo (11 módulos)
├── _arquitectura_modelo_datos.md    # Arquitectura y esquema de base de datos
├── _consigna-mapeo.md               # Consigna del proceso de mapeo
├── _mapeo_*.md                      # Mapeos parciales por módulo
├── branding.yaml                    # Branding editable por cliente (Día 0)
└── wireframes/                      # Wireframes HTML (escala de grises, responsive)
```

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

Ver `humos-doc-producto.md` (secciones 6 y 8). Próximo paso: implementar el modelo de datos y las capas de servicio.