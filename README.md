# Humos v2

Sistema de gestión gastronómica para **Humos** (smoked meats / burgers). Reescritura planificada de una versión anterior hecha con *vibe coding* que quedó difícil de mantener. Es también la base de **LeudAr**, un producto para vender a otros negocios (kioscos, almacenes, vinotecas).

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

## Roadmap

Ver `humos-doc-producto.md` (secciones 6 y 8). Próximo paso: implementar el modelo de datos y las capas de servicio.