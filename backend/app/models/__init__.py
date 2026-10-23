"""Importa todos los modelos para que queden registrados en Base.metadata (Alembic, relaciones)."""

from app.core.database import Base
from app.models.ajuste_inventario import AjusteInventario, DetalleAjusteInventario, MotivoAjuste
from app.models.auditoria import Auditoria
from app.models.caja import ArqueoDenominacion, Caja, ResumenCierreCaja, SesionCaja
from app.models.categoria import Categoria
from app.models.cliente import Cliente
from app.models.compra import Compra, CuentaPorPagar, DetalleCompra, PagoProveedor
from app.models.configuracion import Empresa, Impresora, SerieComprobante
from app.models.correlativo import Correlativo
from app.models.cuenta_por_cobrar import Abono, CuentaPorCobrar
from app.models.devolucion import DetalleDevolucion, Devolucion
from app.models.historial_precio import HistorialPrecio
from app.models.inventario_fisico import DetalleInventarioFisico, InventarioFisico
from app.models.lote import Lote
from app.models.marca import Marca
from app.models.movimiento_caja import MovimientoCaja
from app.models.movimiento_inventario import MovimientoInventario
from app.models.operacion_idempotente import OperacionIdempotente
from app.models.pago_venta import PagoVenta
from app.models.parametro import ParametroSistema
from app.models.permiso import Permiso, rol_permisos
from app.models.producto import CodigoBarras, Producto, ProductoPresentacion
from app.models.producto_proveedor import ProductoProveedor
from app.models.proveedor import Proveedor
from app.models.rol import Rol
from app.models.stock_almacen import StockAlmacen
from app.models.sucursal import Almacen, Sucursal, usuario_sucursales
from app.models.transferencia import DetalleTransferencia, Transferencia
from app.models.usuario import RefreshToken, Usuario
from app.models.venta import DetalleVenta, Venta

__all__ = [
    "Abono",
    "AjusteInventario",
    "Almacen",
    "ArqueoDenominacion",
    "Auditoria",
    "Base",
    "Caja",
    "Categoria",
    "Cliente",
    "CodigoBarras",
    "Compra",
    "Correlativo",
    "CuentaPorCobrar",
    "CuentaPorPagar",
    "DetalleAjusteInventario",
    "DetalleCompra",
    "DetalleDevolucion",
    "DetalleInventarioFisico",
    "DetalleTransferencia",
    "DetalleVenta",
    "Devolucion",
    "Empresa",
    "HistorialPrecio",
    "Impresora",
    "InventarioFisico",
    "Lote",
    "Marca",
    "MotivoAjuste",
    "MovimientoCaja",
    "MovimientoInventario",
    "OperacionIdempotente",
    "PagoProveedor",
    "PagoVenta",
    "ParametroSistema",
    "Permiso",
    "Producto",
    "ProductoPresentacion",
    "ProductoProveedor",
    "Proveedor",
    "RefreshToken",
    "ResumenCierreCaja",
    "Rol",
    "SerieComprobante",
    "SesionCaja",
    "StockAlmacen",
    "Sucursal",
    "Transferencia",
    "Usuario",
    "Venta",
    "rol_permisos",
    "usuario_sucursales",
]
