"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/authStore";

/** Acceso a la sesión actual y acciones de autenticación. */
export function useAuth() {
  const usuario = useAuthStore((s) => s.usuario);
  const estado = useAuthStore((s) => s.estado);
  const setSesion = useAuthStore((s) => s.setSesion);
  const limpiar = useAuthStore((s) => s.limpiar);
  const queryClient = useQueryClient();
  const router = useRouter();

  const tiene = useCallback((permiso: string) => usuario?.permisos.includes(permiso) ?? false, [usuario]);

  const login = useCallback(
    async (username: string, password: string) => {
      const respuesta = await authService.login(username, password);
      setSesion(respuesta);
      return respuesta;
    },
    [setSesion],
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      limpiar();
      queryClient.clear();
      router.replace("/login");
    }
  }, [limpiar, queryClient, router]);

  const cambiarSucursal = useCallback(
    async (sucursalId: number) => {
      const respuesta = await authService.cambiarSucursal(sucursalId);
      setSesion(respuesta);
      // Todos los datos dependen de la sucursal: se recargan
      await queryClient.invalidateQueries();
      return respuesta;
    },
    [setSesion, queryClient],
  );

  return { usuario, estado, tiene, login, logout, cambiarSucursal };
}
