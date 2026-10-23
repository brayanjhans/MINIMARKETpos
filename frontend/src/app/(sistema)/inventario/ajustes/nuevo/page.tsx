"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Minus, Plus, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { BuscadorProducto } from "@/components/productos/BuscadorProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { mensajeError, nuevaClave } from "@/lib/api";
import { cantidad as fmt, cantidadValida, normalizarNumero, vence } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { MotivoAjuste } from "@/types/inventario";
import type { ProductoListado } from "@/types/productos";

interface Linea {
  producto: ProductoListado;
  sale: boolean;
  cantidad: string;
  lote_id: number | null;
  numero_lote: string;
  fecha_vencimiento: string;
}

export default function NuevoAjustePage({ searchParams }: { searchParams: Promise<{ motivo?: string }> }) {
  const { motivo } = use(searchParams);
  return (
    <RequierePermiso permiso="inventario.ajustar">
      <NuevoAjuste motivoInicial={motivo} />
    </RequierePermiso>
  );
}

function NuevoAjuste({ motivoInicial }: { motivoInicial?: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  // La clave se crea al abrir el formulario: si el envío se repite (doble clic, red), no se duplica el ajuste
  const [clave] = useState(nuevaClave);
  const [motivoId, setMotivoId] = useState<number | null>(null);
  const [lineas, setLineas] = useState<Linea[]>([]);
  const [observaciones, setObservaciones] = useState("");
  const [error, setError] = useState<string | null>(null);

  const motivos = useQuery({ queryKey: ["motivos-ajuste"], queryFn: inventarioService.motivos, staleTime: 600_000 });
  const elegido =
    motivos.data?.find((m) => m.id === motivoId) ??
    (motivoInicial === "vencido" ? motivos.data?.find((m) => m.nombre === "Producto vencido") : undefined);

  const elegirMotivo = (m: MotivoAjuste) => {
    setMotivoId(m.id);
    setLineas((ls) => ls.map((l) => ({ ...l, sale: m.tipo === "ENTRADA" ? false : m.tipo === "SALIDA" ? true : l.sale })));
  };

  const agregar = (p: ProductoListado) => {
    setError(null);
    if (!p.maneja_lotes && lineas.some((l) => l.producto.id === p.id)) {
      toast.info(`${p.nombre} ya está en la lista`);
      return;
    }
    setLineas((ls) => [
      ...ls,
      { producto: p, sale: elegido?.tipo !== "ENTRADA", cantidad: "1", lote_id: null, numero_lote: "", fecha_vencimiento: "" },
    ]);
  };
  const cambiar = (i: number, cambio: Partial<Linea>) => {
    setError(null);
    setLineas((ls) => ls.map((l, j) => (j === i ? { ...l, ...cambio } : l)));
  };

  const valor = lineas.reduce((t, l) => t + (Number(normalizarNumero(l.cantidad)) || 0) * Number(l.producto.precio_costo ?? 0) * (l.sale ? -1 : 1), 0);
  const unidades = lineas.reduce((t, l) => t + (Number(normalizarNumero(l.cantidad)) || 0), 0);

  const guardar = useMutation({
    mutationFn: (enviar: boolean) => {
      if (!elegido) throw new Error("Elige por qué se ajusta el stock");
      if (!lineas.length) throw new Error("Agrega al menos un producto");
      for (const l of lineas) {
        if (!cantidadValida(l.cantidad, l.producto.permite_decimales) || Number(normalizarNumero(l.cantidad)) <= 0)
          throw new Error(`Revisa la cantidad de ${l.producto.nombre}`);
        if (l.producto.maneja_lotes && l.sale && !l.lote_id) throw new Error(`Elige de qué lote sale ${l.producto.nombre}`);
        if (l.producto.maneja_lotes && !l.sale && !l.lote_id && !l.numero_lote.trim())
          throw new Error(`Indica el lote donde entra ${l.producto.nombre}`);
      }
      return inventarioService.crearAjuste(
        {
          motivo_id: elegido.id,
          observaciones: observaciones.trim() || null,
          enviar,
          detalles: lineas.map((l) => ({
            producto_id: l.producto.id,
            cantidad: (l.sale ? "-" : "") + normalizarNumero(l.cantidad),
            lote_id: l.lote_id,
            numero_lote: !l.lote_id && l.numero_lote.trim() ? l.numero_lote.trim() : null,
            fecha_vencimiento: !l.lote_id && l.fecha_vencimiento ? l.fecha_vencimiento : null,
          })),
        },
        clave,
      );
    },
    onSuccess: (ajuste) => {
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      toast.success(ajuste.estado === "BORRADOR" ? `Borrador ${ajuste.numero} guardado` : `${ajuste.numero} enviado a aprobación`);
      router.replace(`/inventario/ajustes/${ajuste.id}`);
    },
    onError: (e) => setError(mensajeError(e)),
  });

  return (
    <>
      <div className="mb-5">
        <Link href="/inventario/ajustes" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
          Inventario › Ajustes ›
        </Link>
        <h1 className="flex flex-wrap items-center gap-3 text-[24px] font-extrabold tracking-[-0.02em]">
          Nuevo ajuste
          <span className="text-[13px] font-semibold text-muted-foreground">
            Borrador → <b className="text-amarillo-tinta">Por aprobar</b> → Aplicado
          </span>
        </h1>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex min-w-0 flex-col gap-4">
          <section className="tarjeta p-5">
            <h2 className="mb-3 text-[15px] font-extrabold">¿Por qué se ajusta el stock?</h2>
            <div role="radiogroup" aria-label="Motivo" className="flex flex-wrap gap-2">
              {(motivos.data ?? []).map((m) => (
                <button
                  key={m.id}
                  type="button"
                  role="radio"
                  aria-checked={elegido?.id === m.id}
                  onClick={() => elegirMotivo(m)}
                  className={cn(
                    "inline-flex h-10 items-center gap-2 rounded-xl border-2 border-transparent bg-muted px-3.5 text-[13px] font-semibold",
                    elegido?.id === m.id && "border-primary bg-aviso-fondo font-extrabold",
                  )}
                >
                  <span
                    aria-hidden
                    className={cn("size-2 rounded-full", m.es_merma ? "bg-destructive" : m.tipo === "ENTRADA" ? "bg-positive" : m.tipo === "SALIDA" ? "bg-warning" : "bg-muted-foreground/50")}
                  />
                  {m.nombre}
                </button>
              ))}
            </div>
            <p className="mt-3 text-[13px] text-muted-foreground">
              <span aria-hidden className="mr-1.5 inline-block size-2 rounded-full bg-destructive" />
              Rojo: cuenta como merma (pérdida) en los reportes de ganancia.
            </p>
          </section>

          <section className="tarjeta overflow-hidden">
            <div className="p-4">
              <BuscadorProducto onSeleccionar={agregar} placeholder="Escanea o busca el producto para agregarlo" />
            </div>
            {lineas.length === 0 ? (
              <p className="border-t border-rule px-5 py-10 text-center text-sm text-muted-foreground">
                Escanea o busca los productos que se ajustan.
              </p>
            ) : (
              <div className="scrollbar-fino overflow-x-auto">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                      <th className="h-10 px-4">Producto</th>
                      <th className="px-2">Lote</th>
                      <th className="px-2 text-right">Stock</th>
                      <th className="px-2 text-center">{elegido?.tipo === "AMBOS" ? "Cantidad" : elegido?.tipo === "ENTRADA" ? "Entra" : "Se retira"}</th>
                      <th className="px-2 text-right">Queda</th>
                      <th className="px-4 text-right">{elegido?.es_merma ? "Pérdida" : "Valor"}</th>
                      <th className="w-10" />
                    </tr>
                  </thead>
                  <tbody>
                    {lineas.map((l, i) => (
                      <FilaAjuste
                        key={`${l.producto.id}-${i}`}
                        linea={l}
                        ambos={elegido?.tipo === "AMBOS"}
                        onCambiar={(c) => cambiar(i, c)}
                        onQuitar={() => setLineas((ls) => ls.filter((_, j) => j !== i))}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

        <div className="flex flex-col gap-4">
          <section className="tarjeta bg-navy p-5 text-white dark:bg-navy-2">
            <p className="text-[13px] text-navy-ink">{elegido?.es_merma ? "Pérdida total (merma)" : "Valor del ajuste"}</p>
            <p className={cn("mt-1 text-[32px] leading-[1.15] font-extrabold tracking-[-0.02em] tabular", valor < 0 && "text-[#ffb3aa]")}>{soles(Math.abs(valor))}</p>
            <dl className="mt-2 text-sm">
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Productos</dt>
                <dd className="font-bold tabular">{lineas.length}</dd>
              </div>
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Unidades</dt>
                <dd className="font-bold tabular">{fmt(unidades)}</dd>
              </div>
            </dl>
          </section>
          <section className="tarjeta p-5">
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold">
              Observación
              <textarea
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                maxLength={300}
                rows={3}
                placeholder="Ej. Revisión de la mañana: lácteos vencidos"
                className="resize-none rounded-[10px] border border-input bg-transparent px-3 py-2 text-sm font-normal outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
            <p className="mt-2 text-xs text-muted-foreground">
              El stock no cambia hasta que un Administrador lo apruebe (no puedes aprobar tu propio ajuste). Al aprobar se
              vuelve a revisar el stock y queda en el kardex y la auditoría.
            </p>
          </section>
          {error && (
            <p role="alert" className="rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
              {error}
            </p>
          )}
          <div className="mt-auto flex flex-col gap-2">
            <Button className="h-12 text-[15px] font-extrabold" disabled={guardar.isPending} onClick={() => guardar.mutate(true)}>
              {guardar.isPending && <Loader2 className="animate-spin" />} Enviar a aprobación
            </Button>
            <Button variant="outline" className="h-10" disabled={guardar.isPending} onClick={() => guardar.mutate(false)}>
              Guardar como borrador
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}

function FilaAjuste({
  linea: l,
  ambos,
  onCambiar,
  onQuitar,
}: {
  linea: Linea;
  ambos: boolean;
  onCambiar: (c: Partial<Linea>) => void;
  onQuitar: () => void;
}) {
  const lotes = useQuery({
    queryKey: ["inventario", "lotes", "producto", l.producto.id],
    queryFn: () => inventarioService.lotes({ producto_id: l.producto.id }),
    enabled: l.producto.maneja_lotes,
  });
  const lote = lotes.data?.find((x) => x.id === l.lote_id);
  const n = Number(normalizarNumero(l.cantidad)) || 0;
  const disponible = l.producto.maneja_lotes ? Number(lote?.cantidad_actual ?? 0) : Number(l.producto.stock);
  const queda = disponible + (l.sale ? -n : n);
  const paso = l.producto.permite_decimales ? 0.1 : 1;
  const sumar = (d: number) => onCambiar({ cantidad: String(Math.max(paso, Math.round((n + d) * 1000) / 1000)) });
  const valor = n * Number(l.producto.precio_costo ?? 0);

  return (
    <tr className="border-t border-rule">
      <td className="px-4 py-2.5">
        <p className="font-bold">{l.producto.nombre}</p>
        {l.producto.precio_costo !== null && <p className="text-xs text-muted-foreground tabular">{soles(l.producto.precio_costo)} c/u</p>}
        {ambos && (
          <div className="mt-1 inline-flex rounded-lg bg-muted p-0.5 text-xs font-bold">
            {[true, false].map((sale) => (
              <button
                key={String(sale)}
                type="button"
                onClick={() => onCambiar({ sale, lote_id: null })}
                className={cn("rounded-md px-2 py-0.5", l.sale === sale && "bg-card shadow-sm")}
              >
                {sale ? "Sale" : "Entra"}
              </button>
            ))}
          </div>
        )}
      </td>
      <td className="px-2">
        {!l.producto.maneja_lotes ? (
          <span className="text-muted-foreground">—</span>
        ) : l.sale ? (
          <Select value={l.lote_id ? String(l.lote_id) : undefined} onValueChange={(v) => onCambiar({ lote_id: Number(v) })}>
            <SelectTrigger className="h-9 w-44" aria-label="Lote">
              <SelectValue placeholder={lotes.data?.length === 0 ? "Sin lotes" : "Elegir lote"} />
            </SelectTrigger>
            <SelectContent>
              {(lotes.data ?? []).map((x) => (
                <SelectItem key={x.id} value={String(x.id)}>
                  {x.numero_lote} · {vence(x.dias_para_vencer)} · {fmt(x.cantidad_actual)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <div className="flex gap-1.5">
            <Input value={l.numero_lote} onChange={(e) => onCambiar({ numero_lote: e.target.value, lote_id: null })} placeholder="Lote" maxLength={50} className="h-9 w-24" aria-label="Número de lote" />
            <Input type="date" value={l.fecha_vencimiento} onChange={(e) => onCambiar({ fecha_vencimiento: e.target.value })} className="h-9 w-36" aria-label="Vencimiento" />
          </div>
        )}
      </td>
      <td className="px-2 text-right tabular">{l.producto.maneja_lotes && !lote ? "—" : fmt(disponible)}</td>
      <td className="px-2">
        <div className="mx-auto flex w-fit items-center rounded-[10px] border border-input">
          <button type="button" aria-label="Menos" className="grid size-8 place-items-center" onClick={() => sumar(-paso)}>
            <Minus className="size-3.5" />
          </button>
          <input
            value={l.cantidad}
            onChange={(e) => onCambiar({ cantidad: e.target.value })}
            inputMode="decimal"
            aria-label="Cantidad"
            className="w-14 bg-transparent text-center font-extrabold tabular outline-none"
          />
          <button type="button" aria-label="Más" className="grid size-8 place-items-center" onClick={() => sumar(paso)}>
            <Plus className="size-3.5" />
          </button>
        </div>
      </td>
      <td className={cn("px-2 text-right font-bold tabular", queda < 0 && "text-destructive")}>
        {l.producto.maneja_lotes && !lote && l.sale ? "—" : fmt(queda)}
      </td>
      <td className={cn("px-4 text-right font-bold tabular", l.sale ? "text-destructive" : "text-positive")}>
        {l.producto.precio_costo === null ? "—" : soles(valor)}
      </td>
      <td className="pr-2">
        <Button variant="ghost" size="icon-sm" aria-label={`Quitar ${l.producto.nombre}`} onClick={onQuitar}>
          <X />
        </Button>
      </td>
    </tr>
  );
}
