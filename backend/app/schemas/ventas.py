from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.models.enums import EstadoVenta, MetodoPago, TipoAfectacionIGV, TipoComprobante, UnidadMedida
from app.schemas.base import EsquemaEntrada, EsquemaSalida
from app.schemas.caja import Monto, MontoPositivo
from app.schemas.productos import CantidadPositiva, Precio

Token = Annotated[str, Field(min_length=20, max_length=1000)]


# --- Catálogo del POS -------------------------------------------------------------------------------------


class PresentacionPos(EsquemaSalida):
    id: int
    nombre: str
    factor: Decimal
    precio: Decimal
    codigos: list[str]


class ProductoPos(EsquemaSalida):
    id: int
    nombre: str
    codigos: list[str]
    codigo_interno: str | None
    precio: Decimal
    unidad_medida: UnidadMedida
    permite_decimales: bool
    maneja_lotes: bool
    afecto_icbper: bool
    tipo_afectacion_igv: TipoAfectacionIGV
    stock: Decimal
    categoria_id: int | None
    categoria: str | None
    categoria_color: str | None
    miniatura_url: str | None
    presentaciones: list[PresentacionPos]


class ConfiguracionPos(EsquemaSalida):
    igv_porcentaje: Decimal
    icbper_monto: Decimal
    precios_incluyen_igv: bool
    redondeo_efectivo: Decimal
    descuento_maximo: Decimal  # % que puede dar el cajero sin autorización
    simbolo_moneda: str
    serie: str | None
    almacen_id: int | None


class CatalogoPos(EsquemaSalida):
    configuracion: ConfiguracionPos
    productos: list[ProductoPos]


# --- Venta ------------------------------------------------------------------------------------------------


class ItemVentaEntrada(EsquemaEntrada):
    producto_id: int
    presentacion_id: int | None = None
    cantidad: CantidadPositiva
    # Precio que vio el cajero: si cambió mientras vendía, la venta se rechaza para que no cobre otro monto
    precio_unitario: Precio
    descuento: Precio = Decimal("0")


class PagoEntrada(EsquemaEntrada):
    metodo: MetodoPago
    monto: MontoPositivo
    monto_recibido: Monto | None = None  # solo efectivo: con cuánto paga el cliente
    referencia: Annotated[str | None, Field(max_length=100)] = None

    @model_validator(mode="after")
    def _recibido(self):
        if self.metodo != MetodoPago.EFECTIVO and self.monto_recibido is not None:
            raise ValueError("Solo el pago en efectivo lleva monto recibido")
        if self.monto_recibido is not None and self.monto_recibido < self.monto:
            raise ValueError("El monto recibido no alcanza")
        return self


class VentaCrear(EsquemaEntrada):
    items: Annotated[list[ItemVentaEntrada], Field(min_length=1, max_length=300)]
    descuento: Precio = Decimal("0")  # descuento global, en soles
    pagos: Annotated[list[PagoEntrada], Field(min_length=1, max_length=6)]
    cliente_id: int | None = None
    # Lo que la pantalla le mostró al cliente que debe pagar: si el servidor calcula otro monto, no se vende
    total: Monto
    observaciones: Annotated[str | None, Field(max_length=300)] = None
    autorizaciones: Annotated[list[Token], Field(max_length=4)] = []

    @field_validator("pagos")
    @classmethod
    def _un_efectivo(cls, v: list[PagoEntrada]) -> list[PagoEntrada]:
        if sum(1 for p in v if p.metodo == MetodoPago.EFECTIVO) > 1:
            raise ValueError("Registre el efectivo en un solo pago")
        if sum(1 for p in v if p.metodo == MetodoPago.CREDITO) > 1:
            raise ValueError("Registre el fiado en un solo pago")
        return v


class AnulacionEntrada(EsquemaEntrada):
    motivo: Annotated[str, Field(min_length=5, max_length=300)]
    autorizacion: Token | None = None


class AutorizacionEntrada(EsquemaEntrada):
    username: Annotated[str, Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=1, max_length=128)]
    permiso: Annotated[str, Field(max_length=60)]


class AutorizacionSalida(EsquemaSalida):
    token: str
    supervisor: str
    permiso: str
    expira_en_segundos: int


# --- Consultas --------------------------------------------------------------------------------------------


class DetalleVentaSalida(EsquemaSalida):
    id: int
    producto_id: int
    presentacion_id: int | None
    descripcion: str
    cantidad: Decimal
    factor: Decimal
    precio_unitario: Decimal
    descuento: Decimal
    tipo_afectacion_igv: TipoAfectacionIGV
    igv: Decimal
    icbper: Decimal
    total: Decimal


class PagoSalida(EsquemaSalida):
    metodo: MetodoPago
    monto: Decimal
    monto_recibido: Decimal | None
    referencia: str | None


class VentaListado(EsquemaSalida):
    id: int
    comprobante: str  # T001-00000123
    tipo_comprobante: TipoComprobante
    fecha: datetime
    usuario: str
    cliente: str | None
    caja: str
    items: int
    total: Decimal
    a_cobrar: Decimal
    metodos: list[MetodoPago]
    estado: EstadoVenta


class EmpresaTicket(EsquemaSalida):
    ruc: str
    razon_social: str
    nombre_comercial: str | None
    direccion: str | None
    telefono: str | None
    mensaje_ticket: str | None
    sucursal: str
    direccion_sucursal: str | None


class VentaDetalle(VentaListado):
    sesion_caja_id: int
    cliente_documento: str | None
    op_gravadas: Decimal
    op_exoneradas: Decimal
    op_inafectas: Decimal
    igv: Decimal
    igv_porcentaje: Decimal
    icbper: Decimal
    descuento: Decimal
    redondeo: Decimal
    vuelto: Decimal
    es_credito: bool
    observaciones: str | None
    detalles: list[DetalleVentaSalida]
    pagos: list[PagoSalida]
    anulada_por: str | None
    fecha_anulacion: datetime | None
    motivo_anulacion: str | None
    puede_anular: bool
    empresa: EmpresaTicket

