"use client";

import type { ReactNode } from "react";

import { useAuth } from "@/hooks/useAuth";

/** Muestra el contenido solo si el usuario tiene el permiso (el backend lo valida igualmente). */
export function RequierePermiso({ permiso, children }: { permiso: string; children: ReactNode }) {
  const { tiene } = useAuth();
  if (tiene(permiso)) return <>{children}</>;
  return (
    <section className="tarjeta max-w-xl p-6">
      <h1 className="text-base font-semibold">Esta sección no está en su rol</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Si la necesita para su trabajo, pida a un administrador que agregue el permiso a su rol.
      </p>
    </section>
  );
}
