"use client";

import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError, esSinConexion, MENSAJE_SIN_CONEXION } from "@/lib/api";

/** Un solo aviso de "sin conexión" aunque fallen varias consultas a la vez. */
function avisarSinConexion(error: unknown) {
  if (esSinConexion(error)) toast.error(MENSAJE_SIN_CONEXION, { id: "sin-conexion" });
}

function crearQueryClient() {
  return new QueryClient({
    queryCache: new QueryCache({ onError: avisarSinConexion }),
    mutationCache: new MutationCache({ onError: avisarSinConexion }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        // No reintentar errores de negocio/permisos; sí los de red o servidor (máx. 2 veces)
        retry: (intentos, error) =>
          intentos < 2 && !(error instanceof ApiError && error.status >= 400 && error.status < 500),
      },
      mutations: { retry: false },
    },
  });
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(crearQueryClient);
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider delayDuration={200}>
          {children}
          <Toaster closeButton position="bottom-right" />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
