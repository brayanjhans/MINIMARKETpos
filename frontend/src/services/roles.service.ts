import { api } from "@/lib/api";
import type { Mensaje, ModuloPermisos, RolDetalle, RolListado } from "@/types";

export interface RolEntrada {
  nombre?: string;
  descripcion?: string | null;
  activo?: boolean;
  permisos?: string[];
}

export const rolesService = {
  listar: () => api<RolListado[]>("/roles"),
  catalogoPermisos: () => api<ModuloPermisos[]>("/roles/permisos"),
  obtener: (id: number) => api<RolDetalle>(`/roles/${id}`),
  crear: (datos: RolEntrada) => api<RolDetalle>("/roles", { method: "POST", body: datos }),
  actualizar: (id: number, datos: RolEntrada) => api<RolDetalle>(`/roles/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) => api<Mensaje>(`/roles/${id}`, { method: "DELETE" }),
};
