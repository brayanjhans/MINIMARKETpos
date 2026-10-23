from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CERO, Cantidad, CostoUnitario, Dinero, EnumTexto, FechaHora, TimestampMixin
from app.models.enums import TipoAfectacionIGV, UnidadMedida

if TYPE_CHECKING:
    from app.models.categoria import Categoria
    from app.models.lote import Lote
    from app.models.marca import Marca


class Producto(TimestampMixin, Base):
    """Catálogo de productos. El stock NO vive aquí sino en stock_almacen (por almacén/sucursal)."""

    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("stock_minimo >= 0", name="stock_minimo_no_negativo"),
        CheckConstraint("precio_costo >= 0", name="precio_costo_no_negativo"),
        CheckConstraint("precio_venta >= 0", name="precio_venta_no_negativo"),
        # Búsqueda instantánea por fragmentos del nombre (MATCH ... AGAINST)
        Index("ftx_productos_nombre", "nombre", mysql_prefix="FULLTEXT", mysql_with_parser="ngram"),
        Index("ix_productos_categoria_activo", "categoria_id", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_interno: Mapped[str | None] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id", ondelete="SET NULL"))
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marcas.id", ondelete="SET NULL"), index=True)
    unidad_medida: Mapped[UnidadMedida] = mapped_column(
        EnumTexto(UnidadMedida), default=UnidadMedida.UNIDAD, server_default=UnidadMedida.UNIDAD.value
    )
    # Costo promedio ponderado de la unidad base (solo cambia con entradas: compras y stock inicial)
    precio_costo: Mapped[Decimal] = mapped_column(CostoUnitario, default=CERO, server_default="0")
    # Precio de venta de la unidad base (incluye IGV si la empresa trabaja con precios con IGV)
    precio_venta: Mapped[Decimal] = mapped_column(Dinero, default=CERO, server_default="0")
    # Stock mínimo general; cada almacén puede sobrescribirlo en stock_almacen
    stock_minimo: Mapped[Decimal] = mapped_column(Cantidad, default=CERO, server_default="0")
    tipo_afectacion_igv: Mapped[TipoAfectacionIGV] = mapped_column(
        EnumTexto(TipoAfectacionIGV),
        default=TipoAfectacionIGV.GRAVADO,
        server_default=TipoAfectacionIGV.GRAVADO.value,
    )
    # Impuesto a las bolsas plásticas (se cobra por unidad vendida)
    afecto_icbper: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    maneja_lotes: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    permite_decimales: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Nombre del archivo WEBP de la foto (sin extensión); la miniatura lleva el sufijo "_m"
    imagen: Mapped[str | None] = mapped_column(String(60))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Bloqueo optimista: sube con cada edición manual; si dos personas editan a la vez, la segunda recibe un aviso
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    categoria: Mapped[Categoria | None] = relationship(back_populates="productos", lazy="joined")
    marca: Mapped[Marca | None] = relationship(lazy="joined")
    lotes: Mapped[list[Lote]] = relationship(back_populates="producto")
    presentaciones: Mapped[list[ProductoPresentacion]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="ProductoPresentacion.factor"
    )
    codigos: Mapped[list[CodigoBarras]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", order_by="CodigoBarras.id"
    )


class ProductoPresentacion(TimestampMixin, Base):
    """Presentaciones de venta con su propio código y precio (six-pack, caja x24, etc.).

    Al vender, se descuenta del stock: cantidad x factor (en unidades base).
    """

    __tablename__ = "producto_presentaciones"
    __table_args__ = (
        UniqueConstraint("producto_id", "nombre"),
        CheckConstraint("factor > 0", name="factor_positivo"),
        CheckConstraint("precio_venta >= 0", name="precio_venta_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(80))  # ej. "Six pack", "Caja x24"
    factor: Mapped[Decimal] = mapped_column(Cantidad)  # unidades base que contiene
    precio_venta: Mapped[Decimal] = mapped_column(Dinero)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    producto: Mapped[Producto] = relationship(back_populates="presentaciones")
    codigos: Mapped[list[CodigoBarras]] = relationship(back_populates="presentacion")


class CodigoBarras(Base):
    """Todos los códigos de barras del sistema en UNA tabla: la base de datos garantiza que no se repitan,
    sean de la unidad base (presentacion_id NULL) o de una presentación. Un producto puede tener varios."""

    __tablename__ = "codigos_barras"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True)
    presentacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("producto_presentaciones.id", ondelete="CASCADE"), index=True
    )
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now())

    producto: Mapped[Producto] = relationship(back_populates="codigos")
    presentacion: Mapped[ProductoPresentacion | None] = relationship(back_populates="codigos")
