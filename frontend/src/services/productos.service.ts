import { api, descargar } from "@/lib/api";
import type { Mensaje, Pagina } from "@/types";
import type {
  HistorialPrecio,
  Presentacion,
  ProductoDetalle,
  ProductoEntrada,
  ProductoListado,
  ResultadoImportacion,
  ResumenProductos,
  VistaImportacion,
} from "@/types/productos";

export interface FiltrosProductos {
  pagina?: number;
  tamanio?: number;
  busqueda?: string;
  categoria_id?: number;
  marca_id?: number;
  activo?: boolean | null;
  estado?: "bajo" | "sin_stock" | "negativo" | "sin_codigo";
  orden?: string;
}

function archivo(file: File): FormData {
  const datos = new FormData();
  datos.append("archivo", file);
  return datos;
}

export const productosService = {
  listar: (filtros: FiltrosProductos, signal?: AbortSignal) =>
    api<Pagina<ProductoListado>>("/productos", {
      // activo=null significa "todos": no se envía el filtro
      params: { ...filtros, activo: filtros.activo === null ? undefined : (filtros.activo ?? true) },
      signal,
    }),

  resumen: () => api<ResumenProductos>("/productos/resumen"),

  obtener: (id: number) => api<ProductoDetalle>(`/productos/${id}`),

  porCodigo: (codigo: string) =>
    api<{ producto: ProductoListado; presentacion: Presentacion | null }>(
      `/productos/codigo/${encodeURIComponent(codigo.trim())}`,
    ),

  historialPrecios: (id: number) => api<HistorialPrecio[]>(`/productos/${id}/historial-precios`),

  crear: (datos: ProductoEntrada) => api<ProductoDetalle>("/productos", { method: "POST", body: datos }),

  actualizar: (id: number, datos: Partial<ProductoEntrada> & { version: number }) =>
    api<ProductoDetalle>(`/productos/${id}`, { method: "PATCH", body: datos }),

  eliminar: (id: number) => api<Mensaje>(`/productos/${id}`, { method: "DELETE" }),

  subirImagen: (id: number, file: File) =>
    api<ProductoDetalle>(`/productos/${id}/imagen`, { method: "PUT", body: archivo(file) }),

  quitarImagen: (id: number) => api<ProductoDetalle>(`/productos/${id}/imagen`, { method: "DELETE" }),

  plantilla: () => descargar("/productos/plantilla", undefined, "plantilla_productos.xlsx"),

  exportar: (activo?: boolean) => descargar("/productos/exportar", { activo }, "productos.xlsx"),

  vistaPrevia: (file: File) =>
    api<VistaImportacion>("/productos/importar/vista-previa", { method: "POST", body: archivo(file) }),

  importar: (file: File, clave: string) =>
    api<ResultadoImportacion>("/productos/importar", { method: "POST", body: archivo(file), idempotencia: clave }),
};
