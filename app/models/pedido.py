import enum
from datetime import datetime

from app.extensions import db


class OrigenPedido(enum.Enum):
    MOSTRADOR = 'MOSTRADOR'
    WHATSAPP = 'WHATSAPP'
    PEDIDOSYA = 'PEDIDOSYA'
    RAPPI = 'RAPPI'
    OTRO = 'OTRO'


class TipoEntrega(enum.Enum):
    RETIRO = 'RETIRO'
    DELIVERY = 'DELIVERY'
    MOZO = 'MOZO'


class EstadoPedido(enum.Enum):
    """Estados centralizados, desacoplados del origen del pedido."""

    PENDIENTE = 'PENDIENTE'
    CONFIRMADO = 'CONFIRMADO'
    EN_PREPARACION = 'EN_PREPARACION'
    LISTO = 'LISTO'
    ENTREGADO = 'ENTREGADO'
    CANCELADO = 'CANCELADO'


# Transiciones válidas de estado (para no permitir saltos inválidos).
TRANSICIONES = {
    EstadoPedido.PENDIENTE: [EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO],
    EstadoPedido.CONFIRMADO: [EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO],
    EstadoPedido.EN_PREPARACION: [EstadoPedido.LISTO, EstadoPedido.CANCELADO],
    EstadoPedido.LISTO: [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO],
    EstadoPedido.ENTREGADO: [],
    EstadoPedido.CANCELADO: [],
}

ETIQUETAS_ESTADO_PEDIDO = {
    'PENDIENTE': 'Pendiente',
    'CONFIRMADO': 'Confirmado',
    'EN_PREPARACION': 'En preparación',
    'LISTO': 'Listo / En camino',
    'ENTREGADO': 'Entregado',
    'CANCELADO': 'Cancelado',
}

CLASES_ESTADO_PEDIDO = {
    'PENDIENTE': 'text-bg-secondary',
    'CONFIRMADO': 'text-bg-info',
    'EN_PREPARACION': 'text-bg-warning',
    'LISTO': 'text-bg-primary',
    'ENTREGADO': 'text-bg-success',
    'CANCELADO': 'text-bg-danger',
}


class Pedido(db.Model):
    """Pedido con sus líneas. No usa soft-delete: anular = estado CANCELADO."""

    __tablename__ = 'pedido'
    __table_args__ = (
        db.UniqueConstraint('origen', 'id_externo', name='uq_pedido_origen_externo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False, index=True)
    origen = db.Column(db.Enum(OrigenPedido), nullable=False, default=OrigenPedido.MOSTRADOR)
    id_externo = db.Column(db.String(100))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    metodo_pago_id = db.Column(db.Integer, db.ForeignKey('metodo_pago.id'))
    pago_procesado_externo = db.Column(db.Boolean, default=False, nullable=False)
    tipo_entrega = db.Column(db.Enum(TipoEntrega), nullable=False, default=TipoEntrega.RETIRO)
    cadete_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    direccion = db.Column(db.String(200))
    notas = db.Column(db.Text)
    estado = db.Column(db.Enum(EstadoPedido), nullable=False, default=EstadoPedido.PENDIENTE)
    descuento = db.Column(db.Integer, default=0, nullable=False)  # (centavos) descuento manual
    descuento_promocion = db.Column(db.Integer, default=0, nullable=False)  # (centavos)
    subtotal = db.Column(db.Integer, default=0, nullable=False)  # (centavos)
    total = db.Column(db.Integer, default=0, nullable=False)  # (centavos)
    promocion_id = db.Column(db.Integer, db.ForeignKey('promocion.id'))
    turno_caja_id = db.Column(db.Integer, db.ForeignKey('turno_caja.id'))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    cliente = db.relationship(
        'Cliente', backref=db.backref('pedidos', order_by='Pedido.fecha_hora.desc()')
    )
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    cadete = db.relationship(
        'Usuario', foreign_keys=[cadete_id], backref='entregas'
    )
    metodo_pago = db.relationship('MetodoPago')
    promocion = db.relationship('Promocion')
    turno = db.relationship('TurnoCaja')
    detalles = db.relationship(
        'PedidoDetalle',
        back_populates='pedido',
        cascade='all, delete-orphan',
        order_by='PedidoDetalle.id',
    )

    @property
    def cantidad_items(self):
        return sum(detalle.cantidad for detalle in self.detalles)

    def __repr__(self):
        return f'<Pedido #{self.numero} {self.estado.value} {self.total}>'


class PedidoDetalle(db.Model):
    """Línea de pedido: precio congelado al momento de la venta."""

    __tablename__ = 'pedido_detalle'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(
        db.Integer, db.ForeignKey('pedido.id'), nullable=False, index=True
    )
    producto_id = db.Column(
        db.Integer, db.ForeignKey('producto.id'), nullable=False, index=True
    )
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Integer, nullable=False)  # (centavos) congelado
    subtotal = db.Column(db.Integer, nullable=False)  # (centavos)

    pedido = db.relationship('Pedido', back_populates='detalles')
    producto = db.relationship('Producto')

    def __repr__(self):
        return f'<PedidoDetalle {self.producto_id} x{self.cantidad}>'
