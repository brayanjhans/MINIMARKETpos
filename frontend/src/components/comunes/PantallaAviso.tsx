import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { MarcaSimbolo } from "@/components/comunes/Marca";

interface Props {
  icono: LucideIcon;
  titulo: string;
  mensaje: ReactNode;
  acciones?: ReactNode;
  /** Código o número grande decorativo (ej. "404") */
  codigo?: string;
}

/** Pantalla completa para estados excepcionales: sin conexión, página inexistente, error inesperado. */
export function PantallaAviso({ icono: Icono, titulo, mensaje, acciones, codigo }: Props) {
  return (
    <div className="grid min-h-dvh place-items-center bg-background p-5">
      <div className="tarjeta w-full max-w-md p-8 text-center sm:p-10">
        <MarcaSimbolo className="mx-auto mb-6" />
        {codigo && <p className="text-6xl font-extrabold tracking-[-0.04em] text-amarillo">{codigo}</p>}
        <span className="mx-auto mt-2 grid size-12 place-items-center rounded-[14px] bg-muted">
          <Icono className="size-6 text-muted-foreground" aria-hidden />
        </span>
        <h1 className="mt-4 text-[22px] leading-7 font-extrabold tracking-[-0.02em]">{titulo}</h1>
        <div className="mt-2 text-[15px] leading-relaxed text-muted-foreground">{mensaje}</div>
        {acciones && <div className="mt-6 flex flex-wrap justify-center gap-2">{acciones}</div>}
      </div>
    </div>
  );
}
