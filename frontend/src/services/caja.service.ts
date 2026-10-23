import { api } from "@/lib/api";
import type { Pagina } from "@/types";
import type { CajaFila, EstadoCaja, EstadoSesion, MetodoPago, Sesion, SesionDetalle } from "@/types/ventas";

export interface CierreEntrada {
  arqueo: { denominacion: string; cantidad: number }[];
  declarados: { metodo: MetodoPago; monto: string }[];
  observaciones?: string | null;
}

export const cajaService = {
  cajas: () => api<CajaFila[]>("/caja/cajas"),
  actual: () => api<EstadoCaja>("/caja/actual"),
  abrir: (datos: { caja_id: number; monto_inicial: string; observaciones?: string | null }, clave: string) =>
    api<SesionDetalle>("/caja/abrir", { method: "POST", body: datos, idempotencia: clave }),
  movimiento: (datos: { tipo: "INGRESO" | "EGRESO"; monto: string; concepto: string }, clave: string) =>
    api<SesionDetalle>("/caja/movimientos", { method: "POST", body: datos, idempotencia: clave }),
  cerrar: (id: number, datos: CierreEntrada, clave: string) =>
    api<SesionDetalle>(`/caja/sesiones/${id}/cerrar`, { method: "POST", body: datos, idempotencia: clave }),
  sesiones: (params: {
    usuario_id?: number;
    estado?: EstadoSesion;
    desde?: string;
    hasta?: string;
    pagina?: number;
    tamanio?: number;
  }) => api<Pagina<Sesion>>("/caja/sesiones", { params }),
  sesion: (id: number) => api<SesionDetalle>(`/caja/sesiones/${id}`),
  cajeros: () => api<{ id: number; nombre: string; turnos: number }[]>("/caja/cajeros"),
};
