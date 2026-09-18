"""Formularios de la app (Flask-WTF: validación + protección CSRF)."""

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

UNIDADES_CHOICES = [
    ('kg', 'kg'),
    ('g', 'g'),
    ('l', 'l'),
    ('ml', 'ml'),
    ('ud', 'ud'),
]

CATEGORIAS_CHOICES = [
    ('', 'Sin categoría'),
    ('Hamburguesas', 'Hamburguesas'),
    ('Al plato', 'Al plato'),
    ('Sándwiches', 'Sándwiches'),
    ('Acompañamientos', 'Acompañamientos'),
    ('Bebidas', 'Bebidas'),
    ('Postres', 'Postres'),
]


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])


class CambiarPasswordForm(FlaskForm):
    password = PasswordField(
        'Nueva contraseña',
        validators=[DataRequired(), Length(min=6, message='Mínimo 6 caracteres.')],
    )
    confirmar_password = PasswordField(
        'Repetir contraseña',
        validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden.')],
    )


class UsuarioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(max=100)])
    email_personal = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    rol = SelectField(
        'Rol',
        choices=[('ADMIN', 'Admin/Dueño'), ('CAJERO', 'Cajero'), ('CADETE', 'Cadete')],
        validators=[DataRequired()],
    )
    # Obligatoria al crear; opcional al editar (vacío = no cambiar).
    password = PasswordField(
        'Contraseña',
        validators=[Optional(), Length(min=6, message='Mínimo 6 caracteres.')],
    )
    confirmar_password = PasswordField(
        'Repetir contraseña',
        validators=[Optional(), EqualTo('password', message='Las contraseñas no coinciden.')],
    )
    activo = BooleanField('Activo', default=True)


class ConfiguracionForm(FlaskForm):
    fefo_activo = BooleanField('FEFO activo (descontar primero lo que vence antes)')
    salon_mozos_activo = BooleanField('Habilitar salón / mozos')
    vista_pedidos = SelectField(
        'Vista de pedidos',
        choices=[('LISTA', 'Lista'), ('CUADRICULA', 'Cuadrícula')],
    )
    font_size = SelectField(
        'Tamaño de fuente',
        choices=[('CHICO', 'Chico'), ('MEDIANO', 'Mediano'), ('GRANDE', 'Grande')],
    )
    impresora_termica = StringField(
        'Impresora térmica',
        validators=[Optional(), Length(max=100)],
    )


# ---------------------------------------------------------------------------
# Día 2 — Clientes, Proveedores, Insumos, Recetas/Productos
# ---------------------------------------------------------------------------


class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellido = StringField('Apellido', validators=[Optional(), Length(max=100)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=50)])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=200)])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=1000)])
    activo = BooleanField('Activo', default=True)


class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    rubro = StringField('Rubro', validators=[DataRequired(), Length(max=50)])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=50)])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=1000)])
    activo = BooleanField('Activo', default=True)


class InsumoForm(FlaskForm):
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    rubro = StringField('Rubro', validators=[Optional(), Length(max=50)])
    # Se carga como texto ("$ 7.000" o "7000") y se convierte a centavos.
    costo = StringField('Último costo', validators=[DataRequired(), Length(max=30)])
    unidad = SelectField('Unidad', choices=UNIDADES_CHOICES, validators=[DataRequired()])
    activo = BooleanField('Activo', default=True)


class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción', validators=[Optional(), Length(max=255)])
    categoria = SelectField('Categoría', choices=CATEGORIAS_CHOICES)
    # Se carga como texto ("$ 8.900" o "8900") y se convierte a centavos.
    precio_venta = StringField('Precio de venta', validators=[DataRequired(), Length(max=30)])
    margen_objetivo = IntegerField(
        'Margen objetivo (%)',
        validators=[Optional(), NumberRange(min=0, max=100)],
    )
    activo = BooleanField('Activo', default=True)


class ProductoInsumoForm(FlaskForm):
    insumo_id = SelectField('Insumo', coerce=int, validators=[DataRequired()])
    # Se acepta coma decimal ("0,150") y se parsea en la ruta.
    cantidad = StringField('Cantidad', validators=[DataRequired(), Length(max=30)])
    unidad = SelectField('Unidad', choices=UNIDADES_CHOICES, validators=[DataRequired()])


class LoteForm(FlaskForm):
    insumo_id = SelectField('Insumo', coerce=int, validators=[DataRequired()])
    numero = StringField('Nº de lote', validators=[Optional(), Length(max=50)])
    # Se acepta coma decimal ("3,2") y se parsea en la ruta.
    cantidad = StringField('Cantidad', validators=[DataRequired(), Length(max=30)])
    unidad = SelectField('Unidad', choices=UNIDADES_CHOICES, validators=[DataRequired()])
    fecha_ingreso = DateField('Fecha de ingreso', validators=[Optional()])
    fecha_vencimiento = DateField(
        'Fecha de vencimiento', validators=[DataRequired()]
    )

    def validate_fecha_vencimiento(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('La fecha de vencimiento no puede ser anterior a hoy.')


# ---------------------------------------------------------------------------
# Día 4 — Caja
# ---------------------------------------------------------------------------


class AbrirTurnoForm(FlaskForm):
    # Se acepta coma decimal ("1.500,50") y se parsea en la ruta.
    fondo_inicial = StringField('Fondo inicial', validators=[DataRequired(), Length(max=30)])


class ArqueoForm(FlaskForm):
    efectivo_contado = StringField('Efectivo contado', validators=[DataRequired(), Length(max=30)])
    motivo_diferencia = TextAreaField('Motivo de la diferencia', validators=[Optional(), Length(max=1000)])
    diferencia_confirmada = BooleanField('Confirmo la diferencia y asumo la responsabilidad')


class MovimientoCajaForm(FlaskForm):
    tipo = SelectField(
        'Tipo',
        choices=[('INGRESO', 'Ingreso'), ('EGRESO', 'Egreso')],
        validators=[DataRequired()],
    )
    monto = StringField('Monto', validators=[DataRequired(), Length(max=30)])
    categoria = SelectField(
        'Categoría',
        choices=[
            ('', '—'),
            ('PROVEEDOR', 'Proveedor'),
            ('GASTO', 'Gasto'),
            ('RETIRO_DUENO', 'Retiro dueño'),
            ('VUELTO', 'Vuelto'),
            ('OTRO', 'Otro'),
        ],
        validators=[Optional()],
    )
    proveedor_id = SelectField('Vincular a proveedor', coerce=int, validators=[Optional()])
    motivo = StringField('Motivo / descripción', validators=[DataRequired(), Length(max=255)])


class MetodoPagoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    es_efectivo = BooleanField('Es efectivo (impacta el arqueo)')


class CompraForm(FlaskForm):
    proveedor_id = SelectField('Proveedor', coerce=int, validators=[DataRequired()])
    motivo = StringField('Nota', validators=[Optional(), Length(max=255)])


# ---------------------------------------------------------------------------
# Día 5 — Pedidos
# ---------------------------------------------------------------------------


class PedidoForm(FlaskForm):
    origen = SelectField(
        'Origen',
        choices=[
            ('MOSTRADOR', 'Mostrador'),
            ('WHATSAPP', 'WhatsApp'),
            ('PEDIDOSYA', 'PedidosYa'),
            ('RAPPI', 'Rappi'),
            ('OTRO', 'Otro'),
        ],
        validators=[DataRequired()],
    )
    id_externo = StringField('ID externo', validators=[Optional(), Length(max=100)])

    telefono = StringField('Teléfono', validators=[Optional(), Length(max=50)])
    cliente_id = StringField('Cliente', validators=[Optional()])
    nombre = StringField('Nombre', validators=[Optional(), Length(max=100)])
    apellido = StringField('Apellido', validators=[Optional(), Length(max=100)])

    tipo_entrega = SelectField(
        'Tipo de entrega',
        choices=[('RETIRO', 'Retiro'), ('DELIVERY', 'Delivery'), ('MOZO', 'Mozo')],
        validators=[DataRequired()],
    )
    cadete_id = SelectField('Cadete', coerce=int, validators=[Optional()])
    direccion = StringField('Dirección de entrega', validators=[Optional(), Length(max=200)])
    notas = TextAreaField('Notas del cliente', validators=[Optional(), Length(max=1000)])

    metodo_pago_id = SelectField('Método de pago', coerce=int, validators=[Optional()])
    pago_procesado_externo = BooleanField('El pago ya lo procesó la plataforma')

    descuento = StringField('Descuento manual', validators=[Optional(), Length(max=30)])
    promocion_id = SelectField('Promoción', coerce=int, validators=[Optional()])


class CambiarEstadoPedidoForm(FlaskForm):
    estado = SelectField('Estado', validators=[DataRequired()])


# ---------------------------------------------------------------------------
# Día 6 — Promociones
# ---------------------------------------------------------------------------


class PromocionForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    tipo_descuento = SelectField(
        'Tipo de descuento',
        choices=[
            ('PORCENTAJE', 'Porcentaje (%)'),
            ('MONTO_FIJO', 'Monto fijo ($)'),
            ('DOS_POR_UNO', '2×1'),
        ],
        validators=[DataRequired()],
    )
    valor = StringField('Valor', validators=[Optional(), Length(max=30)])
    aplicacion = SelectField(
        'Aplicación',
        choices=[('AUTOMATICA', 'Automática'), ('MANUAL', 'Manual')],
        validators=[DataRequired()],
    )
    vigencia_desde = DateField('Vigente desde', validators=[DataRequired()])
    vigencia_hasta = DateField('Vigente hasta', validators=[DataRequired()])
    productos = SelectMultipleField('Productos alcanzados', coerce=int, validators=[Optional()])
    activo = BooleanField('Activa', default=True)

    def validate_vigencia_hasta(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('La vigencia no puede terminar en el pasado.')
        if field.data and self.vigencia_desde.data and field.data < self.vigencia_desde.data:
            raise ValidationError('La vigencia de fin no puede ser anterior al inicio.')
