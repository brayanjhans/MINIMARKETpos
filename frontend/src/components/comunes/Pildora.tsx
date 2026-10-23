import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const TONOS = {
  positivo: "bg-pill-positive-bg text-pill-positive-ink",
  negativo: "bg-pill-negative-bg text-pill-negative-ink",
  aviso: "bg-pill-warning-bg text-pill-warning-ink",
  neutro: "bg-pill-neutral-bg text-pill-neutral-ink",
} as const;

/** Etiqueta pequeña con fondo pastel. Nunca se comprime. */
export function Pildora({
  tono = "neutro",
  className,
  children,
}: {
  tono?: keyof typeof TONOS;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 flex-none items-center rounded-lg px-2.5 text-xs font-bold whitespace-nowrap",
        TONOS[tono],
        className,
      )}
    >
      {children}
    </span>
  );
}

const PUNTOS = {
  positivo: "bg-positive",
  negativo: "bg-destructive",
  aviso: "bg-warning",
  neutro: "bg-muted-foreground/50",
} as const;

/** Estado con un punto de color delante, como en los bocetos ("● Activo", "● Bloqueado 15 min"). */
export function Estado({ tono, children }: { tono: keyof typeof PUNTOS; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 text-[13px] font-semibold whitespace-nowrap",
        tono === "negativo" && "text-destructive",
        tono === "neutro" && "text-muted-foreground",
      )}
    >
      <span aria-hidden className={cn("size-2 flex-none rounded-full", PUNTOS[tono])} />
      {children}
    </span>
  );
}
