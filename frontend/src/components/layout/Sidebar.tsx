"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Marca, MarcaSimbolo } from "@/components/comunes/Marca";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/useAuth";
import { NAVEGACION } from "@/lib/navegacion";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/uiStore";

interface Props {
  /** En el celular el menú vive dentro de un panel y nunca se colapsa */
  movil?: boolean;
  alNavegar?: () => void;
}

/** Menú lateral azul noche; el ítem activo va en amarillo (estilo Bodega). */
export function Sidebar({ movil = false, alNavegar }: Props) {
  const pathname = usePathname();
  const { tiene, usuario } = useAuth();
  const colapsadoPreferido = useUIStore((s) => s.sidebarColapsado);
  const alternar = useUIStore((s) => s.alternarSidebar);
  const colapsado = !movil && colapsadoPreferido;

  const grupos = NAVEGACION.map((g) => ({ ...g, items: g.items.filter((i) => tiene(i.permiso)) })).filter(
    (g) => g.items.length > 0,
  );

  return (
    <aside
      className={cn(
        "flex h-full flex-col bg-navy py-5 text-navy-ink transition-[width] duration-200",
        movil ? "w-full px-3.5" : colapsado ? "w-[76px] px-3" : "w-[236px] px-3.5",
      )}
    >
      <div className={cn("mb-2 flex h-11 items-center", colapsado ? "justify-center" : "px-2")}>
        {colapsado ? (
          <MarcaSimbolo />
        ) : (
          <Marca claro subtitulo={usuario ? `Sucursal ${usuario.sucursal_actual.nombre}` : undefined} />
        )}
      </div>

      <nav className="scrollbar-fino -mx-1 flex-1 overflow-y-auto px-1" aria-label="Menú principal">
        {grupos.map((grupo) => (
          <div key={grupo.titulo} className="mt-3 first:mt-1">
            {colapsado ? (
              <div className="mx-auto mb-2 h-px w-6 bg-navy-2" />
            ) : (
              <p className="px-3.5 pb-1 text-[11px] font-bold tracking-wide text-[#6f7ea3] uppercase">
                {grupo.titulo}
              </p>
            )}
            <ul className="space-y-0.5">
              {grupo.items.map((item) => {
                const activo = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const enlace = (
                  <Link
                    href={item.href}
                    onClick={alNavegar}
                    aria-current={activo ? "page" : undefined}
                    aria-label={colapsado ? item.titulo : undefined}
                    className={cn(
                      "flex h-[38px] items-center gap-3 rounded-[12px] px-3.5 text-sm font-medium outline-none",
                      "transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-amarillo",
                      activo ? "bg-amarillo font-bold text-[#14213d]" : "hover:bg-navy-2 hover:text-white",
                      colapsado && "justify-center px-0",
                    )}
                  >
                    <item.icono className="size-[18px] shrink-0" strokeWidth={2} aria-hidden />
                    {!colapsado && <span className="truncate">{item.titulo}</span>}
                  </Link>
                );
                return (
                  <li key={item.href}>
                    {colapsado ? (
                      <Tooltip>
                        <TooltipTrigger asChild>{enlace}</TooltipTrigger>
                        <TooltipContent side="right">{item.titulo}</TooltipContent>
                      </Tooltip>
                    ) : (
                      enlace
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {!movil && (
        <button
          type="button"
          onClick={alternar}
          className={cn(
            "mt-2 flex h-9 items-center gap-3 rounded-[12px] px-3.5 text-[13px] font-medium",
            "transition-colors hover:bg-navy-2 hover:text-white focus-visible:ring-2 focus-visible:ring-amarillo focus-visible:outline-none",
            colapsado && "justify-center px-0",
          )}
          aria-label={colapsado ? "Mostrar el menú completo" : "Contraer el menú"}
        >
          {colapsado ? <PanelLeftOpen className="size-[18px]" /> : <PanelLeftClose className="size-[18px]" />}
          {!colapsado && "Contraer menú"}
        </button>
      )}
    </aside>
  );
}
