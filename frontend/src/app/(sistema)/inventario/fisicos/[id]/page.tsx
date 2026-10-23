"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Barcode, Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { use, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Pildora } from "@/components/comunes/Pildora";
import { RechazoDialog } from "@/components/inventario/RechazoDialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, mensajeError } from "@/lib/api";
import { cantidad, cantidadValida, ESTADOS_FISICO, normalizarNumero } from "@/lib/inventario";
import { cn, fecha, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import { productosService } from "@/services/productos.service";
import type { FisicoDetalle } from "@/types/inventario";

export default function FisicoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="inventario.ver">
      <Fisico id={Number(id)} />
    </RequierePermiso>
  );
}

function Fisico({ id }: { id: number }) {
  const consulta = useQuery({ queryKey: ["inventario", "fisico", id], queryFn: () => inventarioService.fisico(id) });
  if (consulta.isLoading) return <Skeleton className="h-96 w-full rounded-[18px]" />;
  if (!consulta.data) return <p className="tarjeta p-6 text-sm">{mensajeError(consulta.error)}</p>;
  // key: cada versión guardada reinicia lo escrito con lo que confirmó el servidor
  return <Conteo key={consulta.data.fecha_envio ?? "abierto"} inventario={consulta.data} />;
}

function Conteo({ inventario: f }: { inventario: FisicoDetalle }) {
  const { tiene, usuario } = useAuth();
  const queryClient = useQueryClient();
  const enProceso = f.estado === "EN_PROCESO";
  const puedeContar = enProceso && tiene("inventario.inventario_fisico");
  // Lo escrito en pantalla y aún no guardado, por línea
  const [editado, setEditado] = useState<Record<number, string>>({});
  const [escaneo, setEscaneo] = useState("");
  const [rechazando, setRechazando] = useState(false);
  const filas = useRef<Record<number, HTMLInputElement | null>>({});

  const valorDe = (detalleId: number, guardado: string | null) => editado[detalleId] ?? (guardado === null ? "" : String(Number(guardado)));
  const pendientes = Object.keys(editado).length;

  const lineas = useMemo(
    () =>
      f.detalles.map((d) => {
        const texto = valorDe(d.id, d.stock_contado);
        const contado = texto.trim() === "" ? null : Number(normalizarNumero(texto));
        const diferencia = contado === null || Number.isNaN(contado) ? null : contado - Number(d.stock_sistema);
        return { ...d, texto, contado, diferenciaLocal: diferencia };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [f.detalles, editado],
  );
  const contadas = lineas.filter((l) => l.contado !== null).length;
  const costo = (l: (typeof lineas)[number]) => Number(l.costo_unitario ?? 0);
  const faltan = lineas.filter((l) => (l.diferenciaLocal ?? 0) < 0);
  const sobran = lineas.filter((l) => (l.diferenciaLocal ?? 0) > 0);
  const valorFaltan = faltan.reduce((t, l) => t + -l.diferenciaLocal! * costo(l), 0);
  const valorSobran = sobran.reduce((t, l) => t + l.diferenciaLocal! * costo(l), 0);
  const verCostos = f.valor_faltante !== null;

  const actualizar = (d: FisicoDetalle, mensaje?: string) => {
    queryClient.setQueryData(["inventario", "fisico", f.id], d);
    void queryClient.invalidateQueries({ queryKey: ["inventario"] });
    void queryClient.invalidateQueries({ queryKey: ["productos"] });
    if (mensaje) toast.success(mensaje);
  };

  const guardar = useMutation({
    mutationFn: async () => {
      const items = Object.entries(editado).map(([detalleId, texto]) => {
        const linea = f.detalles.find((d) => d.id === Number(detalleId))!;
        if (texto.trim() && !cantidadValida(texto, true)) throw new Error(`Revisa lo contado de ${linea.producto}`);
        return { detalle_id: Number(detalleId), stock_contado: texto.trim() ? normalizarNumero(texto) : null };
      });
      return items.length ? inventarioService.guardarConteo(f.id, items) : f;
    },
    onSuccess: (d) => {
      setEditado({});
      actualizar(d, "Avance guardado");
    },
    onError: (e) => toast.error(mensajeError(e)),
  });
  const accion = useMutation({
    mutationFn: async ({ fn }: { fn: () => Promise<FisicoDetalle>; exito: string }) => {
      if (pendientes) {
        await guardar.mutateAsync();
      }
      return fn();
    },
    onSuccess: (d, { exito }) => {
      setRechazando(false);
      actualizar(d, exito);
    },
    onError: (e) => toast.error(mensajeError(e), { duration: e instanceof ApiError && e.codigo === "recontar" ? 12000 : 6000 }),
  });

  /** Escanear suma 1 a la línea del producto (si tiene varios lotes, a la primera; luego se corrige a mano). */
  const escanear = async (codigo: string) => {
    if (!codigo.trim()) return;
    try {
      const { producto, presentacion } = await productosService.porCodigo(codigo);
      const linea = f.detalles.find((d) => d.producto_id === producto.id);
      if (!linea) {
        toast.error(`${producto.nombre} no está en este conteo`);
        return;
      }
      const suma = presentacion ? Number(presentacion.factor) : 1;
      const actual = Number(normalizarNumero(valorDe(linea.id, linea.stock_contado) || "0")) || 0;
      setEditado((e) => ({ ...e, [linea.id]: String(actual + suma) }));
      filas.current[linea.id]?.scrollIntoView({ block: "center", behavior: "smooth" });
    } catch (error) {
      toast.error(error instanceof ApiError && error.status === 404 ? `No hay ningún producto con el código ${codigo}` : mensajeError(error));
    } finally {
      setEscaneo("");
    }
  };

  const estado = ESTADOS_FISICO[f.estado];
  const neto = valorSobran - valorFaltan;

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div>
          <Link href="/inventario/fisicos" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
            Inventario › Inventario físico
          </Link>
          <h1 className="flex flex-wrap items-center gap-2.5 text-[24px] font-extrabold tracking-[-0.02em]">
            {f.descripcion || "Conteo"} <span className="text-lg font-semibold text-muted-foreground tabular">{f.numero}</span>
            <Pildora tono={estado.tono}>{estado.texto}</Pildora>
          </h1>
        </div>
        <div className="w-full lg:ml-auto lg:w-64">
          <div className="flex justify-between text-[13px] font-bold tabular">
            <span>Contados</span>
            <span>
              {contadas} de {lineas.length}
            </span>
          </div>
          <div className="mt-1.5 h-2 rounded-full bg-input/60">
            <div className="h-2 rounded-full bg-primary transition-[width]" style={{ width: `${(contadas / Math.max(lineas.length, 1)) * 100}%` }} />
          </div>
        </div>
      </div>

      {f.motivo_rechazo && enProceso && (
        <p className="mb-4 rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
          Devuelto para recontar: {f.motivo_rechazo}
        </p>
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_310px]">
        <section className="tarjeta overflow-hidden">
          {puedeContar && (
            <div className="p-4">
              <label className="flex h-11 items-center gap-2.5 rounded-xl border-2 border-primary bg-muted px-3">
                <Barcode className="size-5 flex-none" />
                <input
                  value={escaneo}
                  onChange={(e) => setEscaneo(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      void escanear(escaneo);
                    }
                  }}
                  autoFocus
                  placeholder="Escanea cada unidad: el contador sube solo"
                  aria-label="Escanear para contar"
                  className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                />
              </label>
            </div>
          )}
          <div className="scrollbar-fino max-h-[65vh] overflow-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="sticky top-0 z-10">
                <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                  <th className="h-10 px-4">Producto</th>
                  <th className="px-3 text-right">Sistema al contar</th>
                  <th className="px-3 text-center">Contado</th>
                  <th className="px-3 text-center">Diferencia</th>
                  {verCostos && <th className="px-4 text-right">Valor</th>}
                </tr>
              </thead>
              <tbody>
                {lineas.map((l) => {
                  const dif = l.diferenciaLocal;
                  return (
                    <tr
                      key={l.id}
                      className={cn("border-t border-rule", dif !== null && dif < 0 && "bg-pill-negative-bg/40", dif !== null && dif > 0 && "bg-pill-positive-bg/40")}
                    >
                      <td className="px-4 py-2">
                        <p className="font-bold">{l.producto}</p>
                        {l.lote && (
                          <p className="text-xs text-muted-foreground tabular">
                            Lote {l.lote}
                            {l.fecha_vencimiento && ` · vence ${fecha(l.fecha_vencimiento)}`}
                          </p>
                        )}
                      </td>
                      <td className="px-3 text-right tabular">{cantidad(l.stock_sistema)}</td>
                      <td className="px-3 text-center">
                        {puedeContar ? (
                          <input
                            ref={(el) => {
                              filas.current[l.id] = el;
                            }}
                            value={l.texto}
                            onChange={(e) => setEditado((x) => ({ ...x, [l.id]: e.target.value }))}
                            inputMode="decimal"
                            placeholder="—"
                            aria-label={`Contado de ${l.producto}`}
                            className={cn(
                              "h-9 w-20 rounded-[10px] border-[1.5px] border-input bg-transparent text-center text-[15px] font-extrabold tabular outline-none focus-visible:ring-2 focus-visible:ring-ring",
                              l.contado === null && "border-dashed border-primary",
                            )}
                          />
                        ) : (
                          <b className="tabular">{l.contado === null ? "—" : cantidad(l.contado)}</b>
                        )}
                      </td>
                      <td className="px-3 text-center">
                        {dif === null ? (
                          <span className="text-xs font-bold text-amarillo-tinta">Falta contar</span>
                        ) : (
                          <span
                            className={cn(
                              "inline-flex h-[26px] min-w-11 items-center justify-center rounded-lg px-1.5 text-[13px] font-extrabold tabular",
                              dif < 0 ? "bg-pill-negative-bg text-pill-negative-ink" : dif > 0 ? "bg-pill-positive-bg text-pill-positive-ink" : "bg-pill-neutral-bg text-pill-neutral-ink",
                            )}
                          >
                            {dif > 0 ? "+" : dif < 0 ? "−" : ""}
                            {cantidad(Math.abs(dif))}
                          </span>
                        )}
                      </td>
                      {verCostos && (
                        <td className={cn("px-4 text-right font-bold tabular", dif && dif < 0 ? "text-destructive" : dif ? "text-positive" : "text-muted-foreground")}>
                          {dif ? `${dif < 0 ? "−" : "+"}${soles(Math.abs(dif) * costo(l))}` : "—"}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <div className="flex flex-col gap-4">
          <section className="tarjeta bg-navy p-5 text-white dark:bg-navy-2">
            <p className="text-[13px] text-navy-ink">Diferencia neta</p>
            <p className={cn("mt-1 text-[32px] leading-[1.15] font-extrabold tracking-[-0.02em] tabular", neto < 0 && "text-[#ffb3aa]", neto > 0 && "text-[#7ee2a8]")}>
              {verCostos ? `${neto < 0 ? "−" : ""}${soles(Math.abs(neto))}` : `${faltan.length + sobran.length} líneas`}
            </p>
            <dl className="mt-2 text-sm">
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Faltan</dt>
                <dd className="font-bold text-[#ffb3aa] tabular">
                  {cantidad(faltan.reduce((t, l) => t - l.diferenciaLocal!, 0))} und{verCostos && ` · ${soles(valorFaltan)}`}
                </dd>
              </div>
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Sobran</dt>
                <dd className="font-bold text-[#7ee2a8] tabular">
                  {cantidad(sobran.reduce((t, l) => t + l.diferenciaLocal!, 0))} und{verCostos && ` · ${soles(valorSobran)}`}
                </dd>
              </div>
              <div className="flex justify-between border-t border-sidebar-border py-2">
                <dt className="text-navy-ink">Sin diferencia</dt>
                <dd className="font-bold tabular">{lineas.filter((l) => l.diferenciaLocal === 0).length} líneas</dd>
              </div>
            </dl>
          </section>
          <section className="tarjeta bg-aviso-fondo p-5 text-[13px] leading-relaxed text-muted-foreground">
            <b className="text-foreground">{f.estado === "APLICADO" ? "Aplicado" : "Al aprobar"}</b>
            <p className="mt-1">
              Se aplica solo la diferencia (contado − lo que había al contar). Si se vendió algo durante el conteo, esas ventas
              se respetan: nada se pisa. Los productos con lotes se cuentan por lote. Lo no contado no cambia.
            </p>
          </section>

          {puedeContar && (
            <div className="flex flex-col gap-2">
              <Button
                className="h-12 text-[15px] font-extrabold"
                disabled={accion.isPending || contadas === 0}
                onClick={() => accion.mutate({ fn: () => inventarioService.enviarFisico(f.id), exito: "Enviado a aprobación" })}
              >
                {accion.isPending && <Loader2 className="animate-spin" />} Enviar a aprobación
              </Button>
              <Button variant="outline" className="h-10" disabled={guardar.isPending || !pendientes} onClick={() => guardar.mutate()}>
                {pendientes ? `Guardar avance (${pendientes})` : "Avance guardado"}
              </Button>
              <Button
                variant="ghost"
                className="text-destructive"
                disabled={accion.isPending}
                onClick={() => accion.mutate({ fn: () => inventarioService.cancelarFisico(f.id), exito: "Conteo cancelado" })}
              >
                Cancelar conteo
              </Button>
            </div>
          )}
          {f.estado === "PENDIENTE_APROBACION" && tiene("inventario.aprobar_ajustes") && (
            <div className="flex flex-col gap-2">
              {!f.puede_aprobar && (
                <p className="rounded-xl bg-aviso-fondo px-4 py-3 text-[13px] font-semibold text-amarillo-tinta">
                  {f.usuario_id === usuario?.id ? "Tú hiciste este conteo: debe aprobarlo otra persona." : "No puedes aprobar este conteo."}
                </p>
              )}
              <Button
                className="h-12 text-[15px] font-extrabold"
                disabled={!f.puede_aprobar || accion.isPending}
                onClick={() => accion.mutate({ fn: () => inventarioService.aprobarFisico(f.id), exito: "Conteo aplicado: el stock se corrigió" })}
              >
                {accion.isPending ? <Loader2 className="animate-spin" /> : <Check />} Aprobar y aplicar
              </Button>
              <Button variant="outline" className="h-10" onClick={() => setRechazando(true)}>
                Devolver para recontar
              </Button>
            </div>
          )}
        </div>
      </div>

      <RechazoDialog
        abierto={rechazando}
        titulo="Devolver para recontar"
        descripcion="El conteo vuelve a «En proceso» y quien lo hizo verá el motivo."
        boton="Devolver"
        enviando={accion.isPending}
        onCerrar={() => setRechazando(false)}
        onConfirmar={(motivo) => accion.mutate({ fn: () => inventarioService.rechazarFisico(f.id, motivo), exito: "Devuelto para recontar" })}
      />
    </>
  );
}
