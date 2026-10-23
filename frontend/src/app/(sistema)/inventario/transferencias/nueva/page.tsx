"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Loader2, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { BuscadorProducto } from "@/components/productos/BuscadorProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { mensajeError, nuevaClave } from "@/lib/api";
import { cantidad as fmt, cantidadValida, normalizarNumero, unidadCorta } from "@/lib/inventario";
import { cn } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { ProductoListado } from "@/types/productos";

interface Linea {
  producto: ProductoListado;
  cantidad: string;
}

export default function NuevaTransferenciaPage() {
  return (
    <RequierePermiso permiso="inventario.transferir">
      <NuevaTransferencia />
    </RequierePermiso>
  );
}

function NuevaTransferencia() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [clave] = useState(nuevaClave);
  const [destino, setDestino] = useState<string>();
  const [lineas, setLineas] = useState<Linea[]>([]);
  const [observaciones, setObservaciones] = useState("");
  const [error, setError] = useState<string | null>(null);
  const almacenes = useQuery({ queryKey: ["almacenes"], queryFn: inventarioService.almacenes, staleTime: 300_000 });
  const origen = almacenes.data?.find((a) => a.es_sucursal_actual && a.es_almacen_venta);
  const destinos = (almacenes.data ?? []).filter((a) => a.id !== origen?.id);

  const enviar = useMutation({
    mutationFn: () => {
      if (!destino) throw new Error("Elige a qué almacén va la mercadería");
      if (!lineas.length) throw new Error("Agrega al menos un producto");
      for (const l of lineas) {
        if (!cantidadValida(l.cantidad, l.producto.permite_decimales) || Number(normalizarNumero(l.cantidad)) <= 0)
          throw new Error(`Revisa la cantidad de ${l.producto.nombre}`);
        if (Number(normalizarNumero(l.cantidad)) > Number(l.producto.stock))
          throw new Error(`De ${l.producto.nombre} solo hay ${fmt(l.producto.stock)}`);
      }
      return inventarioService.crearTransferencia(
        {
          almacen_destino_id: Number(destino),
          observaciones: observaciones.trim() || null,
          detalles: lineas.map((l) => ({ producto_id: l.producto.id, cantidad: normalizarNumero(l.cantidad) })),
        },
        clave,
      );
    },
    onSuccess: (t) => {
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
      toast.success(`${t.numero} enviada: la mercadería está en camino`);
      router.replace(`/inventario/transferencias/${t.id}`);
    },
    onError: (e) => setError(mensajeError(e)),
  });

  return (
    <>
      <div className="mb-5">
        <Link href="/inventario/transferencias" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
          Inventario › Transferencias ›
        </Link>
        <h1 className="text-[24px] font-extrabold tracking-[-0.02em]">Nueva transferencia</h1>
      </div>

      <div className="mb-4 flex flex-col items-stretch gap-3 md:flex-row md:items-center">
        <div className="tarjeta flex-1 px-5 py-4">
          <p className="text-xs font-semibold text-muted-foreground">Sale de</p>
          <p className="text-base font-extrabold">{origen?.nombre ?? "…"}</p>
          <p className="text-[13px] text-muted-foreground">{origen?.sucursal}</p>
        </div>
        <div className="mx-auto grid size-11 flex-none rotate-90 place-items-center rounded-xl bg-navy md:rotate-0">
          <ArrowRight className="size-5 text-primary" strokeWidth={2.4} />
        </div>
        <div className="tarjeta flex-1 border-2 border-primary bg-aviso-fondo px-5 py-3">
          <p className="mb-1 text-xs font-bold text-amarillo-tinta">Llega a</p>
          <Select value={destino} onValueChange={setDestino}>
            <SelectTrigger className="w-full bg-card font-bold" aria-label="Almacén de destino">
              <SelectValue placeholder={destinos.length ? "Elegir almacén" : "No hay otro almacén"} />
            </SelectTrigger>
            <SelectContent>
              {destinos.map((a) => (
                <SelectItem key={a.id} value={String(a.id)}>
                  {a.nombre} · {a.sucursal}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="tarjeta overflow-hidden">
          <div className="p-4">
            <BuscadorProducto
              onSeleccionar={(p) => {
                setError(null);
                if (lineas.some((l) => l.producto.id === p.id)) return toast.info(`${p.nombre} ya está en la lista`);
                if (Number(p.stock) <= 0) return toast.error(`${p.nombre} no tiene stock en este almacén`);
                setLineas((ls) => [...ls, { producto: p, cantidad: "1" }]);
              }}
            />
          </div>
          {lineas.length === 0 ? (
            <p className="border-t border-rule px-5 py-10 text-center text-sm text-muted-foreground">Escanea o busca lo que vas a enviar.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                  <th className="h-10 px-4">Producto</th>
                  <th className="px-3 text-right">Hay</th>
                  <th className="px-3 text-center">Envías</th>
                  <th className="w-10" />
                </tr>
              </thead>
              <tbody>
                {lineas.map((l, i) => {
                  const excede = Number(normalizarNumero(l.cantidad)) > Number(l.producto.stock);
                  return (
                    <tr key={l.producto.id} className="h-14 border-t border-rule">
                      <td className="px-4">
                        <p className="font-bold">{l.producto.nombre}</p>
                        {l.producto.maneja_lotes && <p className="text-xs text-muted-foreground">Salen primero los lotes que vencen antes</p>}
                      </td>
                      <td className="px-3 text-right tabular">
                        {fmt(l.producto.stock)} {unidadCorta(l.producto.unidad_medida)}
                      </td>
                      <td className="px-3">
                        <Input
                          value={l.cantidad}
                          onChange={(e) => setLineas((ls) => ls.map((x, j) => (j === i ? { ...x, cantidad: e.target.value } : x)))}
                          inputMode="decimal"
                          aria-label={`Cantidad de ${l.producto.nombre}`}
                          className={cn("mx-auto h-9 w-20 text-center font-extrabold tabular", excede && "border-destructive")}
                        />
                      </td>
                      <td className="pr-2">
                        <Button variant="ghost" size="icon-sm" aria-label={`Quitar ${l.producto.nombre}`} onClick={() => setLineas((ls) => ls.filter((_, j) => j !== i))}>
                          <X />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>

        <div className="flex flex-col gap-4">
          <section className="tarjeta p-5">
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold">
              Observación
              <textarea
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                maxLength={300}
                rows={3}
                placeholder="Ej. Reposición de bebidas para el fin de semana"
                className="resize-none rounded-[10px] border border-input bg-transparent px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          </section>
          <section className="tarjeta bg-aviso-fondo p-5 text-[13px] leading-relaxed text-muted-foreground">
            <b className="text-foreground">Mientras viaja</b>
            <p className="mt-1">
              La mercadería sale de tu almacén al enviar y queda «en tránsito» con su valor hasta que el otro almacén la
              reciba. Lo que no llegue se registra como merma.
            </p>
          </section>
          {error && (
            <p role="alert" className="rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
              {error}
            </p>
          )}
          <Button className="h-12 text-[15px] font-extrabold" disabled={enviar.isPending} onClick={() => enviar.mutate()}>
            {enviar.isPending && <Loader2 className="animate-spin" />} Enviar mercadería
          </Button>
        </div>
      </div>
    </>
  );
}
