import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field, model_validator

from app.models.enums import TipoAfectacionIGV, TipoPrecio, UnidadMedida
from app.schemas.base import EsquemaEntrada, EsquemaSalida

_PATRON_CODIGO = re.compile(r"^[0-9A-Za-z.\-]{3,50}$")
_PATRON_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def normalizar_codigo(valor: str) -> str:
    valor = valor.strip().upper()
    if not _PATRON_CODIGO.match(valor):
        raise ValueError("El código de barras solo admite letras, números, punto y guion (3 a 50 caracteres)")
    return valor


def _sin_repetidos(codigos: list[str]) -> list[str]:
    if len(set(codigos)) != len(codigos):
        raise ValueError("Hay códigos de barras repetidos")
    return codigos


CodigoBarrasTexto = Annotated[str, AfterValidator(normalizar_codigo)]
ListaCodigos = Annotated[list[CodigoBarrasTexto], Field(max_length=10), AfterValidator(_sin_repetidos)]
Precio = Annotated[Decimal, Field(ge=0, le=Decimal("999999.99"), max_digits=12, decimal_places=2)]
Costo = Annotated[Decimal, Field(ge=0, le=Decimal("999999.9999"), max_digits=14, decimal_places=4)]
CantidadPositiva = Annotated[Decimal, Field(gt=0, le=Decimal("999999.999"), max_digits=12, decimal_places=3)]
CantidadNoNegativa = Annotated[Decimal, Field(ge=0, le=Decimal("999999.999"), max_digits=12, decimal_places=3)]
Nombre = Annotated[str, Field(min_length=2, max_length=200)]


def _color(valor: str | None) -> str | None:
    if valor is not None and not _PATRON_COLOR.match(valor):
        raise ValueError("El color debe tener el formato #RRGGBB")
    return valor.lower() if valor else valor


# --- Categorías y marcas ---------------------------------------------------------------------------------


class CategoriaCrear(EsquemaEntrada):
    nombre: Annotated[str, Field(min_length=2, max_length=80)]
    descripcion: Annotated[str | None, Field(max_length=250)] = None
    color: Annotated[str | None, AfterValidator(_color)] = None


class CategoriaActualizar(EsquemaEntrada):
    nombre: Annotated[str | None, Field(min_length=2, max_length=80)] = None
    descripcion: Annotated[str | None, Field(max_length=250)] = None
    color: Annotated[str | None, AfterValidator(_color)] = None
    activo: bool | None = None


class CategoriaResumen(EsquemaSalida):
    id: int
    nombre: str
    color: str | None


class CategoriaSalida(CategoriaResumen):
    descripcion: str | None
    activo: bool
    productos: int = 0
    valor_inventario: Decimal = Decimal(0)


class MarcaCrear(EsquemaEntrada):
    nombre: Annotated[str, Field(min_length=1, max_length=80)]


class MarcaActualizar(EsquemaEntrada):
    nombre: Annotated[str | None, Field(min_length=1, max_length=80)] = None
    activo: bool | None = None


class MarcaResumen(EsquemaSalida):
    id: int
    nombre: str


class MarcaSalida(MarcaResumen):
    activo: bool
    productos: int = 0


# --- Productos ---------------------------------------------------------------------------------------------


class PresentacionEntrada(EsquemaEntrada):
    id: int | None = Field(default=None, description="Vacío = presentación nueva")
    nombre: Annotated[str, Field(min_length=1, max_length=80)]
    factor: Annotated[Decimal, Field(gt=1, le=Decimal("100000"), max_digits=12, decimal_places=3)]
    precio_venta: Precio
    codigos: ListaCodigos = []
    activo: bool = True


class _CamposProducto(EsquemaEntrada):
    descripcion: Annotated[str | None, Field(max_length=2000)] = None
    codigo_interno: Annotated[str | None, Field(min_length=1, max_length=30)] = None
    categoria_id: int | None = None
    marca_id: int | None = None
    stock_minimo: CantidadNoNegativa = Decimal(0)
    tipo_afectacion_igv: TipoAfectacionIGV = TipoAfectacionIGV.GRAVADO
    afecto_icbper: bool = False


class ProductoCrear(_CamposProducto):
    nombre: Nombre
    codigos: ListaCodigos = []
    unidad_medida: UnidadMedida = UnidadMedida.UNIDAD
    precio_venta: Precio
    precio_costo: Costo = Decimal(0)
    maneja_lotes: bool = False
    permite_decimales: bool = False
    presentaciones: Annotated[list[PresentacionEntrada], Field(max_length=10)] = []

    @model_validator(mode="after")
    def _presentaciones_unicas(self) -> ProductoCrear:
        _validar_presentaciones(self.presentaciones, self.codigos)
        return self


class ProductoActualizar(EsquemaEntrada):
    """Edición parcial. `version` es la que el usuario tenía en pantalla: si otro la cambió, se avisa."""

    version: int
    nombre: Nombre | None = None
    descripcion: Annotated[str | None, Field(max_length=2000)] = None
    codigo_interno: Annotated[str | None, Field(min_length=1, max_length=30)] = None
    codigos: ListaCodigos | None = None
    categoria_id: int | None = None
    marca_id: int | None = None
    unidad_medida: UnidadMedida | None = None
    precio_venta: Precio | None = None
    precio_costo: Costo | None = None
    stock_minimo: CantidadNoNegativa | None = None
    tipo_afectacion_igv: TipoAfectacionIGV | None = None
    afecto_icbper: bool | None = None
    maneja_lotes: bool | None = None
    permite_decimales: bool | None = None
    activo: bool | None = None
    presentaciones: Annotated[list[PresentacionEntrada] | None, Field(max_length=10)] = None

    @model_validator(mode="after")
    def _presentaciones_unicas(self) -> ProductoActualizar:
        if self.presentaciones is not None:
            _validar_presentaciones(self.presentaciones, self.codigos or [])
        return self


def _validar_presentaciones(presentaciones: list[PresentacionEntrada], codigos_base: list[str]) -> None:
    nombres = [p.nombre.lower() for p in presentaciones]
    if len(set(nombres)) != len(nombres):
        raise ValueError("Hay presentaciones con el mismo nombre")
    todos = list(codigos_base) + [c for p in presentaciones for c in p.codigos]
    if len(set(todos)) != len(todos):
        raise ValueError("Un mismo código de barras está en el producto y en una presentación")


class CodigoSalida(EsquemaSalida):
    id: int
    codigo: str
    presentacion_id: int | None


class PresentacionSalida(EsquemaSalida):
    id: int
    nombre: str
    factor: Decimal
    precio_venta: Decimal
    activo: bool
    codigos: list[str] = []


class StockEnAlmacen(EsquemaSalida):
    almacen_id: int
    almacen: str
    sucursal_id: int
    sucursal: str
    cantidad: Decimal
    pendiente_lote: Decimal
    stock_minimo: Decimal


class ProductoListado(EsquemaSalida):
    id: int
    nombre: str
    codigo_interno: str | None
    codigo_barras: str | None = Field(description="Primer código de la unidad base")
    categoria: CategoriaResumen | None
    marca: MarcaResumen | None
    unidad_medida: UnidadMedida
    precio_venta: Decimal
    # Se ocultan (null) a quien no puede ver costos
    precio_costo: Decimal | None
    margen: Decimal | None = Field(description="Ganancia sobre el precio de venta, en %")
    stock: Decimal = Field(description="Stock en el almacén de venta de la sucursal actual")
    stock_minimo: Decimal
    estado_stock: str = Field(description="normal, bajo, sin_stock o negativo")
    maneja_lotes: bool
    permite_decimales: bool
    imagen_url: str | None
    miniatura_url: str | None
    activo: bool


class ProductoDetalle(ProductoListado):
    descripcion: str | None
    codigos: list[str]
    presentaciones: list[PresentacionSalida]
    tipo_afectacion_igv: TipoAfectacionIGV
    afecto_icbper: bool
    version: int
    tiene_movimientos: bool = Field(description="Si ya tiene movimientos no se pueden cambiar unidad, lotes ni costo")
    stock_por_almacen: list[StockEnAlmacen]
    creado_en: datetime
    actualizado_en: datetime


class ResumenProductos(EsquemaSalida):
    total: int
    activos: int
    inactivos: int
    stock_bajo: int
    sin_stock: int
    negativos: int
    sin_codigo: int


class HistorialPrecioSalida(EsquemaSalida):
    id: int
    tipo: TipoPrecio
    presentacion_id: int | None
    precio_anterior: Decimal
    precio_nuevo: Decimal
    origen: str
    usuario: str | None
    creado_en: datetime


class ProductoPorCodigo(EsquemaSalida):
    """Resultado de escanear un código: el producto y, si corresponde, la presentación."""

    producto: ProductoListado
    presentacion: PresentacionSalida | None
