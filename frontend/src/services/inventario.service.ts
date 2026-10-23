import { api } from "@/lib/api";
import type { Pagina } from "@/types";
import type {
  AjusteDetalle,
  AjusteDetalleEntrada,
  AjusteListado,
  Almacen,
  EstadoDocumento,
  EstadoFisico,
  EstadoTransferencia,
  FisicoDetalle,
  FisicoListado,
  Lote,
  MotivoAjuste,
  Movimiento,
  ReporteIntegridad,
  ResumenInventario,
  StockFila,
  StockInicialItem,
  TipoMovimiento,
  TransferenciaDetalle,
  TransferenciaListado,
} from "@/types/inventario";

export interface FiltrosStock {
  almacen_id?: number;
  pagina?: number;
  tamanio?: number;
  busqueda?: string;
  categoria_id?: number;
  estado?: "bajo" | "sin_stock" | "con_stock" | "por_regularizar";
  orden?: string;
}

export interface FiltrosKardex {
  almacen_id?: number;
  producto_id?: number;
  tipo?: TipoMovimiento;
  desde?: string;
  hasta?: string;
  pagina?: number;
  tamanio?: number;
}

const ajuste = (id: number, accion: string, body?: unknown) =>
  api<AjusteDetalle>(`/inventario/ajustes/${id}/${accion}`, { method: "POST", body });
const transferencia = (id: number, accion: string, body?: unknown) =>
  api<TransferenciaDetalle>(`/inventario/transferencias/${id}/${accion}`, { method: "POST", body });
const fisico = (id: number, accion: string, body?: unknown) =>
  api<FisicoDetalle>(`/inventario/fisicos/${id}/${accion}`, { method: "POST", body });

export const inventarioService = {
  almacenes: () => api<Almacen[]>("/inventario/almacenes"),
  resumen: (almacen_id?: number) => api<ResumenInventario>("/inventario/resumen", { params: { almacen_id } }),
  stock: (filtros: FiltrosStock, signal?: AbortSignal) =>
    api<Pagina<StockFila>>("/inventario/stock", { params: { ...filtros }, signal }),
  lotes: (params: { almacen_id?: number; producto_id?: number; por_vencer_dias?: number; vencidos?: boolean }) =>
    api<Lote[]>("/inventario/lotes", { params }),
  kardex: (filtros: FiltrosKardex, signal?: AbortSignal) =>
    api<Pagina<Movimiento>>("/inventario/kardex", { params: { ...filtros }, signal }),
  integridad: () => api<ReporteIntegridad>("/inventario/integridad"),
  motivos: () => api<MotivoAjuste[]>("/inventario/motivos-ajuste"),

  stockInicial: (items: StockInicialItem[], clave: string, almacen_id?: number) =>
    api<{ productos: number; unidades: string; valor: string }>("/inventario/stock-inicial", {
      method: "POST",
      body: { almacen_id, items },
      idempotencia: clave,
    }),

  ajustes: (params: { almacen_id?: number; estado?: EstadoDocumento; pagina?: number; tamanio?: number }) =>
    api<Pagina<AjusteListado>>("/inventario/ajustes", { params }),
  ajuste: (id: number) => api<AjusteDetalle>(`/inventario/ajustes/${id}`),
  crearAjuste: (
    datos: { motivo_id: number; observaciones?: string | null; detalles: AjusteDetalleEntrada[]; enviar: boolean },
    clave: string,
  ) => api<AjusteDetalle>("/inventario/ajustes", { method: "POST", body: datos, idempotencia: clave }),
  aprobarAjuste: (id: number) => ajuste(id, "aprobar"),
  rechazarAjuste: (id: number, motivo: string) => ajuste(id, "rechazar", { motivo }),
  anularAjuste: (id: number) => ajuste(id, "anular"),
  enviarAjuste: (id: number) => ajuste(id, "enviar"),

  transferencias: (params: { estado?: EstadoTransferencia; pagina?: number; tamanio?: number }) =>
    api<Pagina<TransferenciaListado>>("/inventario/transferencias", { params }),
  transferencia: (id: number) => api<TransferenciaDetalle>(`/inventario/transferencias/${id}`),
  crearTransferencia: (
    datos: {
      almacen_destino_id: number;
      observaciones?: string | null;
      detalles: { producto_id: number; cantidad: string; lote_id?: number | null }[];
    },
    clave: string,
  ) =>
    api<TransferenciaDetalle>("/inventario/transferencias", {
      method: "POST",
      body: { ...datos, enviar: true },
      idempotencia: clave,
    }),
  recibirTransferencia: (
    id: number,
    detalles: { detalle_id: number; cantidad_recibida: string; motivo_faltante?: string | null }[],
  ) => transferencia(id, "recibir", { detalles }),
  anularTransferencia: (id: number) => transferencia(id, "anular"),

  fisicos: (params: { almacen_id?: number; estado?: EstadoFisico; pagina?: number; tamanio?: number }) =>
    api<Pagina<FisicoListado>>("/inventario/fisicos", { params }),
  fisico: (id: number) => api<FisicoDetalle>(`/inventario/fisicos/${id}`),
  crearFisico: (
    datos: { descripcion?: string | null; categoria_id?: number | null; producto_ids?: number[] | null },
    clave: string,
  ) => api<FisicoDetalle>("/inventario/fisicos", { method: "POST", body: datos, idempotencia: clave }),
  guardarConteo: (id: number, items: { detalle_id: number; stock_contado: string | null }[]) =>
    api<FisicoDetalle>(`/inventario/fisicos/${id}/conteos`, { method: "PUT", body: { items } }),
  enviarFisico: (id: number) => fisico(id, "enviar"),
  aprobarFisico: (id: number) => fisico(id, "aprobar"),
  rechazarFisico: (id: number, motivo: string) => fisico(id, "rechazar", { motivo }),
  cancelarFisico: (id: number) => fisico(id, "cancelar"),
};
