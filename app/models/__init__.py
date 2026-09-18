"""Registro central de modelos.

Importar este paquete deja todos los modelos disponibles en SQLAlchemy,
necesario para que Flask-Migrate detecte el esquema.
"""

from app.models.caja import (
    Arqueo,
    CategoriaMovimientoCaja,
    EstadoTurno,
    MetodoPago,
    MovimientoCaja,
    TipoMovimientoCaja,
    TurnoCaja,
)
from app.models.cliente import Cliente
from app.models.inventario import (
    Conteo,
    Lote,
    MovimientoInventario,
    TipoMovimientoInventario,
)
from app.models.proveedor import Insumo, Proveedor
from app.models.pedido import (
    CLASES_ESTADO_PEDIDO,
    ETIQUETAS_ESTADO_PEDIDO,
    TRANSICIONES,
    EstadoPedido,
    OrigenPedido,
    Pedido,
    PedidoDetalle,
    TipoEntrega,
)
from app.models.notificacion import Notificacion, TipoNotificacion
from app.models.promocion import (
    CLASES_ESTADO_PROMO,
    ETIQUETAS_ESTADO_PROMO,
    AplicacionPromocion,
    Promocion,
    PromocionProducto,
    TipoDescuento,
)
from app.models.receta import Producto, ProductoInsumo
from app.models.sistema import Auditoria, Configuracion
from app.models.usuario import RolUsuario, Usuario

__all__ = [
    'Usuario',
    'RolUsuario',
    'Configuracion',
    'Auditoria',
    'Cliente',
    'Proveedor',
    'Insumo',
    'Producto',
    'ProductoInsumo',
    'Lote',
    'Conteo',
    'MovimientoInventario',
    'TipoMovimientoInventario',
    'MetodoPago',
    'TurnoCaja',
    'MovimientoCaja',
    'Arqueo',
    'EstadoTurno',
    'TipoMovimientoCaja',
    'CategoriaMovimientoCaja',
    'Pedido',
    'PedidoDetalle',
    'EstadoPedido',
    'OrigenPedido',
    'TipoEntrega',
    'TRANSICIONES',
    'ETIQUETAS_ESTADO_PEDIDO',
    'CLASES_ESTADO_PEDIDO',
    'Promocion',
    'PromocionProducto',
    'TipoDescuento',
    'AplicacionPromocion',
    'ETIQUETAS_ESTADO_PROMO',
    'CLASES_ESTADO_PROMO',
    'Notificacion',
    'TipoNotificacion',
]
