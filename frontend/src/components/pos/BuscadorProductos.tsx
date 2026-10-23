"use client";

import { Barcode } from "lucide-react";
import { forwardRef, useImperativeHandle, useMemo, useRef, useState } from "react";

import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { cantidad as fmt, unidadCorta } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import type { PresentacionPos, ProductoPos } from "@/types/ventas";

export interface Opcion {
  producto: ProductoPos;
  presentacion: PresentacionPos | null;
}

export interface BuscadorHandle {
  enfocar: () => void;
}

interface Props {
  productos: ProductoPos[];
  onAgregar: (opcion: Opcion, cantidad: string) => void;
  onNoEncontrado: (codigo: string) => void;
}

const normalizar = (t: string) =>
  t
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
// "3*7750..." o "3 x coca": cantidad antes del código o del nombre
const CANTIDAD = /^(\d{1,4}(?:[.,]\d{1,3})?)\s*[*x×]\s*(.+)$/i;
const MAX_RESULTADOS = 24;

/**
 * Buscador del POS: todo en memoria, sin esperar al servidor. Un código exacto (lector USB + Enter) agrega el
 * producto o la presentación; si no, filtra por nombre/categoría y Enter agrega la opción resaltada.
 */
export const BuscadorProductos = forwardRef<BuscadorHandle, Props>(function BuscadorProductos(
  { productos, onAgregar, onNoEncontrado },
  ref,
) {
  const [texto, setTexto] = useState("");
  const [categoria, setCategoria] = useState<number | null>(null);
  const [activo, setActivo] = useState(0);
  const entrada = useRef<HTMLInputElement>(null);
  useImperativeHandle(ref, () => ({ enfocar: () => entrada.current?.focus() }));

  const { porCodigo, indice, categorias } = useMemo(() => {
    const porCodigo = new Map<string, Opcion>();
    const categorias = new Map<number, { nombre: string; color: string | null; n: number }>();
    for (const p of productos) {
      for (const c of p.codigos) porCodigo.set(c.toUpperCase(), { producto: p, presentacion: null });
      if (p.codigo_interno) porCodigo.set(p.codigo_interno.toUpperCase(), { producto: p, presentacion: null });
      for (const pr of p.presentaciones)
        for (const c of pr.codigos) porCodigo.set(c.toUpperCase(), { producto: p, presentacion: pr });
      if (p.categoria_id) {
        const cat = categorias.get(p.categoria_id) ?? { nombre: p.categoria ?? "", color: p.categoria_color, n: 0 };
        cat.n += 1;
        categorias.set(p.categoria_id, cat);
      }
    }
    const indice = productos.map((p) => ({ p, texto: normalizar(`${p.nombre} ${p.categoria ?? ""} ${p.codigo_interno ?? ""}`) }));
    return { porCodigo, indice, categorias: [...categorias.entries()].sort((a, b) => b[1].n - a[1].n) };
  }, [productos]);

  const coincidencia = CANTIDAD.exec(texto.trim());
  const consulta = (coincidencia ? coincidencia[2]! : texto).trim();
  const cantidad = coincidencia ? coincidencia[1]!.replace(",", ".") : "1";

  const resultados = useMemo((): Opcion[] => {
    const palabras = normalizar(consulta).split(/\s+/).filter(Boolean);
    const lista = indice
      .filter(({ p, texto }) => (categoria === null || p.categoria_id === categoria) && palabras.every((w) => texto.includes(w)))
      .slice(0, MAX_RESULTADOS)
      .map(({ p }) => p);
    // Con texto, cada presentación es una opción más (Six pack, Caja x24)
    return lista.flatMap((p) => [
      { producto: p, presentacion: null },
      ...(palabras.length ? p.presentaciones.map((pr) => ({ producto: p, presentacion: pr })) : []),
    ]);
  }, [indice, consulta, categoria]);

  const agregar = (opcion: Opcion) => {
    onAgregar(opcion, cantidad);
    setTexto("");
    setActivo(0);
    entrada.current?.focus();
  };

  const alPresionar = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const n = resultados.length || 1;
      setActivo((i) => (i + (e.key === "ArrowDown" ? 1 : n - 1)) % n);
      return;
    }
    if (e.key === "Escape" && texto) {
      e.stopPropagation();
      setTexto("");
      return;
    }
    if (e.key !== "Enter") return;
    e.preventDefault();
    if (!consulta) return;
    const exacto = porCodigo.get(consulta.toUpperCase());
    if (exacto) return agregar(exacto);
    if (/^\d{6,}$/.test(consulta)) {
      onNoEncontrado(consulta);
      setTexto("");
      return;
    }
    if (resultados[activo]) agregar(resultados[activo]!);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <label className="flex h-[62px] flex-none items-center gap-3 rounded-2xl border-[2.5px] border-primary bg-card px-4">
        <Barcode className="size-6 flex-none" />
        <input
          ref={entrada}
          value={texto}
          onChange={(e) => {
            setTexto(e.target.value);
            setActivo(0);
          }}
          onKeyDown={alPresionar}
          placeholder="Escanea el código o escribe el producto…"
          aria-label="Buscar producto o escanear código"
          className="min-w-0 flex-1 bg-transparent text-[18px] font-semibold outline-none placeholder:text-muted-foreground"
          autoComplete="off"
          spellCheck={false}
          autoFocus
        />
        {coincidencia && <span className="rounded-lg bg-amarillo-suave px-2 py-1 text-xs font-extrabold text-amarillo-tinta tabular">× {cantidad}</span>}
        <kbd className="grid h-7 min-w-[34px] place-items-center rounded-md bg-navy px-1.5 text-xs font-extrabold text-amarillo">F2</kbd>
      </label>

      <div className="scrollbar-fino flex flex-none gap-2 overflow-x-auto pb-1">
        <Chip activo={categoria === null} onClick={() => setCategoria(null)}>
          Todos
        </Chip>
        {categorias.map(([id, c]) => (
          <Chip key={id} activo={categoria === id} color={c.color} onClick={() => setCategoria(categoria === id ? null : id)}>
            {c.nombre}
          </Chip>
        ))}
      </div>

      <div className="scrollbar-fino -mr-2 min-h-0 flex-1 overflow-y-auto pr-2">
        {resultados.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">No hay productos con «{consulta}»</p>
        ) : (
          <ul role="listbox" aria-label="Productos" className="grid grid-cols-2 gap-3 md:grid-cols-3 2xl:grid-cols-4">
            {resultados.map((o, i) => (
              <li key={`${o.producto.id}-${o.presentacion?.id ?? 0}`} role="option" aria-selected={i === activo}>
                <Tarjeta opcion={o} resaltada={!!consulta && i === activo} onClick={() => agregar(o)} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
});

function Chip({
  activo,
  color,
  onClick,
  children,
}: {
  activo: boolean;
  color?: string | null;
  onClick: () => void;
  children: React.ReactNode;
}) {
  const base = color ?? "#8a93a6";
  return (
    <button
      type="button"
      onClick={onClick}
      tabIndex={-1}
      style={
        activo
          ? undefined
          : {
              background: `color-mix(in oklab, ${base} 16%, var(--card))`,
              color: `color-mix(in oklab, ${base} 70%, var(--foreground))`,
            }
      }
      className={cn(
        "h-9 flex-none rounded-[10px] px-3.5 text-[13px] font-bold whitespace-nowrap transition-opacity",
        activo ? "bg-navy text-amarillo dark:bg-navy-2" : "hover:opacity-80",
      )}
    >
      {children}
    </button>
  );
}

function Tarjeta({ opcion, resaltada, onClick }: { opcion: Opcion; resaltada: boolean; onClick: () => void }) {
  const { producto: p, presentacion: pr } = opcion;
  const stock = Number(p.stock);
  const precio = pr ? pr.precio : p.precio;
  return (
    <button
      type="button"
      tabIndex={-1}
      onClick={onClick}
      className={cn(
        "flex h-full w-full flex-col gap-2 rounded-2xl border-2 bg-card p-3.5 text-left transition-colors hover:border-primary/60",
        resaltada ? "border-primary" : "border-transparent",
      )}
    >
      <ImagenProducto id={p.id} nombre={p.nombre} url={p.miniatura_url} className="size-11 rounded-xl text-[13px]" />
      <span className="line-clamp-2 text-sm leading-tight font-bold">
        {p.nombre}
        {pr && <span className="text-amarillo-tinta"> · {pr.nombre}</span>}
      </span>
      <span className="mt-auto flex w-full items-baseline justify-between gap-2">
        <b className="text-base tabular">{soles(precio)}</b>
        <span
          className={cn(
            "text-xs tabular",
            stock <= 0 ? "font-bold text-destructive" : stock <= 3 ? "font-bold text-destructive" : "text-muted-foreground",
          )}
        >
          {pr
            ? `${fmt(pr.factor)} und`
            : p.afecto_icbper
              ? "+ ICBPER"
              : stock <= 0
                ? "Sin stock"
                : stock <= 3
                  ? `Quedan ${fmt(stock)}`
                  : `${fmt(stock)} ${unidadCorta(p.unidad_medida)}`}
        </span>
      </span>
    </button>
  );
}
