// Reflejan app/schemas/productos.py e inventario.py (los decimales llegan como texto: "12.500")

export type UnidadMedida = "UNIDAD" | "KILOGRAMO" | "GRAMO" | "LITRO" | "MILILITRO" | "PAQUETE" | "CAJA" | "DOCENA";
export type AfectacionIGV = "GRAVADO" | "EXONERADO" | "INAFECTO";
export type EstadoStock = "normal" | "bajo" | "sin_stock" | "negativo" | "por_regularizar";

export const UNIDADES: { valor: UnidadMedida; etiqueta: string; corta: string }[] = [
  { valor: "UNIDAD", etiqueta: "Unidad", corta: "und" },
  { valor: "KILOGRAMO", etiqueta: "Kilogramo", corta: "kg" },
  { valor: "GRAMO", etiqueta: "Gramo", corta: "g" },
  { valor: "LITRO", etiqueta: "Litro", corta: "L" },
  { valor: "MILILITRO", etiqueta: "Mililitro", corta: "ml" },
  { valor: "PAQUETE", etiqueta: "Paquete", corta: "paq" },
  { valor: "CAJA", etiqueta: "Caja", corta: "caja" },
  { valor: "DOCENA", etiqueta: "Docena", corta: "doc" },
];

export interface CategoriaResumen {
  id: number;
  nombre: string;
  color: string | null;
}

export interface Categoria extends CategoriaResumen {
  descripcion: string | null;
  activo: boolean;
  productos: number;
  valor_inventario: string;
}

export interface Marca {
  id: number;
  nombre: string;
  activo: boolean;
  productos: number;
}

export interface Presentacion {
  id: number;
  nombre: string;
  factor: string;
  precio_venta: string;
  activo: boolean;
  codigos: string[];
}

export interface StockEnAlmacen {
  almacen_id: number;
  almacen: string;
  sucursal_id: number;
  sucursal: string;
  cantidad: string;
  pendiente_lote: string;
  stock_minimo: string;
}

export interface ProductoListado {
  id: number;
  nombre: string;
  codigo_interno: string | null;
  codigo_barras: string | null;
  categoria: CategoriaResumen | null;
  marca: { id: number; nombre: string } | null;
  unidad_medida: UnidadMedida;
  precio_venta: string;
  precio_costo: string | null;
  margen: string | null;
  stock: string;
  stock_minimo: string;
  estado_stock: EstadoStock;
  maneja_lotes: boolean;
  permite_decimales: boolean;
  imagen_url: string | null;
  miniatura_url: string | null;
  activo: boolean;
}

export interface ProductoDetalle extends ProductoListado {
  descripcion: string | null;
  codigos: string[];
  presentaciones: Presentacion[];
  tipo_afectacion_igv: AfectacionIGV;
  afecto_icbper: boolean;
  version: number;
  tiene_movimientos: boolean;
  stock_por_almacen: StockEnAlmacen[];
  creado_en: string;
  actualizado_en: string;
}

export interface PresentacionEntrada {
  id?: number | null;
  nombre: string;
  factor: string;
  precio_venta: string;
  codigos: string[];
  activo?: boolean;
}

export interface ProductoEntrada {
  nombre: string;
  descripcion?: string | null;
  codigo_interno?: string | null;
  codigos: string[];
  categoria_id: number | null;
  marca_id: number | null;
  unidad_medida: UnidadMedida;
  precio_venta: string;
  precio_costo?: string;
  stock_minimo: string;
  tipo_afectacion_igv: AfectacionIGV;
  afecto_icbper: boolean;
  maneja_lotes: boolean;
  permite_decimales: boolean;
  presentaciones: PresentacionEntrada[];
  activo?: boolean;
}

export interface ResumenProductos {
  total: number;
  activos: number;
  inactivos: number;
  stock_bajo: number;
  sin_stock: number;
  negativos: number;
  sin_codigo: number;
}

export interface HistorialPrecio {
  id: number;
  tipo: "COSTO" | "VENTA";
  presentacion_id: number | null;
  precio_anterior: string;
  precio_nuevo: string;
  origen: string;
  usuario: string | null;
  creado_en: string;
}

export interface FilaImportacion {
  fila: number;
  nombre: string | null;
  codigo_barras: string | null;
  precio_venta: string | null;
  precio_anterior: string | null;
  stock_inicial: string | null;
  accion: "nuevo" | "actualiza" | "sin_cambios" | "error";
  errores: string[];
}

export interface VistaImportacion {
  total: number;
  nuevos: number;
  actualizan: number;
  sin_cambios: number;
  errores: number;
  con_stock: number;
  filas: FilaImportacion[];
}

export interface ResultadoImportacion {
  creados: number;
  actualizados: number;
  omitidos: number;
  con_stock: number;
  valor_stock: string;
  repetida: boolean;
}
