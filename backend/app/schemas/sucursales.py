from app.schemas.base import EsquemaSalida


class SucursalResumen(EsquemaSalida):
    id: int
    codigo: str
    nombre: str
