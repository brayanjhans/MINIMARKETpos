"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { use, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Pildora } from "@/components/comunes/Pildora";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { mensajeError } from "@/lib/api";
import { cantidad, cantidadValida, ESTADOS_TRANSFERENCIA, normalizarNumero } from "@/lib/inventario";
import { cn, fecha, fechaHora, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { TransferenciaDetalle } from "@/types/inventario";

export default function TransferenciaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="inventario.ver">
      <Transferencia id={Number(id)} />
    </RequierePermiso>
  );
}

function Transferencia({ id }: { id: number }) {
  const queryClient = useQueryClient();
  const consulta = useQuery({ queryKey: ["inventario", "transferencia", id], queryFn: () => inventarioService.transferencia(id) });
  // Lo recibido por línea (por defecto, todo lo enviado) y el motivo si falta algo
  const [recibido, setRecibido] = useState<Record<number, string>>({});
  const [motivos, setMotivos] = useState<Record<number, string>>({});
  const [confirmarAnular, setConfirmarAnular] = useState(false);

  const terminar = (t: TransferenciaDetalle, mensaje: string) => {
    queryClient.setQueryData(["inventario", "transferencia", id], t);
    void queryClient.invalidateQueries({ queryKey: ["inventario"] });
    void queryClient.invalidateQueries({ queryKey: ["productos"] });
    toast.success(mensaje);
  };
  const recibir = useMutation({
    mutationFn: (t: TransferenciaDetalle) => {
      const detalles = t.detalles.map((d) => {
        const valor = recibido[d.id] ?? String(Number(d.cantidad));
        if (!cantidadValida(valor, true)) throw new Error(`Revisa lo recibido de ${d.producto}`);
        if (Number(normalizarNumero(valor)) > Number(d.cantidad)) throw new Error(`De ${d.producto} se enviaron ${cantidad(d.cantidad)}`);
        return { detalle_id: d.id, cantidad_recibida: normalizarNumero(valor), motivo_faltante: motivos[d.id]?.trim() || null };
      });
      return inventarioService.recibirTransferencia(id, detalles);
    },
    onSuccess: (t) => terminar(t, `${t.numero} recibida: el stock se sumó a ${t.almacen_destino}`),
    onError: (e) => toast.error(mensajeError(e), { duration: 8000 }),
  });
  const anular = useMutation({
    mutationFn: () => inventarioService.anularTransferencia(id),
    onSuccess: (t) => terminar(t, `${t.numero} anulada: la mercadería volvió al origen`),
    onError: (e) => toast.error(mensajeError(e)),
  });

  if (consulta.isLoading) return <Skeleton className="h-80 w-full rounded-[18px]" />;
  if (!consulta.data) return <p className="tarjeta p-6 text-sm">{mensajeError(consulta.error)}</p>;
  const t = consulta.data;
  const pasos = [
    { texto: "Preparada", hecho: true },
    { texto: "En camino", hecho: t.estado === "EN_TRANSITO" || t.estado === "RECIBIDA" },
    { texto: "Recibida", hecho: t.estado === "RECIBIDA" },
  ];
  const recibiendo = t.puede_recibir;

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div>
          <Link href="/inventario/transferencias" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
            Inventario › Transferencias ›
          </Link>
          <h1 className="flex flex-wrap items-center gap-2.5 text-[24px] font-extrabold tracking-[-0.02em]">
            Transferencia <span className="text-lg font-semibold text-muted-foreground tabular">{t.numero}</span>
            {t.estado === "ANULADA" && <Pildora>Anulada</Pildora>}
          </h1>
        </div>
        {t.estado !== "ANULADA" && (
          <ol className="flex items-center gap-3 lg:ml-auto">
            {pasos.map((p, i) => {
              const actual = !p.hecho && (i === 0 || pasos[i - 1]!.hecho);
              return (
                <li key={p.texto} className="flex items-center gap-2.5 text-[13px] font-bold">
                  {i > 0 && <span aria-hidden className={cn("h-0.5 w-7", p.hecho || actual ? "bg-primary" : "bg-input")} />}
                  <span
                    className={cn(
                      "grid size-[26px] place-items-center rounded-full text-xs",
                      p.hecho ? "bg-positive text-white" : actual ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                    )}
                  >
                    {p.hecho ? <Check className="size-3.5" strokeWidth={3} /> : i + 1}
                  </span>
                  <span className={cn(!p.hecho && !actual && "text-muted-foreground")}>{p.texto}</span>
                </li>
              );
            })}
          </ol>
        )}
      </div>

      <div className="mb-4 flex flex-col items-stretch gap-3 md:flex-row md:items-center">
        <div className="tarjeta flex-1 px-5 py-4">
          <p className="text-xs font-semibold text-muted-foreground">Sale de</p>
          <p className="text-base font-extrabold">{t.almacen_origen}</p>
          <p className="text-[13px] text-muted-foreground">
            {t.sucursal_origen} · envió {t.usuario ?? "—"}
            {t.fecha_envio && `, ${fechaHora(t.fecha_envio)}`}
          </p>
        </div>
        <div className="mx-auto grid size-11 flex-none rotate-90 place-items-center rounded-xl bg-navy md:rotate-0">
          <ArrowRight className="size-5 text-primary" strokeWidth={2.4} />
        </div>
        <div className={cn("tarjeta flex-1 px-5 py-4", recibiendo && "border-2 border-primary bg-aviso-fondo")}>
          <p className={cn("text-xs font-semibold", recibiendo ? "font-bold text-amarillo-tinta" : "text-muted-foreground")}>Llega a</p>
          <p className="text-base font-extrabold">{t.almacen_destino}</p>
          <p className="text-[13px] text-muted-foreground">
            {t.sucursal_destino} ·{" "}
            {t.usuario_recibe ? `recibió ${t.usuario_recibe}, ${fechaHora(t.fecha_recepcion)}` : "lo confirma quien recibe"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
        <section className="tarjeta overflow-hidden">
          <h2 className="px-4 pt-4 pb-3 text-[15px] font-extrabold">
            {recibiendo ? "Recibir mercadería" : "Mercadería"}
            {recibiendo && <span className="text-[13px] font-medium text-muted-foreground"> · marca lo que realmente llegó</span>}
          </h2>
          <div className="scrollbar-fino overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                  <th className="h-10 px-4">Producto</th>
                  <th className="px-3">Lote</th>
                  <th className="px-3 text-right">Enviado</th>
                  <th className="px-3 text-center">Recibido</th>
                  <th className="px-4">Estado</th>
                </tr>
              </thead>
              <tbody>
                {t.detalles.map((d) => {
                  const valor = recibido[d.id] ?? String(Number(recibiendo ? d.cantidad : d.cantidad_recibida));
                  const falta = Number(d.cantidad) - (Number(normalizarNumero(valor)) || 0);
                  return (
                    <tr key={d.id} className={cn("border-t border-rule", falta > 0 && t.estado !== "EN_TRANSITO" && t.estado !== "PENDIENTE" && "bg-pill-negative-bg/40")}>
                      <td className="px-4 py-2.5 font-bold">{d.producto}</td>
                      <td className="px-3 text-[13px] text-muted-foreground tabular">
                        {d.lote ? `${d.lote}${d.fecha_vencimiento ? ` · ${fecha(d.fecha_vencimiento)}` : ""}` : "—"}
                      </td>
                      <td className="px-3 text-right tabular">{cantidad(d.cantidad)}</td>
                      <td className="px-3 text-center">
                        {recibiendo ? (
                          <Input
                            value={valor}
                            onChange={(e) => setRecibido((r) => ({ ...r, [d.id]: e.target.value }))}
                            inputMode="decimal"
                            aria-label={`Recibido de ${d.producto}`}
                            className={cn("mx-auto h-9 w-20 text-center font-extrabold tabular", falta > 0 && "border-destructive")}
                          />
                        ) : t.estado === "RECIBIDA" ? (
                          <b className="tabular">{cantidad(d.cantidad_recibida)}</b>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 text-[13px] font-bold">
                        {recibiendo ? (
                          falta > 0 ? (
                            <Input
                              value={motivos[d.id] ?? ""}
                              onChange={(e) => setMotivos((m) => ({ ...m, [d.id]: e.target.value }))}
                              placeholder={`Faltan ${cantidad(falta)}: ¿por qué?`}
                              maxLength={150}
                              aria-label="Motivo del faltante"
                              className="h-9 border-destructive"
                            />
                          ) : (
                            <span className="text-positive">● Completo</span>
                          )
                        ) : t.estado === "RECIBIDA" ? (
                          Number(d.faltante) > 0 ? (
                            <span className="text-destructive">
                              ● Faltaron {cantidad(d.faltante)}
                              {d.motivo_faltante && ` (${d.motivo_faltante})`}
                            </span>
                          ) : (
                            <span className="text-positive">● Completo</span>
                          )
                        ) : (
                          <span className="text-muted-foreground">{ESTADOS_TRANSFERENCIA[t.estado].texto}</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="border-t border-rule px-4 py-3 text-[13px] text-muted-foreground">
            Se envían primero los lotes que vencen antes. Lo que no llega se registra como merma del almacén de origen, con su
            motivo. Nada se pierde sin registro.
          </p>
        </section>

        <div className="flex flex-col gap-4">
          <section className="tarjeta p-5 text-sm">
            {t.valor !== null && (
              <>
                <p className="text-[13px] text-muted-foreground">Valor enviado</p>
                <p className="text-[26px] font-extrabold tabular">{soles(t.valor)}</p>
              </>
            )}
            {t.observaciones && <p className="mt-2 border-t border-rule pt-2 text-[13px]">{t.observaciones}</p>}
          </section>
          {recibiendo && (
            <Button className="h-12 text-[15px] font-extrabold" disabled={recibir.isPending} onClick={() => recibir.mutate(t)}>
              {recibir.isPending && <Loader2 className="animate-spin" />} Confirmar recepción
            </Button>
          )}
          {t.estado === "EN_TRANSITO" && !t.puede_recibir && (
            <p className="rounded-xl bg-aviso-fondo px-4 py-3 text-[13px] font-semibold text-amarillo-tinta">
              En camino. La confirma una persona de {t.sucursal_destino} al recibirla.
            </p>
          )}
          {t.puede_anular && (
            <Button
              variant="outline"
              className="h-10"
              disabled={anular.isPending}
              onClick={() => (confirmarAnular ? anular.mutate() : setConfirmarAnular(true))}
            >
              {confirmarAnular ? "¿Seguro? La mercadería vuelve al origen" : "Anular transferencia"}
            </Button>
          )}
        </div>
      </div>
    </>
  );
}
