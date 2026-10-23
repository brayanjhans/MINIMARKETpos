import enum


class UnidadMedida(enum.StrEnum):
    UNIDAD = "UNIDAD"
    KILOGRAMO = "KILOGRAMO"
    GRAMO = "GRAMO"
    LITRO = "LITRO"
    MILILITRO = "MILILITRO"
    PAQUETE = "PAQUETE"
    CAJA = "CAJA"
    DOCENA = "DOCENA"


class TipoAfectacionIGV(enum.StrEnum):
    GRAVADO = "GRAVADO"
    EXONERADO = "EXONERADO"  # ej. frutas, verduras, huevos (Apéndice I de la Ley del IGV)
    INAFECTO = "INAFECTO"


class TipoMovimientoInventario(enum.StrEnum):
    STOCK_INICIAL = "STOCK_INICIAL"
    ENTRADA_COMPRA = "ENTRADA_COMPRA"
    ANULACION_COMPRA = "ANULACION_COMPRA"
    SALIDA_VENTA = "SALIDA_VENTA"
    ANULACION_VENTA = "ANULACION_VENTA"
    DEVOLUCION_VENTA = "DEVOLUCION_VENTA"
    AJUSTE_ENTRADA = "AJUSTE_ENTRADA"
    AJUSTE_SALIDA = "AJUSTE_SALIDA"
    INVENTARIO_FISICO = "INVENTARIO_FISICO"
    TRANSFERENCIA_SALIDA = "TRANSFERENCIA_SALIDA"
    TRANSFERENCIA_ENTRADA = "TRANSFERENCIA_ENTRADA"


class EstadoDocumento(enum.StrEnum):
    """Estado de documentos internos (ajustes de inventario)."""

    BORRADOR = "BORRADOR"
    PENDIENTE_APROBACION = "PENDIENTE_APROBACION"
    APLICADO = "APLICADO"
    ANULADO = "ANULADO"


class TipoMotivoAjuste(enum.StrEnum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AMBOS = "AMBOS"


class EstadoTransferencia(enum.StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_TRANSITO = "EN_TRANSITO"  # salió del almacén de origen
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"


class TipoPrecio(enum.StrEnum):
    COSTO = "COSTO"
    VENTA = "VENTA"


class EstadoInventarioFisico(enum.StrEnum):
    EN_PROCESO = "EN_PROCESO"
    APLICADO = "APLICADO"
    CANCELADO = "CANCELADO"


class EstadoSesionCaja(enum.StrEnum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"


class TipoMovimientoCaja(enum.StrEnum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"


class TipoDenominacion(enum.StrEnum):
    BILLETE = "BILLETE"
    MONEDA = "MONEDA"


class TipoComprobante(enum.StrEnum):
    TICKET = "TICKET"
    BOLETA = "BOLETA"
    FACTURA = "FACTURA"


class EstadoVenta(enum.StrEnum):
    COMPLETADA = "COMPLETADA"
    DEVUELTA_PARCIAL = "DEVUELTA_PARCIAL"
    DEVUELTA = "DEVUELTA"
    ANULADA = "ANULADA"


class MetodoPago(enum.StrEnum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    YAPE = "YAPE"
    PLIN = "PLIN"
    TRANSFERENCIA = "TRANSFERENCIA"
    CREDITO = "CREDITO"  # venta al fiado


class TipoDocumentoIdentidad(enum.StrEnum):
    DNI = "DNI"
    RUC = "RUC"
    CARNET_EXTRANJERIA = "CARNET_EXTRANJERIA"
    PASAPORTE = "PASAPORTE"
    SIN_DOCUMENTO = "SIN_DOCUMENTO"


class EstadoCompra(enum.StrEnum):
    PENDIENTE = "PENDIENTE"  # orden de compra emitida
    RECIBIDA_PARCIAL = "RECIBIDA_PARCIAL"
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"


class CondicionPago(enum.StrEnum):
    CONTADO = "CONTADO"
    CREDITO = "CREDITO"


class EstadoCuenta(enum.StrEnum):
    PENDIENTE = "PENDIENTE"
    PARCIAL = "PARCIAL"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class TipoParametro(enum.StrEnum):
    TEXTO = "TEXTO"
    ENTERO = "ENTERO"
    DECIMAL = "DECIMAL"
    BOOLEANO = "BOOLEANO"
    JSON = "JSON"


class TipoImpresora(enum.StrEnum):
    TERMICA_58 = "TERMICA_58"
    TERMICA_80 = "TERMICA_80"
    A4 = "A4"


class ConexionImpresora(enum.StrEnum):
    NAVEGADOR = "NAVEGADOR"  # impresión desde el diálogo del navegador
    USB = "USB"
    RED = "RED"
