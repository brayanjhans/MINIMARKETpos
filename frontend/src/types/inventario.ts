import type { UnidadMedida } from "@/types/productos";

export type EstadoDocumento = "BORRADOR" | "PENDIENTE_APROBACION" | "APLICADO" | "RECHAZADO" | "ANULADO";
export type EstadoTransferencia = "PENDIENTE" | "EN_TRANSITO" | "RECIBIDA" | "ANULADA";
export type EstadoFisico = "EN_PROCESO" | "PENDIENTE_APROBACION" | "APLICADO" | "CANCELADO";
export type TipoMovimiento =
  | "STOCK_INICIAL"
  | "ENTRADA_COMPRA"
  | "ANULACION_COMPRA"
  | "SALIDA_VENTA"
  | "ANULACION_VENTA"
  | "DEVOLUCION_VENTA"
  | "AJUSTE_ENTRADA"
  | "AJUSTE_SALIDA"
  | "INVENTARIO_FISICO"
  | "TRANSFERENCIA_SALIDA"
  | "TRANSFERENCIA_ENTRADA"
  | "TRANSFERENCIA_ANULADA";

export interface Almacen {
  id: number;
  nombre: string;
  sucursal_id: number;
  sucursal: string;
  es_almacen_venta: boolean;
  es_sucursal_actual: boolean;
}

export interface StockFila {
  producto_id: number;
  nombre: string;
  codigo_barras: string | null;
  categoria: string | null;
  categoria_color: string | null;
  unidad_medida: UnidadMedida;
  maneja_lotes: boolean;
  cantidad: string;
  pendiente_lote: string;
  stock_minimo: string;
  estado: "normal" | "bajo" | "sin_stock" | "negativo" | "por_regularizar";
  costo_unitario: string | null;
  valor: string | null;
  miniatura_url: string | null;
}

export interface ResumenInventario {
  almacen_id: number;
  valor_total: string | null;
  productos: number;
  unidades: string;
  stock_bajo: number;
  sin_stock: number;
  por_regularizar: number;
  lotes_por_vencer: number;
  valor_por_vencer: string | null;
  lotes_vencidos: number;
  dias_alerta: number;
  mermas_mes: string | null;
  ajustes_mes: number;
  por_aprobar: number;
  transito_valor: string | null;
  transito_documentos: number;
}

export interface Lote {
  id: number;
  producto_id: number;
  producto: string;
  almacen_id: number;
  numero_lote: string;
  fecha_vencimiento: string | null;
  dias_para_vencer: number | null;
  cantidad_actual: string;
  costo_unitario: string | null;
  valor: string | null;
}

export interface Movimiento {
  id: number;
  creado_en: string;
  producto_id: number;
  almacen_id: number;
  tipo: TipoMovimiento;
  cantidad: string;
  stock_anterior: string;
  stock_nuevo: string;
  costo_unitario: string | null;
  lote: string | null;
  referencia_tipo: string | null;
  referencia_id: number | null;
  documento: string | null;
  motivo: string | null;
  usuario: string | null;
}

export interface MotivoAjuste {
  id: number;
  nombre: string;
  tipo: "ENTRADA" | "SALIDA" | "AMBOS";
  es_merma: boolean;
}

export interface AjusteDetalleEntrada {
  producto_id: number;
  cantidad: string;
  lote_id?: number | null;
  numero_lote?: string | null;
  fecha_vencimiento?: string | null;
}

export interface AjusteListado {
  id: number;
  numero: string;
  almacen_id: number;
  almacen: string;
  motivo: string;
  es_merma: boolean;
  estado: EstadoDocumento;
  observaciones: string | null;
  usuario: string | null;
  aprobado_por: string | null;
  total_unidades: string;
  valor: string | null;
  creado_en: string;
  fecha_envio: string | null;
  fecha_aplicacion: string | null;
}

export interface AjusteDetalle extends AjusteListado {
  usuario_id: number;
  motivo_id: number;
  motivo_rechazo: string | null;
  puede_aprobar: boolean;
  detalles: {
    id: number;
    producto_id: number;
    producto: string;
    lote_id: number | null;
    lote: string | null;
    fecha_vencimiento: string | null;
    cantidad: string;
    costo_unitario: string | null;
    valor: string | null;
  }[];
}

export interface TransferenciaListado {
  id: number;
  numero: string;
  estado: EstadoTransferencia;
  almacen_origen_id: number;
  almacen_origen: string;
  sucursal_origen: string;
  almacen_destino_id: number;
  almacen_destino: string;
  sucursal_destino: string;
  observaciones: string | null;
  usuario: string | null;
  usuario_recibe: string | null;
  productos: number;
  valor: string | null;
  creado_en: string;
  fecha_envio: string | null;
  fecha_recepcion: string | null;
}

export interface TransferenciaDetalle extends TransferenciaListado {
  puede_recibir: boolean;
  puede_anular: boolean;
  detalles: {
    id: number;
    producto_id: number;
    producto: string;
    lote_id: number | null;
    lote: string | null;
    fecha_vencimiento: string | null;
    cantidad: string;
    cantidad_recibida: string;
    faltante: string;
    motivo_faltante: string | null;
    costo_unitario: string | null;
  }[];
}

export interface FisicoListado {
  id: number;
  numero: string;
  almacen_id: number;
  almacen: string;
  descripcion: string | null;
  estado: EstadoFisico;
  usuario: string | null;
  aprobado_por: string | null;
  total_lineas: number;
  contadas: number;
  con_diferencia: number;
  valor_faltante: string | null;
  valor_sobrante: string | null;
  creado_en: string;
  fecha_envio: string | null;
  fecha_aplicacion: string | null;
}

export interface FisicoLinea {
  id: number;
  producto_id: number;
  producto: string;
  codigo_barras: string | null;
  lote_id: number | null;
  lote: string | null;
  fecha_vencimiento: string | null;
  stock_sistema: string;
  stock_contado: string | null;
  diferencia: string | null;
  costo_unitario: string | null;
  valor_diferencia: string | null;
}

export interface FisicoDetalle extends FisicoListado {
  usuario_id: number;
  categoria_id: number | null;
  motivo_rechazo: string | null;
  puede_aprobar: boolean;
  detalles: FisicoLinea[];
}

export interface ProblemaIntegridad {
  tipo: string;
  producto_id: number | null;
  producto: string | null;
  almacen_id: number | null;
  detalle: string;
}

export interface ReporteIntegridad {
  correcto: boolean;
  revisados: number;
  problemas: ProblemaIntegridad[];
}

export interface StockInicialItem {
  producto_id: number;
  cantidad: string;
  costo_unitario: string;
  numero_lote?: string | null;
  fecha_vencimiento?: string | null;
}
