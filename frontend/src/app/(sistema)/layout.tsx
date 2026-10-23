"use client";

import { WifiOff } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { CambiarPasswordDialog } from "@/components/auth/CambiarPasswordDialog";
import { MarcaSimbolo } from "@/components/comunes/Marca";
import { PantallaAviso } from "@/components/comunes/PantallaAviso";
import { Button } from "@/components/ui/button";
import { BarraInferior } from "@/components/layout/BarraInferior";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { renovarSesion } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function SistemaLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const estado = useAuthStore((s) => s.estado);
  const accessToken = useAuthStore((s) => s.accessToken);
  const debeCambiar = useAuthStore((s) => s.usuario?.debe_cambiar_password ?? false);
  const setEstado = useAuthStore((s) => s.setEstado);

  // Al recargar la página el access token (en memoria) se pierde: se recupera con la cookie de sesión
  useEffect(() => {
    if (!accessToken && estado === "verificando") void renovarSesion();
  }, [accessToken, estado]);

  useEffect(() => {
    if (estado === "anonimo") {
      const siguiente = pathname !== "/dashboard" ? `?siguiente=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${siguiente}`);
    }
  }, [estado, pathname, router]);

  if (estado === "sin_conexion") {
    return (
      <PantallaAviso
        icono={WifiOff}
        titulo="Sin conexión con el servidor"
        mensaje="Tu sesión sigue activa. Revisa que el sistema esté encendido y vuelve a intentar."
        acciones={<Button onClick={() => setEstado("verificando")}>Reintentar</Button>}
      />
    );
  }

  if (estado !== "autenticado") {
    return (
      <div className="grid h-dvh place-items-center bg-navy">
        <div className="flex flex-col items-center gap-3 text-sm font-semibold text-navy-ink">
          <MarcaSimbolo className="size-12 animate-pulse rounded-[14px]" />
          Abriendo tu sesión…
        </div>
      </div>
    );
  }

  // El punto de venta ocupa toda la pantalla (tiene su propia barra con la caja y los atajos)
  if (pathname === "/pos") {
    return (
      <>
        {children}
        <CambiarPasswordDialog abierto={debeCambiar} onCambiar={() => undefined} obligatorio />
      </>
    );
  }

  return (
    <div className="flex h-dvh overflow-hidden">
      <div className="hidden lg:block">
        <Sidebar />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="scrollbar-fino flex-1 overflow-y-auto">
          <div className="w-full px-4 pt-1 pb-28 md:px-7 lg:pb-10">{children}</div>
        </main>
      </div>
      <BarraInferior />
      <CambiarPasswordDialog abierto={debeCambiar} onCambiar={() => undefined} obligatorio />
    </div>
  );
}
