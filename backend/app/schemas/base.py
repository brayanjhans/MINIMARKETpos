from pydantic import BaseModel, ConfigDict


class EsquemaEntrada(BaseModel):
    """Base para datos que envía el cliente: limpia espacios y rechaza campos desconocidos."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class EsquemaSalida(BaseModel):
    """Base para respuestas: se construye desde los modelos ORM."""

    model_config = ConfigDict(from_attributes=True)
