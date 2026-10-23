import type { ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface Props {
  etiqueta: string;
  valor: ReactNode | undefined;
  detalle?: ReactNode;
  /** Tarjeta azul noche (el dato principal de la pantalla) */
  oscuro?: boolean;
  /** Tarjeta amarilla pálida (algo que requiere atención pronto) */
  aviso?: boolean;
  /** El número va en rojo */
  alerta?: boolean;
  onClick?: () => void;
  className?: string;
}

/** Tarjeta con un número grande: los contadores de cabecera del estilo Bodega. */
export function Indicador({ etiqueta, valor, detalle, oscuro, aviso, alerta, onClick, className }: Props) {
  const Contenedor = onClick ? "button" : "div";
  return (
    <Contenedor
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={cn(
        "tarjeta flex flex-col items-start px-[18px] py-4 text-left",
        oscuro && "bg-navy text-white dark:bg-navy-2",
        aviso && "bg-aviso-fondo",
        onClick && "transition-shadow hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
        className,
      )}
    >
      <span
        className={cn(
          "text-[13px] font-medium",
          oscuro ? "text-navy-ink" : aviso ? "font-semibold text-amarillo-tinta" : "text-muted-foreground",
        )}
      >
        {etiqueta}
      </span>
      {valor === undefined ? (
        <Skeleton className="mt-1.5 h-8 w-16" />
      ) : (
        <span className={cn("text-[26px] leading-9 font-extrabold tracking-[-0.02em] tabular", alerta && "text-destructive")}>
          {valor}
        </span>
      )}
      {detalle && (
        <span className={cn("text-xs", oscuro ? "text-navy-ink" : aviso ? "text-amarillo-tinta" : "text-muted-foreground")}>
          {detalle}
        </span>
      )}
    </Contenedor>
  );
}
