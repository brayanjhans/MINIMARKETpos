import { api } from "@/lib/api";
import type { AuditoriaItem, Pagina, ResumenAuditoria } from "@/types";

export interface FiltrosAuditoria {
  pagina?: number;
  tamanio?: number;
  modulo?: string;
  accion?: string;
  usuario_id?: number;
  desde?: string;
  hasta?: string;
  orden?: string;
}

export const auditoriaService = {
  resumen: (desde?: string, hasta?: string) =>
    api<ResumenAuditoria>("/auditoria/resumen", { params: { desde, hasta } }),

  listar: (filtros: FiltrosAuditoria, signal?: AbortSignal) =>
    api<Pagina<AuditoriaItem>>("/auditoria", { params: { ...filtros }, signal }),
};
