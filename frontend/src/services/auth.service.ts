import { api } from "@/lib/api";
import type { Mensaje, TokenRespuesta, UsuarioSesion } from "@/types";

export const authService = {
  login: (username: string, password: string) =>
    api<TokenRespuesta>("/auth/login", { method: "POST", body: { username, password }, autenticado: false }),

  logout: () => api<Mensaje>("/auth/logout", { method: "POST", autenticado: false }),

  me: () => api<UsuarioSesion>("/auth/me"),

  cambiarSucursal: (sucursal_id: number) =>
    api<TokenRespuesta>("/auth/cambiar-sucursal", { method: "POST", body: { sucursal_id } }),

  cambiarPassword: (password_actual: string, password_nueva: string) =>
    api<TokenRespuesta>("/auth/cambiar-password", { method: "POST", body: { password_actual, password_nueva } }),
};
