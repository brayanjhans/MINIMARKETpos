import { api } from "@/lib/api";
import type { Pagina } from "@/types";
import type {
  Autorizacion,
  CatalogoPos,
  EstadoVenta,
  MetodoPago,
  VentaDetalle,
  VentaEntrada,
  VentaListado,
  VerificacionTicket,
} from "@/types/ventas";

export interface FiltrosVentas {
  sesion_caja_id?: number;
  usuario_id?: number;
  estado?: EstadoVenta;
  metodo?: MetodoPago;
  busqueda?: string;
  desde?: string;
  hasta?: string;
  pagina?: number;
  tamanio?: number;
}

export const ventasService = {
  catalogo: () => api<CatalogoPos>("/ventas/catalogo"),
  resumenHoy: () =>
    api<{
      total: string;
      tickets: number;
      promedio: string | null;
      por_metodo: Record<MetodoPago, string>;
      por_hora: { hora: number; total: string }[];
    }>("/ventas/resumen-hoy"),
  registrar: (datos: VentaEntrada, clave: string) =>
    api<VentaDetalle>("/ventas", { method: "POST", body: datos, idempotencia: clave }),
  listar: (filtros: FiltrosVentas, signal?: AbortSignal) =>
    api<Pagina<VentaListado>>("/ventas", { params: { ...filtros }, signal }),
  obtener: (id: number) => api<VentaDetalle>(`/ventas/${id}`),
  verificar: (texto: string) => api<VerificacionTicket>("/ventas/verificar", { params: { texto } }),
  anular: (id: number, motivo: string, autorizacion: string | null, clave: string) =>
    api<VentaDetalle>(`/ventas/${id}/anular`, { method: "POST", body: { motivo, autorizacion }, idempotencia: clave }),
  autorizar: (username: string, password: string, permiso: string) =>
    api<Autorizacion>("/ventas/autorizar", { method: "POST", body: { username, password, permiso } }),
};
