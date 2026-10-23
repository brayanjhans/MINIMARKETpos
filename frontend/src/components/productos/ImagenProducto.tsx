import { pastelPorId } from "@/lib/colores";
import { cn, iniciales } from "@/lib/utils";

interface Props {
  id: number;
  nombre: string;
  /** Miniatura WEBP (~8 KB); si no hay, se muestran las iniciales */
  url: string | null | undefined;
  className?: string;
}

/** Foto pequeña del producto (carga diferida) o sus iniciales en un cuadro pastel. */
export function ImagenProducto({ id, nombre, url, className }: Props) {
  if (url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- ya es un WEBP de 160 px servido con caché larga
      <img
        src={url}
        alt=""
        loading="lazy"
        decoding="async"
        width={40}
        height={40}
        className={cn("size-10 flex-none rounded-[12px] bg-muted object-cover", className)}
      />
    );
  }
  return (
    <span
      aria-hidden
      className={cn(
        "grid size-10 flex-none place-items-center rounded-[12px] text-xs font-extrabold",
        pastelPorId(id),
        className,
      )}
    >
      {iniciales(nombre)}
    </span>
  );
}
