import { cn } from "@/lib/utils";

/** Marca: la tiendita en un cuadro amarillo. */
export function MarcaSimbolo({ className }: { className?: string }) {
  return (
    <span className={cn("grid size-9 flex-none place-items-center rounded-[11px] bg-amarillo", className)}>
      <svg
        viewBox="0 0 24 24"
        className="size-[55%]"
        fill="none"
        stroke="#14213d"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M3 9l1.5-5h15L21 9" />
        <path d="M4 9v11h16V9" />
        <path d="M3 9h18" />
        <path d="M9 20v-6h6v6" />
      </svg>
    </span>
  );
}

interface Props {
  className?: string;
  /** Línea pequeña bajo el nombre (la sucursal) */
  subtitulo?: string;
  /** Texto blanco para fondos azul noche */
  claro?: boolean;
}

export function Marca({ className, subtitulo, claro }: Props) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <MarcaSimbolo />
      <span className="leading-tight">
        <span className={cn("block text-[17px] font-extrabold tracking-[-0.02em]", claro && "text-white")}>
          Minimarket
        </span>
        {subtitulo && <span className="block text-xs font-semibold text-amarillo">{subtitulo}</span>}
      </span>
    </span>
  );
}
