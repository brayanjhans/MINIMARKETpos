import { pastelPorId } from "@/lib/colores";
import { cn, iniciales } from "@/lib/utils";

interface Props {
  id: number;
  nombre: string;
  className?: string;
  /** Clases de color propias (por ejemplo, el color del rol); si no, uno estable por persona */
  color?: string;
}

/** Iniciales de una persona en un cuadro redondeado de color pastel. */
export function Inicial({ id, nombre, className, color }: Props) {
  return (
    <span
      aria-hidden
      className={cn(
        "grid size-9 flex-none place-items-center rounded-[12px] text-xs font-extrabold",
        color ?? pastelPorId(id),
        className,
      )}
    >
      {iniciales(nombre)}
    </span>
  );
}
