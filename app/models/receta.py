from app.extensions import db


class Producto(db.Model):
    """Producto vendible: puede ser simple (sin receta) o compuesto (con insumos).

    - Simple: se revende tal cual (ej. bebida); sin líneas de receta, food cost 0.
    - Compuesto: receta con uno o más insumos (`producto_insumo`).
    Pedidos/Inventario/Caja no distinguen entre ambos.
    """

    __tablename__ = 'producto'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Integer, nullable=False)  # (centavos)
    margen_objetivo = db.Column(db.Integer)  # porcentaje informativo
    activo = db.Column(db.Boolean, default=True, nullable=False)  # soft-delete

    insumos = db.relationship(
        'ProductoInsumo',
        back_populates='producto',
        cascade='all, delete-orphan',
        order_by='ProductoInsumo.id',
    )

    def __repr__(self):
        return f'<Producto {self.nombre} ({self.precio_venta} centavos)>'


class ProductoInsumo(db.Model):
    """Línea de receta: unión producto ↔ insumo con cantidad y unidad."""

    __tablename__ = 'producto_insumo'
    __table_args__ = (
        db.UniqueConstraint('producto_id', 'insumo_id', name='uq_producto_insumo'),
    )

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(
        db.Integer, db.ForeignKey('producto.id'), nullable=False, index=True
    )
    insumo_id = db.Column(
        db.Integer, db.ForeignKey('insumo.id'), nullable=False, index=True
    )
    cantidad = db.Column(db.Numeric(12, 3), nullable=False)
    unidad = db.Column(db.String(20), nullable=False)  # g, kg, ml, l

    producto = db.relationship('Producto', back_populates='insumos')
    insumo = db.relationship('Insumo', back_populates='lineas')

    def __repr__(self):
        return f'<ProductoInsumo {self.producto_id}-{self.insumo_id} {self.cantidad}{self.unidad}>'
