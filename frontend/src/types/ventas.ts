// Reflejan app/schemas/ventas.py, caja.py y clientes.py

import type { UnidadMedida } from "@/types/productos";

export type MetodoPago = "EFECTIVO" | "TARJETA" | "YAPE" | "PLIN" | "TRANSFERENCIA" | "CREDITO";
export type Afectacion = "GRAVADO" | "EXONERADO" | "INAFECTO";
export type EstadoVenta = "COMPLETADA" | "DEVUELTA_PARCIAL" | "DEVUELTA" | "ANULADA";
export type EstadoSesion = "ABIERTA" | "CERRADA";

// ---------- Catálogo del POS ----------
export interface PresentacionPos {
  id: number;
  nombre: string;
  factor: string;
  precio: string;
  codigos: string[];
}

export interface ProductoPos {
  id: number;
  nombre: string;
  codigos: string[];
  codigo_interno: string | null;
  precio: string;
  unidad_medida: UnidadMedida;
  permite_decimales: boolean;
  maneja_lotes: boolean;
  afecto_icbper: boolean;
  tipo_afectacion_igv: Afectacion;
  stock: string;
  categoria_id: number | null;
  categoria: string | null;
  categoria_color: string | null;
  miniatura_url: string | null;
  presentaciones: PresentacionPos[];
}

export interface ConfiguracionPos {
  igv_porcentaje: string;
  icbper_monto: string;
  precios_incluyen_igv: boolean;
  redondeo_efectivo: string;
  descuento_maximo: string;
  simbolo_moneda: string;
  serie: string | null;
  almacen_id: number | null;
}

export interface CatalogoPos {
  configuracion: ConfiguracionPos;
  productos: ProductoPos[];
}

// ---------- Venta ----------
export interface PagoEntrada {
  metodo: MetodoPago;
  monto: string;
  monto_recibido?: string | null;
  referencia?: string | null;
}

export interface VentaEntrada {
  items: {
    producto_id: number;
    presentacion_id: number | null;
    cantidad: string;
    precio_unitario: string;
    descuento: string;
  }[];
  descuento: string;
  pagos: PagoEntrada[];
  cliente_id: number | null;
  total: string;
  observaciones?: string | null;
  autorizaciones: string[];
}

export interface VentaListado {
  id: number;
  comprobante: string;
  tipo_comprobante: string;
  fecha: string;
  usuario: string;
  cliente: string | null;
  caja: string;
  items: number;
  total: string;
  a_cobrar: string;
  metodos: MetodoPago[];
  estado: EstadoVenta;
}

export interface VentaDetalle extends VentaListado {
  sesion_caja_id: number;
  cliente_documento: string | null;
  op_gravadas: string;
  op_exoneradas: string;
  op_inafectas: string;
  igv: string;
  igv_porcentaje: string;
  icbper: string;
  descuento: string;
  redondeo: string;
  vuelto: string;
  es_credito: boolean;
  observaciones: string | null;
  detalles: {
    id: number;
    producto_id: number;
    presentacion_id: number | null;
    descripcion: string;
    cantidad: string;
    factor: string;
    precio_unitario: string;
    descuento: string;
    tipo_afectacion_igv: Afectacion;
    igv: string;
    icbper: string;
    total: string;
  }[];
  pagos: { metodo: MetodoPago; monto: string; monto_recibido: string | null; referencia: string | null }[];
  anulada_por: string | null;
  fecha_anulacion: string | null;
  motivo_anulacion: string | null;
  puede_anular: boolean;
  /** Firma del servidor: si alguien altera el ticket impreso, deja de coincidir */
  codigo_verificacion: string;
  /** Contenido del QR: RUC|TK|SERIE|NUMERO|IGV|TOTAL|FECHA|TIPO DOC|N.° DOC|CÓDIGO */
  qr: string;
  empresa: {
    ruc: string;
    razon_social: string;
    nombre_comercial: string | null;
    direccion: string | null;
    telefono: string | null;
    mensaje_ticket: string | null;
    sucursal: string;
    direccion_sucursal: string | null;
  };
}

export interface VerificacionTicket {
  valido: boolean;
  motivo: string;
  venta_id: number | null;
  comprobante: string | null;
  estado: EstadoVenta | null;
  total: string | null;
  fecha: string | null;
}

export interface Autorizacion {
  token: string;
  supervisor: string;
  permiso: string;
  expira_en_segundos: number;
}

// ---------- Caja ----------
export interface CajaFila {
  id: number;
  nombre: string;
  descripcion: string | null;
  sesion_id: number | null;
  abierta_por: string | null;
  abierta_desde: string | null;
  es_mia: boolean;
}

export interface Sesion {
  id: number;
  caja_id: number;
  caja: string;
  sucursal: string;
  usuario_id: number;
  usuario: string;
  estado: EstadoSesion;
  fecha_apertura: string;
  fecha_cierre: string | null;
  monto_inicial: string;
  ventas: number;
  anuladas: number;
  total_vendido: string | null;
  ingresos: string;
  egresos: string;
  efectivo_esperado: string | null;
  monto_contado: string | null;
  diferencia: string | null;
  observaciones_apertura: string | null;
  observaciones_cierre: string | null;
  puede_ver_esperado: boolean;
}

export interface SesionDetalle extends Sesion {
  metodos: {
    metodo: MetodoPago;
    operaciones: number;
    monto_sistema: string | null;
    monto_declarado: string | null;
    diferencia: string | null;
  }[];
  movimientos: { id: number; tipo: "INGRESO" | "EGRESO"; monto: string; concepto: string; usuario: string; creado_en: string }[];
  arqueo: { denominacion: string; tipo: string; cantidad: number; subtotal: string }[];
  denominaciones: string[];
}

export interface EstadoCaja {
  sesion: Sesion | null;
  sucursal_distinta: boolean;
}

// ---------- Clientes ----------
export type TipoDocumento = "DNI" | "RUC" | "CARNET_EXTRANJERIA" | "PASAPORTE" | "SIN_DOCUMENTO";

export interface Cliente {
  id: number;
  tipo_documento: TipoDocumento;
  numero_documento: string | null;
  nombre: string;
  telefono: string | null;
  permite_credito: boolean;
  limite_credito: string;
  deuda: string;
  activo: boolean;
}
