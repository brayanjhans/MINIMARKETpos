"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Barcode, Loader2, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { PageHeader } from "@/components/comunes/PageHeader";
import { NavInventario } from "@/components/inventario/NavInventario";
import { BuscadorProducto } from "@/components/productos/BuscadorProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, mensajeError, nuevaClave } from "@/lib/api";
import { cantidad as fmt, cantidadValida, normalizarNumero } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { ProductoListado } from "@/types/productos";

interface Linea {
  clave: string;
  producto: ProductoListado;
  cantidad: string;
  costo: string;
  lote: string;
  vencimiento: string;
  /** Motivo por el que no se puede cargar (ya tiene movimientos) */
  bloqueo: string | null;
}

const COSTO = /^\d{1,6}([.,]\d{1,4})?$/;

export default function StockInicialPage() {
  return (
    <RequierePermiso permiso="inventario.stock_inicial">
      <StockInicial />
    </RequierePermiso>
  );
}

function StockInicial() {
  const queryClient = useQueryClient();
  const [clave, setClave] = useState(nuevaClave);
  const [lineas, setLineas] = useState<Linea[]>([]);
  const [error, setError] = useState<string | null>(null);

  const agregar = async (p: ProductoListado) => {
    setError(null);
    if (!p.maneja_lotes && lineas.some((l) => l.producto.id === p.id)) return toast.info(`${p.nombre} ya está en la lista`);
    let bloqueo: string | null = null;
    try {
      const [estado] = await api<{ producto_id: number; puede: boolean; motivo: string | null }[]>(
        "/inventario/stock-inicial/cargables",
        { params: { producto_ids: p.id } },
      );
      bloqueo = estado && !estado.puede ? estado.motivo : null;
    } catch {
      // si no se pudo consultar, el servidor lo validará al cargar
    }
    setLineas((ls) => [
      ...ls,
      {
        clave: nuevaClave(),
        producto: p,
        cantidad: "",
        costo: p.precio_costo && Number(p.precio_costo) > 0 ? String(Number(p.precio_costo)) : "",
        lote: "",
        vencimiento: "",
        bloqueo,
      },
    ]);
  };
  const cambiar = (i: number, c: Partial<Linea>) => {
    setError(null);
    setLineas((ls) => ls.map((l, j) => (j === i ? { ...l, ...c } : l)));
  };

  const validas = lineas.filter((l) => !l.bloqueo);
  const valor = validas.reduce((t, l) => t + (Number(normalizarNumero(l.cantidad)) || 0) * (Number(normalizarNumero(l.costo)) || 0), 0);
  const unidades = validas.reduce((t, l) => t + (Number(normalizarNumero(l.cantidad)) || 0), 0);

  const cargar = useMutation({
    mutationFn: () => {
      if (!validas.length) throw new Error("Agrega productos que se puedan cargar");
      for (const l of validas) {
        if (!cantidadValida(l.cantidad, l.producto.permite_decimales) || Number(normalizarNumero(l.cantidad)) <= 0)
          throw new Error(`Escribe cuántos hay de ${l.producto.nombre}`);
        if (!COSTO.test(l.costo.trim())) throw new Error(`Escribe el costo de ${l.producto.nombre}`);
        if (l.producto.maneja_lotes && !l.lote.trim()) throw new Error(`Indica el lote de ${l.producto.nombre}`);
      }
      return inventarioService.stockInicial(
        validas.map((l) => ({
          producto_id: l.producto.id,
          cantidad: normalizarNumero(l.cantidad),
          costo_unitario: normalizarNumero(l.costo),
          numero_lote: l.producto.maneja_lotes ? l.lote.trim() : null,
          fecha_vencimiento: l.producto.maneja_lotes && l.vencimiento ? l.vencimiento : null,
        })),
        clave,
      );
    },
    onSuccess: (r) => {
      toast.success(`Stock cargado: ${r.productos} productos, ${soles(r.valor)}`);
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
      setLineas([]);
      setClave(nuevaClave()); // la próxima carga es otra operación
    },
    onError: (e) => setError(mensajeError(e)),
  });

  return (
    <>
      <PageHeader titulo="Cargar stock inicial" linea="Para empezar a usar el sistema con lo que ya tienes en el almacén de venta." />
      <NavInventario />

      <div className="mb-4 grid gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-3 rounded-2xl border-2 border-primary bg-aviso-fondo p-4">
          <span className="grid size-10 flex-none place-items-center rounded-xl bg-primary text-primary-foreground">
            <Barcode className="size-5" />
          </span>
          <div>
            <b>Uno por uno</b>
            <p className="text-[13px] text-muted-foreground">Escaneas cada producto y escribes cuántos hay</p>
          </div>
        </div>
        <Link href="/productos/importar" className="tarjeta flex items-center gap-3 p-4 transition-shadow hover:shadow-md">
          <span className="grid size-10 flex-none place-items-center rounded-xl bg-p-verde text-[11px] font-extrabold text-p-verde-t">XLSX</span>
          <div>
            <b>Desde Excel</b>
            <p className="text-[13px] text-muted-foreground">Una columna «Stock inicial» en la plantilla de productos</p>
          </div>
        </Link>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
        <section className="tarjeta overflow-hidden">
          <div className="p-4">
            <BuscadorProducto onSeleccionar={(p) => void agregar(p)} placeholder="Escanea o busca el producto" autoFocus />
          </div>
          {lineas.length === 0 ? (
            <p className="border-t border-rule px-5 py-10 text-center text-sm text-muted-foreground">
              Escanea los productos del almacén. Cada uno se carga una sola vez; después el stock cambia con compras, ventas o
              ajustes.
            </p>
          ) : (
            <div className="scrollbar-fino overflow-x-auto">
              <table className="w-full min-w-[680px] text-sm">
                <thead>
                  <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                    <th className="h-10 px-4">Producto</th>
                    <th className="px-2">Cantidad</th>
                    <th className="px-2">Costo c/u</th>
                    <th className="px-2">Lote y vencimiento</th>
                    <th className="px-4 text-right">Valor</th>
                    <th className="w-10" />
                  </tr>
                </thead>
                <tbody>
                  {lineas.map((l, i) => (
                    <tr key={l.clave} className={cn("border-t border-rule", l.bloqueo && "bg-aviso-fondo")}>
                      <td className="px-4 py-2 font-bold">{l.producto.nombre}</td>
                      {l.bloqueo ? (
                        <td colSpan={4} className="px-2 text-[13px] font-semibold text-amarillo-tinta">
                          {l.bloqueo}:{" "}
                          <Link href="/inventario/ajustes/nuevo" className="font-extrabold underline">
                            hacer un ajuste
                          </Link>
                        </td>
                      ) : (
                        <>
                          <td className="px-2">
                            <Input value={l.cantidad} onChange={(e) => cambiar(i, { cantidad: e.target.value })} inputMode="decimal" className="h-9 w-20 tabular" aria-label="Cantidad" autoFocus />
                          </td>
                          <td className="px-2">
                            <Input value={l.costo} onChange={(e) => cambiar(i, { costo: e.target.value })} inputMode="decimal" className="h-9 w-24 tabular" aria-label="Costo" placeholder="0.00" />
                          </td>
                          <td className="px-2">
                            {l.producto.maneja_lotes ? (
                              <div className="flex gap-1.5">
                                <Input value={l.lote} onChange={(e) => cambiar(i, { lote: e.target.value })} className="h-9 w-24" maxLength={50} placeholder="Lote" aria-label="Lote" />
                                <Input type="date" value={l.vencimiento} onChange={(e) => cambiar(i, { vencimiento: e.target.value })} className="h-9 w-36" aria-label="Vencimiento" />
                              </div>
                            ) : (
                              <span className="text-[13px] text-muted-foreground">No controla lotes</span>
                            )}
                          </td>
                          <td className="px-4 text-right font-bold tabular">
                            {soles((Number(normalizarNumero(l.cantidad)) || 0) * (Number(normalizarNumero(l.costo)) || 0))}
                          </td>
                        </>
                      )}
                      <td className="pr-2">
                        <Button variant="ghost" size="icon-sm" aria-label={`Quitar ${l.producto.nombre}`} onClick={() => setLineas((ls) => ls.filter((_, j) => j !== i))}>
                          <X />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <div className="flex flex-col gap-4">
          <section className="tarjeta bg-navy p-5 text-white dark:bg-navy-2">
            <p className="text-[13px] text-navy-ink">Valor que entra al inventario</p>
            <p className="text-[32px] font-extrabold tracking-[-0.02em] tabular">{soles(valor)}</p>
            <dl className="mt-2 text-sm">
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Productos</dt>
                <dd className="font-bold tabular">{new Set(validas.map((l) => l.producto.id)).size}</dd>
              </div>
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Unidades</dt>
                <dd className="font-bold tabular">{fmt(unidades)}</dd>
              </div>
            </dl>
          </section>
          <section className="tarjeta bg-aviso-fondo p-5 text-[13px] leading-relaxed text-muted-foreground">
            <b className="text-foreground">Una sola vez por producto</b>
            <p className="mt-1">
              Cada producto entra con «Stock inicial» en su kardex y ese costo pasa a ser su costo promedio. Después, todo
              cambio se hace con compras, ventas o ajustes.
            </p>
          </section>
          {error && (
            <p role="alert" className="rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
              {error}
            </p>
          )}
          <Button className="h-12 text-[15px] font-extrabold" disabled={cargar.isPending || !validas.length} onClick={() => cargar.mutate()}>
            {cargar.isPending && <Loader2 className="animate-spin" />} Cargar stock inicial
          </Button>
        </div>
      </div>
    </>
  );
}
