import { PageHeader } from "@/components/comunes/PageHeader";

interface Props {
  titulo: string;
  fase: number;
  descripcion: string;
  /** Lo que tendrá la pantalla, como lista de lo que se podrá hacer */
  tareas?: string[];
}

/** Pantalla de un módulo que se construye en una fase posterior: dice qué tendrá y cuándo. */
export function Proximamente({ titulo, fase, descripcion, tareas = [] }: Props) {
  return (
    <>
      <PageHeader titulo={titulo} linea={`Se habilita en la fase ${fase} del proyecto.`} />
      <section className="tarjeta max-w-3xl p-6">
        <span className="mb-3 inline-flex h-7 items-center rounded-lg bg-amarillo-suave px-2.5 text-xs font-bold text-amarillo-tinta">
          Fase {fase}
        </span>
        <p className="text-[15px] leading-6 font-semibold">{descripcion}</p>
        {tareas.length > 0 && (
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            {tareas.map((t) => (
              <li key={t} className="flex gap-2">
                <span aria-hidden className="mt-2 size-1 flex-none rounded-full bg-muted-foreground" />
                {t}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
