import { api } from "@/lib/api";
import type { Mensaje, Pagina, ResumenUsuarios, UsuarioActualizar, UsuarioCrear, UsuarioDetalle, UsuarioListado } from "@/types";

export interface FiltrosUsuarios {
  pagina?: number;
  tamanio?: number;
  busqueda?: string;
  rol_id?: number;
  activo?: boolean;
  sucursal_id?: number;
  orden?: string;
}

export const usuariosService = {
  listar: (filtros: FiltrosUsuarios, signal?: AbortSignal) =>
    api<Pagina<UsuarioListado>>("/usuarios", { params: { ...filtros }, signal }),

  resumen: () => api<ResumenUsuarios>("/usuarios/resumen"),

  obtener: (id: number) => api<UsuarioDetalle>(`/usuarios/${id}`),

  crear: (datos: UsuarioCrear) => api<UsuarioDetalle>("/usuarios", { method: "POST", body: datos }),

  actualizar: (id: number, datos: UsuarioActualizar) =>
    api<UsuarioDetalle>(`/usuarios/${id}`, { method: "PATCH", body: datos }),

  restablecerPassword: (id: number, password: string, debe_cambiar_password = true) =>
    api<Mensaje>(`/usuarios/${id}/restablecer-password`, {
      method: "POST",
      body: { password, debe_cambiar_password },
    }),

  desbloquear: (id: number) => api<UsuarioDetalle>(`/usuarios/${id}/desbloquear`, { method: "POST" }),

  cerrarSesiones: (id: number) => api<Mensaje>(`/usuarios/${id}/cerrar-sesiones`, { method: "POST" }),
};
