from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.models.enums import EstadoSesionCaja, MetodoPago, TipoMovimientoCaja
from app.schemas.base import EsquemaEntrada, EsquemaSalida

Monto = Annotated[Decimal, Field(ge=0, le=Decimal("999999.99"), max_digits=12, decimal_places=2)]
MontoPositivo = Annotated[Decimal, Field(gt=0, le=Decimal("999999.99"), max_digits=12, decimal_places=2)]
Texto = Annotated[str | None, Field(max_length=300)]


class CajaSalida(EsquemaSalida):
    id: int
    nombre: str
    descripcion: str | None
    # Turno abierto en esta caja (si hay)
    sesion_id: int | None
    abierta_por: str | None
    abierta_desde: datetime | None
    es_mia: bool


class AperturaEntrada(EsquemaEntrada):
    caja_id: int
    monto_inicial: Monto
    observaciones: Texto = None


class MovimientoCajaEntrada(EsquemaEntrada):
    tipo: TipoMovimientoCaja
    monto: MontoPositivo
    concepto: Annotated[str, Field(min_length=3, max_length=200)]


class ConteoDenominacion(EsquemaEntrada):
    denominacion: Annotated[Decimal, Field(gt=0, le=1000, max_digits=7, decimal_places=2)]
    cantidad: Annotated[int, Field(ge=0, le=100000)]


class DeclaradoMetodo(EsquemaEntrada):
    metodo: MetodoPago
    monto: Monto

    @field_validator("metodo")
    @classmethod
    def _no_efectivo(cls, v: MetodoPago) -> MetodoPago:
        if v in (MetodoPago.EFECTIVO, MetodoPago.CREDITO):
            raise ValueError("El efectivo se cuenta por billetes y monedas; el fiado no se declara")
        return v


class CierreEntrada(EsquemaEntrada):
    """Cierre ciego: el cajero cuenta billetes y monedas y declara los vouchers/apps sin ver lo esperado."""

    arqueo: Annotated[list[ConteoDenominacion], Field(max_length=30)]
    declarados: Annotated[list[DeclaradoMetodo], Field(max_length=6)] = []
    observaciones: Texto = None

    @field_validator("arqueo")
    @classmethod
    def _sin_repetidos(cls, v: list[ConteoDenominacion]) -> list[ConteoDenominacion]:
        if len({c.denominacion for c in v}) != len(v):
            raise ValueError("Hay billetes o monedas repetidos en el arqueo")
        return v

    @field_validator("declarados")
    @classmethod
    def _metodos_unicos(cls, v: list[DeclaradoMetodo]) -> list[DeclaradoMetodo]:
        if len({d.metodo for d in v}) != len(v):
            raise ValueError("Hay métodos de pago repetidos")
        return v


class MovimientoCajaSalida(EsquemaSalida):
    id: int
    tipo: TipoMovimientoCaja
    monto: Decimal
    concepto: str
    usuario: str
    creado_en: datetime


class ResumenMetodo(EsquemaSalida):
    metodo: MetodoPago
    operaciones: int
    monto_sistema: Decimal | None  # oculto al cajero mientras la caja está abierta (cierre ciego)
    monto_declarado: Decimal | None
    diferencia: Decimal | None


class DenominacionSalida(EsquemaSalida):
    denominacion: Decimal
    tipo: str
    cantidad: int
    subtotal: Decimal


class SesionSalida(EsquemaSalida):
    id: int
    caja_id: int
    caja: str
    sucursal: str
    usuario_id: int
    usuario: str
    estado: EstadoSesionCaja
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    monto_inicial: Decimal
    ventas: int
    anuladas: int
    total_vendido: Decimal | None
    ingresos: Decimal
    egresos: Decimal
    # Arqueo: None mientras está abierta para quien no puede ver todas las cajas (cierre ciego)
    efectivo_esperado: Decimal | None
    monto_contado: Decimal | None
    diferencia: Decimal | None
    observaciones_apertura: str | None
    observaciones_cierre: str | None
    puede_ver_esperado: bool


class SesionDetalle(SesionSalida):
    metodos: list[ResumenMetodo]
    movimientos: list[MovimientoCajaSalida]
    arqueo: list[DenominacionSalida]
    denominaciones: list[Decimal]


class EstadoCaja(EsquemaSalida):
    """Lo que necesita la barra superior y el POS: si hay caja abierta y cuál."""

    sesion: SesionSalida | None
    sucursal_distinta: bool  # la caja abierta del usuario es de otra sucursal
