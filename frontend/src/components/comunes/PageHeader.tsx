import type { ReactNode } from "react";

interface Props {
  titulo: string;
  /** Una línea bajo el título: de qué trata la pantalla o el dato del momento */
  linea?: ReactNode;
  acciones?: ReactNode;
}

export function PageHeader({ titulo, linea, acciones }: Props) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-[26px] leading-8 font-extrabold tracking-[-0.02em]">{titulo}</h1>
        {linea && <p className="mt-0.5 text-sm text-muted-foreground">{linea}</p>}
      </div>
      {acciones && <div className="flex shrink-0 flex-wrap items-center gap-2">{acciones}</div>}
    </div>
  );
}
