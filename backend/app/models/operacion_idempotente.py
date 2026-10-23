from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import FechaHora


class OperacionIdempotente(Base):
    """Operaciones ya ejecutadas, por clave enviada por el cliente (cabecera Idempotency-Key).

    Si un doble clic o un reintento de red repite la petición, se devuelve el resultado de la primera
    en vez de ejecutarla dos veces. La fila se guarda en la MISMA transacción que la operación.
    """

    __tablename__ = "operaciones_idempotentes"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    clave: Mapped[str] = mapped_column(String(64), primary_key=True)
    operacion: Mapped[str] = mapped_column(String(40))
    referencia_id: Mapped[int | None] = mapped_column(BigInteger)
    creado_en: Mapped[datetime] = mapped_column(FechaHora(), server_default=func.now(), index=True)
