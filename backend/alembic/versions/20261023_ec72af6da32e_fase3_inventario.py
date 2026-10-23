"""fase3 inventario

- Códigos de barras en una sola tabla (unicidad real entre productos y presentaciones).
- Foto del producto como archivo WEBP (columna `imagen`) y bloqueo optimista (`version`).
- Stock negativo solo por ventas autorizadas (se quita el CHECK) y `pendiente_lote`.
- Ajustes e inventarios físicos con aprobación; inventario físico y transferencias por lote.
- Operaciones idempotentes (doble clic / reintentos).
- Kardex inmutable: triggers que impiden UPDATE y DELETE en movimientos_inventario.

Revision ID: ec72af6da32e
Revises: 83a9f78491cb
Create Date: 2026-10-23 10:56:43.059338-05:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = 'ec72af6da32e'
down_revision: str | Sequence[str] | None = '83a9f78491cb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PARAMETROS_RETIRADOS = (
    "ventas.permitir_sin_stock", "inventario.ajustes_requieren_aprobacion", "inventario.metodo_salida_lotes",
)


def _crear_triggers_kardex() -> None:
    """Kardex inmutable: ni la aplicación ni un error humano en la consola pueden cambiar la historia.

    Va PRIMERO: en MySQL los cambios de estructura no se deshacen, así que si falla no queda nada a medias.
    """
    try:
        op.execute(
            "CREATE TRIGGER trg_kardex_sin_modificar BEFORE UPDATE ON movimientos_inventario FOR EACH ROW "
            "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El kardex no se puede modificar'"
        )
    except sa.exc.OperationalError as exc:
        if getattr(exc.orig, "args", (None,))[0] == 1419:
            raise RuntimeError(
                "MySQL no permite crear triggers con este usuario porque el registro binario está activo. "
                "Un administrador de MySQL debe ejecutar una vez:  SET PERSIST log_bin_trust_function_creators = 1;"
                "  (en Docker ya va en docker-compose.yml) y luego repetir la migración."
            ) from exc
        raise
    op.execute(
        "CREATE TRIGGER trg_kardex_sin_borrar BEFORE DELETE ON movimientos_inventario FOR EACH ROW "
        "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El kardex no se puede borrar'"
    )


def upgrade() -> None:
    _crear_triggers_kardex()
    op.create_table('operaciones_idempotentes',
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('clave', sa.String(length=64), nullable=False),
    sa.Column('operacion', sa.String(length=40), nullable=False),
    sa.Column('referencia_id', sa.BigInteger(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name=op.f('fk_operaciones_idempotentes_usuario_id_usuarios'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'clave', name=op.f('pk_operaciones_idempotentes'))
    )
    op.create_index(op.f('ix_operaciones_idempotentes_creado_en'), 'operaciones_idempotentes', ['creado_en'], unique=False)
    op.create_table('codigos_barras',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('producto_id', sa.Integer(), nullable=False),
    sa.Column('presentacion_id', sa.Integer(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['presentacion_id'], ['producto_presentaciones.id'], name=op.f('fk_codigos_barras_presentacion_id_producto_presentaciones'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], name=op.f('fk_codigos_barras_producto_id_productos'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_codigos_barras')),
    sa.UniqueConstraint('codigo', name=op.f('uq_codigos_barras_codigo'))
    )
    op.create_index(op.f('ix_codigos_barras_presentacion_id'), 'codigos_barras', ['presentacion_id'], unique=False)
    op.create_index(op.f('ix_codigos_barras_producto_id'), 'codigos_barras', ['producto_id'], unique=False)

    # Se copian los códigos existentes antes de borrar las columnas antiguas
    op.execute(
        "INSERT INTO codigos_barras (codigo, producto_id, presentacion_id) "
        "SELECT codigo_barras, id, NULL FROM productos WHERE codigo_barras IS NOT NULL AND codigo_barras <> ''"
    )
    op.execute(
        "INSERT IGNORE INTO codigos_barras (codigo, producto_id, presentacion_id) "
        "SELECT codigo_barras, producto_id, id FROM producto_presentaciones "
        "WHERE codigo_barras IS NOT NULL AND codigo_barras <> ''"
    )

    op.add_column('ajustes_inventario', sa.Column('motivo_rechazo', sa.String(length=300), nullable=True))
    op.add_column('ajustes_inventario', sa.Column('fecha_envio', sa.DateTime(), nullable=True))
    op.add_column('detalles_ajuste_inventario', sa.Column('numero_lote', sa.String(length=50), nullable=True))
    op.add_column('detalles_ajuste_inventario', sa.Column('fecha_vencimiento', sa.Date(), nullable=True))
    op.add_column('detalles_inventario_fisico', sa.Column('lote_id', sa.Integer(), nullable=True))
    op.add_column('detalles_inventario_fisico', sa.Column('lote_clave', sa.Integer(), sa.Computed('COALESCE(lote_id, 0)', persisted=True), nullable=False))
    op.create_index(op.f('ix_detalles_inventario_fisico_producto_id'), 'detalles_inventario_fisico', ['producto_id'], unique=False)
    op.create_unique_constraint(op.f('uq_detalles_inventario_fisico_inventario_id_producto_id_lote_clave'), 'detalles_inventario_fisico', ['inventario_id', 'producto_id', 'lote_clave'])
    op.drop_index(op.f('uq_detalles_inventario_fisico_inventario_id_producto_id'), table_name='detalles_inventario_fisico')
    op.create_foreign_key(op.f('fk_detalles_inventario_fisico_lote_id_lotes'), 'detalles_inventario_fisico', 'lotes', ['lote_id'], ['id'], ondelete='RESTRICT')
    op.add_column('detalles_transferencia', sa.Column('costo_unitario', sa.Numeric(precision=14, scale=4), server_default='0', nullable=False))
    op.add_column('detalles_transferencia', sa.Column('motivo_faltante', sa.String(length=150), nullable=True))
    op.add_column('inventarios_fisicos', sa.Column('aprobado_por_id', sa.Integer(), nullable=True))
    op.add_column('inventarios_fisicos', sa.Column('motivo_rechazo', sa.String(length=300), nullable=True))
    op.add_column('inventarios_fisicos', sa.Column('fecha_envio', sa.DateTime(), nullable=True))
    op.create_foreign_key(op.f('fk_inventarios_fisicos_aprobado_por_id_usuarios'), 'inventarios_fisicos', 'usuarios', ['aprobado_por_id'], ['id'], ondelete='RESTRICT')
    op.drop_index(op.f('uq_producto_presentaciones_codigo_barras'), table_name='producto_presentaciones')
    op.drop_column('producto_presentaciones', 'codigo_barras')
    op.add_column('productos', sa.Column('imagen', sa.String(length=60), nullable=True))
    op.add_column('productos', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
    op.drop_index(op.f('uq_productos_codigo_barras'), table_name='productos')
    # Las fotos anteriores eran URL externas: no se pueden convertir, se vuelven a subir
    op.drop_column('productos', 'imagen_url')
    op.drop_column('productos', 'codigo_barras')

    # Solo una venta autorizada puede dejar el stock negativo; el servicio de stock lo controla
    op.drop_constraint(op.f('ck_stock_almacen_cantidad_no_negativa'), 'stock_almacen', type_='check')
    op.add_column('stock_almacen', sa.Column('pendiente_lote', sa.Numeric(precision=12, scale=3), server_default='0', nullable=False))
    op.create_check_constraint(op.f('ck_stock_almacen_pendiente_lote_no_negativo'), 'stock_almacen', 'pendiente_lote >= 0')

    lista = ", ".join(f"'{c}'" for c in PARAMETROS_RETIRADOS)
    op.execute(f"DELETE FROM parametros_sistema WHERE clave IN ({lista})")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_kardex_sin_borrar")
    op.execute("DROP TRIGGER IF EXISTS trg_kardex_sin_modificar")
    op.drop_constraint(op.f('ck_stock_almacen_pendiente_lote_no_negativo'), 'stock_almacen', type_='check')
    op.drop_column('stock_almacen', 'pendiente_lote')
    op.execute("UPDATE stock_almacen SET cantidad = 0 WHERE cantidad < 0")
    op.create_check_constraint(op.f('ck_stock_almacen_cantidad_no_negativa'), 'stock_almacen', 'cantidad >= 0')
    op.add_column('productos', sa.Column('codigo_barras', mysql.VARCHAR(length=50), nullable=True))
    op.add_column('productos', sa.Column('imagen_url', mysql.VARCHAR(length=300), nullable=True))
    op.create_index(op.f('uq_productos_codigo_barras'), 'productos', ['codigo_barras'], unique=True)
    op.drop_column('productos', 'version')
    op.drop_column('productos', 'imagen')
    op.add_column('producto_presentaciones', sa.Column('codigo_barras', mysql.VARCHAR(length=50), nullable=True))
    op.create_index(op.f('uq_producto_presentaciones_codigo_barras'), 'producto_presentaciones', ['codigo_barras'], unique=True)
    op.execute(
        "UPDATE productos p JOIN (SELECT producto_id, MIN(codigo) codigo FROM codigos_barras "
        "WHERE presentacion_id IS NULL GROUP BY producto_id) c ON c.producto_id = p.id SET p.codigo_barras = c.codigo"
    )
    op.execute(
        "UPDATE producto_presentaciones pp JOIN (SELECT presentacion_id, MIN(codigo) codigo FROM codigos_barras "
        "WHERE presentacion_id IS NOT NULL GROUP BY presentacion_id) c ON c.presentacion_id = pp.id "
        "SET pp.codigo_barras = c.codigo"
    )
    op.drop_constraint(op.f('fk_inventarios_fisicos_aprobado_por_id_usuarios'), 'inventarios_fisicos', type_='foreignkey')
    op.drop_column('inventarios_fisicos', 'fecha_envio')
    op.drop_column('inventarios_fisicos', 'motivo_rechazo')
    op.drop_column('inventarios_fisicos', 'aprobado_por_id')
    op.drop_column('detalles_transferencia', 'motivo_faltante')
    op.drop_column('detalles_transferencia', 'costo_unitario')
    op.drop_constraint(op.f('fk_detalles_inventario_fisico_lote_id_lotes'), 'detalles_inventario_fisico', type_='foreignkey')
    op.create_index(op.f('uq_detalles_inventario_fisico_inventario_id_producto_id'), 'detalles_inventario_fisico', ['inventario_id', 'producto_id'], unique=True)
    op.drop_constraint(op.f('uq_detalles_inventario_fisico_inventario_id_producto_id_lote_clave'), 'detalles_inventario_fisico', type_='unique')
    op.drop_index(op.f('ix_detalles_inventario_fisico_producto_id'), table_name='detalles_inventario_fisico')
    op.drop_column('detalles_inventario_fisico', 'lote_clave')
    op.drop_column('detalles_inventario_fisico', 'lote_id')
    op.drop_column('detalles_ajuste_inventario', 'fecha_vencimiento')
    op.drop_column('detalles_ajuste_inventario', 'numero_lote')
    op.drop_column('ajustes_inventario', 'fecha_envio')
    op.drop_column('ajustes_inventario', 'motivo_rechazo')
    op.drop_table('codigos_barras')
    op.drop_table('operaciones_idempotentes')
