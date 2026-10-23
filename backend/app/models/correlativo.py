from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Correlativo(TimestampMixin, Base):
    """Numeración de documentos internos (OC-000001, AJ-000001...).

    El siguiente número se obtiene con SELECT ... FOR UPDATE para que dos usuarios nunca reciban el mismo.
    Las series de comprobantes de venta (B001, F001...) están en series_comprobante.
    """

    __tablename__ = "correlativos"
    __table_args__ = (CheckConstraint("ultimo_numero >= 0", name="ultimo_numero_no_negativo"),)

    clave: Mapped[str] = mapped_column(String(30), primary_key=True)  # ORDEN_COMPRA, AJUSTE...
    prefijo: Mapped[str] = mapped_column(String(5))
    ultimo_numero: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    longitud: Mapped[int] = mapped_column(Integer, default=6, server_default="6")
    descripcion: Mapped[str] = mapped_column(String(100))
