from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.notificacion import Notificacion
from app.services import dashboard_service, notificacion_service

main_bp = Blueprint('main', __name__)

PERIODOS_VALIDOS = ('DIA', 'SEMANA', 'MES', 'HISTORICO')


@main_bp.route('/')
@login_required
def index():
    periodo = request.args.get('periodo', 'DIA')
    if periodo not in PERIODOS_VALIDOS:
        periodo = 'DIA'

    notificacion_service.generar(current_user.id)
    notificaciones = notificacion_service.activas()
    resumen = dashboard_service.resumen(periodo)

    return render_template(
        'main/index.html',
        periodo=periodo,
        periodos=dashboard_service.PERIODOS,
        resumen=resumen,
        notificaciones=notificaciones,
    )


@main_bp.route('/notificaciones/<int:notificacion_id>/descartar', methods=['POST'])
@login_required
def descartar_notificacion(notificacion_id):
    notificacion = db.get_or_404(Notificacion, notificacion_id)
    notificacion.descartada = True
    db.session.commit()
    flash('Notificación descartada.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/notificaciones/descartar', methods=['POST'])
@login_required
def descartar_todas():
    Notificacion.query.filter_by(descartada=False).update({'descartada': True})
    db.session.commit()
    flash('Notificaciones descartadas.', 'info')
    return redirect(url_for('main.index'))
