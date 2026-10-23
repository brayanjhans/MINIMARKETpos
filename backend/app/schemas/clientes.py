import re
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from app.models.enums import TipoDocumentoIdentidad
from app.schemas.base import EsquemaEntrada, EsquemaSalida
from app.schemas.caja import Monto

_LONGITUD = {
    TipoDocumentoIdentidad.DNI: re.compile(r"^\d{8}$"),
    TipoDocumentoIdentidad.RUC: re.compile(r"^(10|15|17|20)\d{9}$"),
    TipoDocumentoIdentidad.CARNET_EXTRANJERIA: re.compile(r"^[A-Z0-9]{6,12}$"),
    TipoDocumentoIdentidad.PASAPORTE: re.compile(r"^[A-Z0-9]{6,12}$"),
}


class ClienteCrear(EsquemaEntrada):
    tipo_documento: TipoDocumentoIdentidad = TipoDocumentoIdentidad.DNI
    numero_documento: Annotated[str | None, Field(max_length=15)] = None
    nombre: Annotated[str, Field(min_length=2, max_length=200)]
    telefono: Annotated[str | None, Field(max_length=20)] = None
    direccion: Annotated[str | None, Field(max_length=250)] = None
    permite_credito: bool = False
    limite_credito: Monto = Decimal("0")

    @model_validator(mode="after")
    def _documento(self):
        if self.tipo_documento == TipoDocumentoIdentidad.SIN_DOCUMENTO:
            self.numero_documento = None
            return self
        numero = (self.numero_documento or "").strip().upper()
        if not _LONGITUD[self.tipo_documento].match(numero):
            raise ValueError(f"El número de {self.tipo_documento.value.replace('_', ' ')} no es válido")
        self.numero_documento = numero
        return self


class ClienteSalida(EsquemaSalida):
    id: int
    tipo_documento: TipoDocumentoIdentidad
    numero_documento: str | None
    nombre: str
    telefono: str | None
    permite_credito: bool
    limite_credito: Decimal
    deuda: Decimal
    activo: bool
