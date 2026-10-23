import { create } from "zustand";

import type { TokenRespuesta, UsuarioSesion } from "@/types";

/** "sin_conexion": el servidor no respondió al recuperar la sesión (no significa que la sesión sea inválida) */
type EstadoSesion = "verificando" | "autenticado" | "anonimo" | "sin_conexion";

interface AuthState {
  /** El access token vive solo en memoria (nunca en localStorage) para reducir el riesgo ante XSS. */
  accessToken: string | null;
  usuario: UsuarioSesion | null;
  estado: EstadoSesion;
  setSesion: (respuesta: TokenRespuesta) => void;
  limpiar: () => void;
  setEstado: (estado: EstadoSesion) => void;
  tiene: (permiso: string) => boolean;
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  accessToken: null,
  usuario: null,
  estado: "verificando",
  setSesion: (respuesta) =>
    set({ accessToken: respuesta.access_token, usuario: respuesta.usuario, estado: "autenticado" }),
  limpiar: () => set({ accessToken: null, usuario: null, estado: "anonimo" }),
  setEstado: (estado) => set({ estado }),
  tiene: (permiso) => get().usuario?.permisos.includes(permiso) ?? false,
}));
