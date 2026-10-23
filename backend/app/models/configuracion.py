from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Computed, ForeignKey, Integer, String, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Dinero, EnumTexto, Porcentaje, TimestampMixin
from app.models.enums import ConexionImpresora, TipoComprobante, TipoImpresora


class Empresa(TimestampMixin, Base):
    """Datos de la empresa (un solo RUC para todas las sucursales). Tabla de una sola fila (id = 1)."""

    __tablename__ = "empresa"
    __table_args__ = (
        CheckConstraint("id = 1", name="fila_unica"),
        CheckConstraint("igv_porcentaje >= 0 AND igv_porcentaje <= 100", name="igv_valido"),
        CheckConstraint("icbper_monto >= 0", name="icbper_no_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1, autoincrement=False)
    ruc: Mapped[str] = mapped_column(String(11))
    razon_social: Mapped[str] = mapped_column(String(200))
    nombre_comercial: Mapped[str | None] = mapped_column(String(200))
    direccion_fiscal: Mapped[str | None] = mapped_column(String(250))
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    logo_url: Mapped[str | None] = mapped_column(String(300))
    igv_porcentaje: Mapped[Decimal] = mapped_column(Porcentaje)
    # Monto del impuesto a las bolsas plásticas por unidad (S/ 0.50 desde 2023)
    icbper_monto: Mapped[Decimal] = mapped_column(Dinero, default=Decimal("0.50"), server_default="0.50")
    precios_incluyen_igv: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    moneda: Mapped[str] = mapped_column(String(3), default="PEN", server_default="PEN")
    simbolo_moneda: Mapped[str] = mapped_column(String(5), default="S/", server_default="S/")
    mensaje_ticket: Mapped[str | None] = mapped_column(String(300))


class SerieComprobante(TimestampMixin, Base):
    """Series de comprobantes por sucursal. El correlativo se obtiene con SELECT ... FOR UPDATE."""

    __tablename__ = "series_comprobante"
    __table_args__ = (CheckConstraint("correlativo_actual >= 0", name="correlativo_no_negativo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    tipo_comprobante: Mapped[TipoComprobante] = mapped_column(EnumTexto(TipoComprobante))
    serie: Mapped[str] = mapped_column(String(4), unique=True)  # única para todo el RUC
    correlativo_actual: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    predeterminada: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Solo una serie predeterminada por sucursal y tipo de comprobante (NULL si no es predeterminada)
    predeterminada_clave: Mapped[str | None] = mapped_column(
        String(45),
        Computed("CASE WHEN predeterminada THEN CONCAT(sucursal_id, '-', tipo_comprobante) END", persisted=True),
        unique=True,
    )


class Impresora(TimestampMixin, Base):
    """Impresora de tickets. Puede asignarse a una caja concreta o ser la predeterminada de la sucursal."""

    __tablename__ = "impresoras"

    id: Mapped[int] = mapped_column(primary_key=True)
    sucursal_id: Mapped[int] = mapped_column(ForeignKey("sucursales.id", ondelete="RESTRICT"), index=True)
    caja_id: Mapped[int | None] = mapped_column(ForeignKey("cajas.id", ondelete="SET NULL"), index=True)
    nombre: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[TipoImpresora] = mapped_column(EnumTexto(TipoImpresora))
    conexion: Mapped[ConexionImpresora] = mapped_column(EnumTexto(ConexionImpresora))
    direccion: Mapped[str | None] = mapped_column(String(150))  # IP:puerto o nombre del dispositivo
    predeterminada: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Solo una impresora predeterminada por sucursal (NULL si no lo es)
    sucursal_predeterminada_id: Mapped[int | None] = mapped_column(
        Integer, Computed("CASE WHEN predeterminada THEN sucursal_id END", persisted=True), unique=True
    )
