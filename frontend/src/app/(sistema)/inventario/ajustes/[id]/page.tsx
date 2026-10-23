"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { use, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Pildora } from "@/components/comunes/Pildora";
import { RechazoDialog } from "@/components/inventario/RechazoDialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";
import { cantidad, ESTADOS_AJUSTE } from "@/lib/inventario";
import { cn, fecha, fechaHora, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { AjusteDetalle } from "@/types/inventario";

export default function AjustePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="inventario.ver">
      <Ajuste id={Number(id)} />
    </RequierePermiso>
  );
}

function Ajuste({ id }: { id: number }) {
  const { tiene, usuario } = useAuth();
  const queryClient = useQueryClient();
  const [rechazando, setRechazando] = useState(false);
  const consulta = useQuery({ queryKey: ["inventario", "ajuste", id], queryFn: () => inventarioService.ajuste(id) });

  const accion = useMutation({
    mutationFn: ({ fn }: { fn: () => Promise<AjusteDetalle>; exito: string }) => fn(),
    onSuccess: (ajuste, { exito }) => {
      queryClient.setQueryData(["inventario", "ajuste", id], ajuste);
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
      toast.success(exito);
      setRechazando(false);
    },
    onError: (error) => toast.error(mensajeError(error), { duration: 8000 }),
  });

  if (consulta.isLoading) return <Skeleton className="h-80 w-full rounded-[18px]" />;
  if (!consulta.data)
    return (
      <p className="tarjeta p-6 text-sm">
        {mensajeError(consulta.error)}{" "}
        <Link href="/inventario/ajustes" className="font-bold underline">
          Volver
        </Link>
      </p>
    );
  const a = consulta.data;
  const estado = ESTADOS_AJUSTE[a.estado];
  const esAutor = a.usuario_id === usuario?.id;
  const abierto = a.estado === "BORRADOR" || a.estado === "PENDIENTE_APROBACION";

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div>
          <Link href="/inventario/ajustes" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
            Inventario › Ajustes ›
          </Link>
          <h1 className="flex flex-wrap items-center gap-2.5 text-[24px] font-extrabold tracking-[-0.02em]">
            {a.motivo} <span className="text-lg font-semibold text-muted-foreground tabular">{a.numero}</span>
            <Pildora tono={estado.tono}>{estado.texto}</Pildora>
          </h1>
        </div>
        <div className="flex flex-wrap gap-2 sm:ml-auto">
          {abierto && (esAutor || tiene("inventario.aprobar_ajustes")) && (
            <Button variant="outline" disabled={accion.isPending} onClick={() => accion.mutate({ fn: () => inventarioService.anularAjuste(id), exito: "Ajuste anulado" })}>
              Anular
            </Button>
          )}
          {a.estado === "BORRADOR" && esAutor && (
            <Button disabled={accion.isPending} onClick={() => accion.mutate({ fn: () => inventarioService.enviarAjuste(id), exito: "Enviado a aprobación" })}>
              Enviar a aprobación
            </Button>
          )}
          {a.estado === "PENDIENTE_APROBACION" && tiene("inventario.aprobar_ajustes") && (
            <>
              <Button variant="outline" className="text-destructive" disabled={accion.isPending} onClick={() => setRechazando(true)}>
                Rechazar
              </Button>
              <Button
                disabled={!a.puede_aprobar || accion.isPending}
                title={a.puede_aprobar ? undefined : "Debe aprobarlo otra persona"}
                onClick={() => accion.mutate({ fn: () => inventarioService.aprobarAjuste(id), exito: "Ajuste aprobado: el stock se actualizó" })}
              >
                {accion.isPending ? <Loader2 className="animate-spin" /> : <Check />} Aprobar y aplicar
              </Button>
            </>
          )}
        </div>
      </div>

      {a.estado === "PENDIENTE_APROBACION" && !a.puede_aprobar && tiene("inventario.aprobar_ajustes") && (
        <p className="mb-4 rounded-xl bg-aviso-fondo px-4 py-3 text-sm font-semibold text-amarillo-tinta">
          Tú registraste este ajuste: debe aprobarlo otra persona con permiso de aprobar.
        </p>
      )}
      {a.motivo_rechazo && (
        <p className="mb-4 rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
          Rechazado por {a.aprobado_por}: {a.motivo_rechazo}
        </p>
      )}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="tarjeta overflow-hidden">
          <div className="scrollbar-fino overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                  <th className="h-10 px-4">Producto</th>
                  <th className="px-3">Lote</th>
                  <th className="px-3 text-right">Cantidad</th>
                  <th className="px-4 text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {a.detalles.map((d) => (
                  <tr key={d.id} className="h-14 border-t border-rule">
                    <td className="px-4">
                      <Link href={`/productos/${d.producto_id}`} className="font-bold hover:underline">
                        {d.producto}
                      </Link>
                      {d.costo_unitario !== null && <p className="text-xs text-muted-foreground tabular">{soles(d.costo_unitario)} c/u</p>}
                    </td>
                    <td className="px-3 text-[13px] tabular">
                      {d.lote ? `${d.lote}${d.fecha_vencimiento ? ` · vence ${fecha(d.fecha_vencimiento)}` : ""}` : "—"}
                    </td>
                    <td className={cn("px-3 text-right font-extrabold tabular", Number(d.cantidad) < 0 ? "text-destructive" : "text-positive")}>
                      {Number(d.cantidad) > 0 && "+"}
                      {cantidad(d.cantidad)}
                    </td>
                    <td className="px-4 text-right font-bold tabular">{d.valor === null ? "—" : soles(d.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="tarjeta flex flex-col gap-3 p-5 text-sm">
          {a.valor !== null && (
            <div>
              <p className="text-[13px] text-muted-foreground">{a.es_merma ? "Pérdida (merma)" : "Valor"}</p>
              <p className={cn("text-[28px] font-extrabold tabular", Number(a.valor) < 0 && "text-destructive")}>{soles(Math.abs(Number(a.valor)))}</p>
            </div>
          )}
          <Dato titulo="Almacén" valor={a.almacen} />
          <Dato titulo="Registró" valor={`${a.usuario ?? "—"} · ${fechaHora(a.creado_en)}`} />
          {a.fecha_envio && <Dato titulo="Enviado a aprobación" valor={fechaHora(a.fecha_envio)} />}
          {a.estado === "APLICADO" && <Dato titulo="Aprobó y aplicó" valor={`${a.aprobado_por} · ${fechaHora(a.fecha_aplicacion)}`} />}
          {a.observaciones && <Dato titulo="Observación" valor={a.observaciones} />}
          {a.estado === "APLICADO" && (
            <p className="rounded-xl bg-pill-positive-bg px-3 py-2 text-[13px] font-semibold text-pill-positive-ink">
              Aplicado: cada producto tiene su movimiento en el kardex. Un ajuste aplicado no se borra; si hubo un error,
              registra otro en sentido contrario.
            </p>
          )}
        </section>
      </div>

      <RechazoDialog
        abierto={rechazando}
        titulo={`Rechazar ${a.numero}`}
        descripcion="El stock no cambia. El motivo queda registrado y lo verá quien registró el ajuste."
        boton="Rechazar ajuste"
        enviando={accion.isPending}
        onCerrar={() => setRechazando(false)}
        onConfirmar={(motivo) => accion.mutate({ fn: () => inventarioService.rechazarAjuste(id, motivo), exito: "Ajuste rechazado" })}
      />
    </>
  );
}

function Dato({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div className="border-t border-rule pt-2.5">
      <p className="text-xs text-muted-foreground">{titulo}</p>
      <p className="font-semibold">{valor}</p>
    </div>
  );
}
