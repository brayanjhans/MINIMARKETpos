"use client";

import { cn } from "@/lib/utils";

interface Props<T extends string> {
  opciones: { valor: T; etiqueta: string; cantidad?: number }[];
  valor: T;
  onCambiar: (valor: T) => void;
  etiqueta: string;
}

/** Filtros en forma de chips: el elegido va en azul noche (estilo Bodega). */
export function Pestanas<T extends string>({ opciones, valor, onCambiar, etiqueta }: Props<T>) {
  return (
    <div role="tablist" aria-label={etiqueta} className="flex flex-wrap gap-2">
      {opciones.map((o) => {
        const activa = o.valor === valor;
        return (
          <button
            key={o.valor}
            role="tab"
            type="button"
            aria-selected={activa}
            onClick={() => onCambiar(o.valor)}
            className={cn(
              "inline-flex h-[34px] items-center gap-1.5 rounded-[10px] px-3 text-[13px] font-semibold transition-colors",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
              activa ? "bg-navy font-bold text-white dark:bg-secondary dark:text-secondary-foreground" : "bg-muted hover:bg-accent",
            )}
          >
            {o.etiqueta}
            {o.cantidad !== undefined && <span className={cn("tabular", !activa && "text-muted-foreground")}>{o.cantidad}</span>}
          </button>
        );
      })}
    </div>
  );
}
