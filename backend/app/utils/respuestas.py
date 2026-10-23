from pydantic import BaseModel


class Mensaje(BaseModel):
    """Respuesta simple para operaciones sin datos de retorno."""

    mensaje: str


class ErrorCampo(BaseModel):
    campo: str | None
    mensaje: str


class RespuestaError(BaseModel):
    """Formato estándar de error que devuelve la API (documentado en OpenAPI)."""

    detalle: str
    codigo: str
    errores: list[ErrorCampo] | None = None
    datos: dict[str, object] | None = None
