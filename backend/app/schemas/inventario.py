from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.models.enums import (
    EstadoDocumento,
    EstadoInventarioFisico,
    EstadoTransferencia,
    TipoMotivoAjuste,
    TipoMovimientoInventario,
    UnidadMedida,
)
from app.schemas.base import EsquemaEntrada, EsquemaSalida
from app.schemas.productos import CantidadNoNegativa, CantidadPositiva, Costo

Observaciones = Annotated[str | None, Field(max_length=300)]
NumeroLote = Annotated[str | None, Field(min_length=1, max_length=50)]
CantidadConSigno = Annotated[
    Decimal, Field(ge=Decimal("-999999.999"), le=Decimal("999999.999"), max_digits=12, decimal_places=3)
]


class AlmacenSalida(EsquemaSalida):
    id: int
    nombre: str
    sucursal_id: int
    sucursal: str
    es_almacen_venta: bool
    es_sucursal_actual: bool


# --- Consultas ---------------------------------------------------------------------------------------------


class StockFila(EsquemaSalida):
    producto_id: int
    nombre: str
    codigo_barras: str | None
    categoria: str | None
    categoria_color: str | None
    unidad_medida: UnidadMedida
    maneja_lotes: bool
    cantidad: Decimal
    pendiente_lote: Decimal
    stock_minimo: Decimal
    estado: str
    costo_unitario: Decimal | None
    valor: Decimal | None
    miniatura_url: str | None


class ResumenInventario(EsquemaSalida):
    almacen_id: int
    valor_total: Decimal | None
    productos: int
    unidades: Decimal
    stock_bajo: int
    sin_stock: int
    por_regularizar: int
    lotes_por_vencer: int
    valor_por_vencer: Decimal | None
    lotes_vencidos: int
    dias_alerta: int
    mermas_mes: Decimal | None
    ajustes_mes: int
    por_aprobar: int
    transito_valor: Decimal | None
    transito_documentos: int


class LoteSalida(EsquemaSalida):
    id: int
    producto_id: int
    producto: str
    almacen_id: int
    numero_lote: str
    fecha_vencimiento: date | None
    dias_para_vencer: int | None
    cantidad_actual: Decimal
    costo_unitario: Decimal | None
    valor: Decimal | None


class MovimientoSalida(EsquemaSalida):
    id: int
    creado_en: datetime
    producto_id: int
    almacen_id: int
    tipo: TipoMovimientoInventario
    cantidad: Decimal
    stock_anterior: Decimal
    stock_nuevo: Decimal
    costo_unitario: Decimal | None
    lote: str | None
    referencia_tipo: str | None
    referencia_id: int | None
    documento: str | None
    motivo: str | None
    usuario: str | None


class ProblemaIntegridad(EsquemaSalida):
    tipo: str
    producto_id: int | None
    producto: str | None
    almacen_id: int | None
    detalle: str


class ReporteIntegridad(EsquemaSalida):
    correcto: bool
    revisados: int
    problemas: list[ProblemaIntegridad]


# --- Stock inicial -----------------------------------------------------------------------------------------


class StockInicialItem(EsquemaEntrada):
    producto_id: int
    cantidad: CantidadPositiva
    costo_unitario: Costo
    numero_lote: NumeroLote = None
    fecha_vencimiento: date | None = None


class StockInicialEntrada(EsquemaEntrada):
    almacen_id: int | None = Field(default=None, description="Vacío = almacén de venta de la sucursal actual")
    items: Annotated[list[StockInicialItem], Field(min_length=1, max_length=1000)]


class StockInicialResultado(EsquemaSalida):
    productos: int
    unidades: Decimal
    valor: Decimal


class ProductoCargable(EsquemaSalida):
    """Si un producto puede recibir stock inicial en un almacén (no debe tener movimientos ahí)."""

    producto_id: int
    puede: bool
    motivo: str | None


# --- Ajustes -----------------------------------------------------------------------------------------------


class MotivoAjusteSalida(EsquemaSalida):
    id: int
    nombre: str
    tipo: TipoMotivoAjuste
    es_merma: bool


class AjusteDetalleEntrada(EsquemaEntrada):
    producto_id: int
    cantidad: CantidadConSigno = Field(description="Positivo = entra, negativo = sale")
    lote_id: int | None = None
    numero_lote: NumeroLote = None
    fecha_vencimiento: date | None = None

    @field_validator("cantidad")
    @classmethod
    def _no_cero(cls, valor: Decimal) -> Decimal:
        if valor == 0:
            raise ValueError("La cantidad no puede ser cero")
        return valor


class AjusteCrear(EsquemaEntrada):
    almacen_id: int | None = None
    motivo_id: int
    observaciones: Observaciones = None
    detalles: Annotated[list[AjusteDetalleEntrada], Field(min_length=1, max_length=200)]
    enviar: bool = Field(default=True, description="True = se envía a aprobación; False = queda en borrador")


class AjusteActualizar(EsquemaEntrada):
    motivo_id: int
    observaciones: Observaciones = None
    detalles: Annotated[list[AjusteDetalleEntrada], Field(min_length=1, max_length=200)]


class Rechazo(EsquemaEntrada):
    motivo: Annotated[str, Field(min_length=3, max_length=300)]


class AjusteDetalleSalida(EsquemaSalida):
    id: int
    producto_id: int
    producto: str
    lote_id: int | None
    lote: str | None
    fecha_vencimiento: date | None
    cantidad: Decimal
    costo_unitario: Decimal | None
    valor: Decimal | None


class AjusteListado(EsquemaSalida):
    id: int
    numero: str
    almacen_id: int
    almacen: str
    motivo: str
    es_merma: bool
    estado: EstadoDocumento
    observaciones: str | None
    usuario: str | None
    aprobado_por: str | None
    total_unidades: Decimal
    valor: Decimal | None
    creado_en: datetime
    fecha_envio: datetime | None
    fecha_aplicacion: datetime | None


class AjusteDetalle(AjusteListado):
    usuario_id: int
    motivo_id: int
    motivo_rechazo: str | None
    detalles: list[AjusteDetalleSalida]
    puede_aprobar: bool


# --- Transferencias ----------------------------------------------------------------------------------------


class TransferenciaDetalleEntrada(EsquemaEntrada):
    producto_id: int
    cantidad: CantidadPositiva
    lote_id: int | None = Field(default=None, description="Vacío = se toman los lotes que vencen primero")


class TransferenciaCrear(EsquemaEntrada):
    almacen_origen_id: int | None = Field(default=None, description="Vacío = almacén de venta de la sucursal actual")
    almacen_destino_id: int
    observaciones: Observaciones = None
    detalles: Annotated[list[TransferenciaDetalleEntrada], Field(min_length=1, max_length=200)]
    enviar: bool = True


class RecepcionDetalle(EsquemaEntrada):
    detalle_id: int
    cantidad_recibida: CantidadNoNegativa
    motivo_faltante: Annotated[str | None, Field(max_length=150)] = None


class RecepcionEntrada(EsquemaEntrada):
    detalles: Annotated[list[RecepcionDetalle], Field(max_length=500)] = Field(
        default=[], description="Las líneas no indicadas se reciben completas"
    )
    observaciones: Observaciones = None


class TransferenciaDetalleSalida(EsquemaSalida):
    id: int
    producto_id: int
    producto: str
    lote_id: int | None
    lote: str | None
    fecha_vencimiento: date | None
    cantidad: Decimal
    cantidad_recibida: Decimal
    faltante: Decimal
    motivo_faltante: str | None
    costo_unitario: Decimal | None


class TransferenciaListado(EsquemaSalida):
    id: int
    numero: str
    estado: EstadoTransferencia
    almacen_origen_id: int
    almacen_origen: str
    sucursal_origen: str
    almacen_destino_id: int
    almacen_destino: str
    sucursal_destino: str
    observaciones: str | None
    usuario: str | None
    usuario_recibe: str | None
    productos: int
    valor: Decimal | None
    creado_en: datetime
    fecha_envio: datetime | None
    fecha_recepcion: datetime | None


class TransferenciaDetalle(TransferenciaListado):
    detalles: list[TransferenciaDetalleSalida]
    puede_recibir: bool
    puede_anular: bool


# --- Inventario físico -------------------------------------------------------------------------------------


class InventarioFisicoCrear(EsquemaEntrada):
    almacen_id: int | None = None
    descripcion: Annotated[str | None, Field(max_length=200)] = None
    categoria_id: int | None = None
    producto_ids: Annotated[list[int] | None, Field(max_length=2000)] = None

    @model_validator(mode="after")
    def _un_alcance(self) -> InventarioFisicoCrear:
        if self.categoria_id is not None and self.producto_ids:
            raise ValueError("Indique una categoría o una lista de productos, no ambas")
        return self


class ConteoItem(EsquemaEntrada):
    detalle_id: int
    stock_contado: CantidadNoNegativa | None = Field(description="Vacío = aún no contado")


class ConteoEntrada(EsquemaEntrada):
    items: Annotated[list[ConteoItem], Field(min_length=1, max_length=2000)]


class FisicoDetalleSalida(EsquemaSalida):
    id: int
    producto_id: int
    producto: str
    codigo_barras: str | None
    lote_id: int | None
    lote: str | None
    fecha_vencimiento: date | None
    stock_sistema: Decimal
    stock_contado: Decimal | None
    diferencia: Decimal | None
    costo_unitario: Decimal | None
    valor_diferencia: Decimal | None


class FisicoListado(EsquemaSalida):
    id: int
    numero: str
    almacen_id: int
    almacen: str
    descripcion: str | None
    estado: EstadoInventarioFisico
    usuario: str | None
    aprobado_por: str | None
    total_lineas: int
    contadas: int
    con_diferencia: int
    valor_faltante: Decimal | None
    valor_sobrante: Decimal | None
    creado_en: datetime
    fecha_envio: datetime | None
    fecha_aplicacion: datetime | None


class FisicoDetalle(FisicoListado):
    usuario_id: int
    categoria_id: int | None
    motivo_rechazo: str | None
    detalles: list[FisicoDetalleSalida]
    puede_aprobar: bool
