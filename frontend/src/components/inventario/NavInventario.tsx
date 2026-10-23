"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const SECCIONES = [
  { href: "/inventario", texto: "Stock", permiso: "inventario.ver" },
  { href: "/inventario/kardex", texto: "Kardex", permiso: "inventario.kardex" },
  { href: "/inventario/ajustes", texto: "Ajustes y mermas", permiso: "inventario.ver" },
  { href: "/inventario/transferencias", texto: "Transferencias", permiso: "inventario.ver" },
  { href: "/inventario/fisicos", texto: "Inventario físico", permiso: "inventario.ver" },
  { href: "/inventario/stock-inicial", texto: "Stock inicial", permiso: "inventario.stock_inicial" },
];

/** Secciones de inventario como chips (la elegida en azul noche). */
export function NavInventario({ pendientes }: { pendientes?: number }) {
  const { tiene } = useAuth();
  const ruta = usePathname();
  return (
    <nav aria-label="Secciones de inventario" className="scrollbar-fino -mx-1 mb-4 flex gap-2 overflow-x-auto px-1 pb-1">
      {SECCIONES.filter((s) => tiene(s.permiso)).map((s) => {
        const activa = s.href === "/inventario" ? ruta === s.href : ruta.startsWith(s.href);
        return (
          <Link
            key={s.href}
            href={s.href}
            aria-current={activa ? "page" : undefined}
            className={cn(
              "inline-flex h-[34px] flex-none items-center gap-1.5 rounded-[10px] px-3 text-[13px] font-semibold transition-colors",
              activa ? "bg-navy font-bold text-white dark:bg-secondary dark:text-secondary-foreground" : "bg-card hover:bg-accent",
            )}
          >
            {s.texto}
            {s.href === "/inventario/ajustes" && !!pendientes && (
              <span className="grid h-5 min-w-5 place-items-center rounded-full bg-primary px-1.5 text-[11px] font-extrabold text-primary-foreground tabular">
                {pendientes}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
