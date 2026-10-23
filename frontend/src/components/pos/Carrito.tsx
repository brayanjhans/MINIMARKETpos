"use client";

import { Minus, Plus, ShoppingBasket, Trash2, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import { desdeCentimos, type Totales } from "@/lib/ventas";
import { cn, soles } from "@/lib/utils";
import type { ItemCarrito } from "@/store/carritoStore";
import type { Cliente } from "@/types/ventas";

interface Props {
  items: ItemCarrito[];
  totales: Totales;
  igv: string;
  cliente: Cliente | null;
  descuento: string;
  ultimo: string | null;
  onCantidad: (clave: string, cantidad: string) => void;
  onQuitar: (clave: string) => void;
  onDescuento: (valor: string) => void;
  onCliente: () => void;
  onCobrar: () => void;
  onVaciar: () => void;
}

const sumar = (texto: string, delta: number, decimales: boolean) => {
  const n = Number(texto.replace(",", ".")) || 0;
  const r = Math.max(n + delta, decimales ? 0.001 : 1);
  return String(Math.round(r * 1000) / 1000);
};

export function Carrito(p: Props) {
  const { totales: t } = p;
  const unidades = p.items.length;
  return (
    <section className="flex min-h-0 flex-col rounded-[20px] bg-card p-5" aria-label="Venta actual">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-extrabold">Venta actual</h2>
        <button type="button" onClick={p.onCliente} className="flex min-w-0 items-center gap-1.5 text-[13px] text-muted-foreground hover:text-foreground">
          Cliente: <b className="truncate text-foreground">{p.cliente?.nombre ?? "Varios"}</b>
          <kbd className="rounded-md bg-navy px-1.5 py-0.5 text-[11px] font-extrabold text-amarillo">F6</kbd>
        </button>
      </div>

      <div className="scrollbar-fino -mx-2 mt-2 min-h-0 flex-1 overflow-y-auto px-2">
        {p.items.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 py-10 text-center text-sm text-muted-foreground">
            <ShoppingBasket className="size-8" />
            Escanea un producto para empezar
          </div>
        ) : (
          <ul>
            {p.items.map((item, i) => {
              const linea = t.lineas[i];
              const reciente = item.clave === p.ultimo;
              return (
                <li
                  key={item.clave}
                  className={cn(
                    "grid grid-cols-[minmax(0,1fr)_auto_auto_auto] items-center gap-2.5 border-t border-rule py-2.5 first:border-t-0",
                    reciente && "-mx-2 rounded-xl border-transparent bg-aviso-fondo px-2",
                  )}
                >
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-sm leading-tight font-bold">
                      {item.nombre}
                      {item.presentacion && <span className="text-amarillo-tinta"> · {item.presentacion}</span>}
                    </p>
                    <p className={cn("text-xs tabular", reciente ? "font-semibold text-amarillo-tinta" : "text-muted-foreground")}>
                      {soles(item.precio)} c/u{item.afecto_icbper && " + ICBPER"}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 rounded-[10px] bg-muted p-[3px]">
                    <button
                      type="button"
                      tabIndex={-1}
                      aria-label={`Uno menos de ${item.nombre}`}
                      onClick={() => p.onCantidad(item.clave, sumar(item.cantidad, -1, item.permite_decimales))}
                      className="grid size-7 place-items-center rounded-lg bg-card"
                    >
                      <Minus className="size-3.5" />
                    </button>
                    <Input
                      value={item.cantidad}
                      onChange={(e) => p.onCantidad(item.clave, e.target.value)}
                      inputMode="decimal"
                      aria-label={`Cantidad de ${item.nombre}`}
                      className="h-7 w-12 border-0 bg-transparent px-0 text-center font-bold shadow-none tabular focus-visible:ring-1"
                    />
                    <button
                      type="button"
                      tabIndex={-1}
                      aria-label={`Uno más de ${item.nombre}`}
                      onClick={() => p.onCantidad(item.clave, sumar(item.cantidad, 1, item.permite_decimales))}
                      className="grid size-7 place-items-center rounded-lg bg-card"
                    >
                      <Plus className="size-3.5" />
                    </button>
                  </div>
                  <b className="w-16 text-right tabular">{linea ? desdeCentimos(linea.total) : "—"}</b>
                  <button
                    type="button"
                    tabIndex={-1}
                    aria-label={`Quitar ${item.nombre}`}
                    onClick={() => p.onQuitar(item.clave)}
                    className="grid size-7 place-items-center rounded-lg text-muted-foreground hover:bg-muted hover:text-destructive"
                  >
                    <X className="size-4" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <dl className="flex flex-col gap-1 border-t border-dashed border-border py-3 text-[13px] text-muted-foreground tabular">
        {t.gravadas > 0 && <Linea texto="Op. gravada" valor={t.gravadas} />}
        {t.exoneradas > 0 && <Linea texto="Op. exonerada" valor={t.exoneradas} />}
        {t.inafectas > 0 && <Linea texto="Op. inafecta" valor={t.inafectas} />}
        <Linea texto={`IGV ${Number(p.igv)}%`} valor={t.igv} />
        {t.icbper > 0 && <Linea texto="ICBPER" valor={t.icbper} />}
        <div className="flex items-center justify-between gap-3">
          <dt>Descuento S/</dt>
          <dd>
            <Input
              value={p.descuento}
              onChange={(e) => p.onDescuento(e.target.value)}
              inputMode="decimal"
              placeholder="0.00"
              aria-label="Descuento en soles"
              className="h-7 w-20 text-right tabular"
            />
          </dd>
        </div>
        {t.error && <p className="font-semibold text-destructive">{t.error}</p>}
      </dl>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={p.onVaciar}
          disabled={!p.items.length}
          aria-label="Vaciar la venta"
          className="grid h-[74px] w-14 flex-none place-items-center rounded-2xl bg-muted text-muted-foreground hover:text-destructive disabled:opacity-40"
        >
          <Trash2 className="size-5" />
        </button>
        <button
          type="button"
          onClick={p.onCobrar}
          disabled={!p.items.length || !!t.error}
          className="flex h-[74px] flex-1 items-center justify-between rounded-2xl bg-primary px-5 text-primary-foreground transition-opacity hover:opacity-95 disabled:opacity-50"
        >
          <span className="text-left">
            <span className="block text-lg font-extrabold">Cobrar</span>
            <span className="text-xs font-bold opacity-75">
              {unidades} {unidades === 1 ? "producto" : "productos"} · F4
            </span>
          </span>
          <span className="text-[32px] font-extrabold tracking-[-0.02em] tabular">{soles(desdeCentimos(t.total))}</span>
        </button>
      </div>
    </section>
  );
}

function Linea({ texto, valor }: { texto: string; valor: number }) {
  return (
    <div className="flex justify-between">
      <dt>{texto}</dt>
      <dd>{desdeCentimos(valor)}</dd>
    </div>
  );
}
