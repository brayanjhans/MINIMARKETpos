"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Loader2, Printer } from "lucide-react";
import Link from "next/link";
import { use, useCallback, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Pildora } from "@/components/comunes/Pildora";
import { AutorizacionDialog, type PedidoAutorizacion } from "@/components/pos/AutorizacionDialog";
import { ImprimirTicket, Ticket } from "@/components/pos/Ticket";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, mensajeError, nuevaClave } from "@/lib/api";
import { fechaHora, soles } from "@/lib/utils";
import { ventasService } from "@/services/ventas.service";
import type { VentaDetalle } from "@/types/ventas";

export default function VentaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="pos.vender">
      <Detalle id={Number(id)} />
    </RequierePermiso>
  );
}

function Detalle({ id }: { id: number }) {
  const venta = useQuery({ queryKey: ["ventas", id], queryFn: () => ventasService.obtener(id) });
  const [imprimir, setImprimir] = useState<VentaDetalle | null>(null);
  const [anulando, setAnulando] = useState(false);
  const listo = useCallback(() => setImprimir(null), []);

  if (venta.isLoading) return <Loader2 className="size-6 animate-spin text-muted-foreground" />;
  if (!venta.data) return <p className="text-sm text-muted-foreground">{mensajeError(venta.error)}</p>;
  const v = venta.data;

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[13px] text-muted-foreground">
            <Link href="/ventas" className="hover:underline">
              Tickets
            </Link>{" "}
            ›
          </p>
          <h1 className="flex flex-wrap items-center gap-3 text-[26px] leading-8 font-extrabold tracking-[-0.02em] tabular">
            {v.comprobante}
            {v.estado === "ANULADA" ? <Pildora tono="negativo">Anulada</Pildora> : <Pildora tono="positivo">Pagada</Pildora>}
          </h1>
          <p className="text-sm text-muted-foreground">
            {fechaHora(v.fecha)} · {v.caja} · {v.usuario}
          </p>
        </div>
        <div className="flex gap-2">
          {v.puede_anular && (
            <Button variant="outline" className="text-destructive" onClick={() => setAnulando(true)}>
              <Ban /> Anular
            </Button>
          )}
          <Button onClick={() => setImprimir(v)}>
            <Printer /> Imprimir ticket
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[auto_minmax(0,1fr)]">
        <div className="tarjeta self-start overflow-hidden p-3">
          <Ticket venta={v} className="rounded-lg" />
        </div>
        <div className="flex flex-col gap-3">
          {v.estado === "ANULADA" && (
            <section className="tarjeta bg-pill-negative-bg p-5 text-pill-negative-ink">
              <b>Anulada por {v.anulada_por}</b>
              <p className="text-sm">
                {v.fecha_anulacion && fechaHora(v.fecha_anulacion)} · {v.motivo_anulacion}
              </p>
              <p className="mt-1 text-xs">El stock volvió al almacén y el monto no cuenta en el arqueo.</p>
            </section>
          )}
          {v.es_credito && (
            <section className="tarjeta bg-aviso-fondo p-5 text-sm">
              <b>Venta al fiado</b> a {v.cliente}. La deuda se cobra desde Clientes (Fase 5).
            </section>
          )}
          {!v.puede_anular && v.estado === "COMPLETADA" && (
            <p className="text-[13px] text-muted-foreground">
              El turno de caja de esta venta ya se cerró: si el cliente devuelve algo, se registra como devolución.
            </p>
          )}
          <p className="text-sm text-muted-foreground">
            Total cobrado <b className="text-foreground tabular">{soles(v.a_cobrar)}</b>
          </p>
        </div>
      </div>

      <Anular venta={v} abierto={anulando} onCerrar={() => setAnulando(false)} />
      <ImprimirTicket venta={imprimir} onListo={listo} />
    </>
  );
}

function Anular({ venta, abierto, onCerrar }: { venta: VentaDetalle; abierto: boolean; onCerrar: () => void }) {
  const queryClient = useQueryClient();
  const { tiene } = useAuth();
  const [clave] = useState(nuevaClave);
  const [motivo, setMotivo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [pedido, setPedido] = useState<PedidoAutorizacion | null>(null);

  const anular = async (autorizacion: string | null) => {
    setEnviando(true);
    setError(null);
    try {
      await ventasService.anular(venta.id, motivo.trim(), autorizacion, clave);
      toast.success(`Venta ${venta.comprobante} anulada`);
      void queryClient.invalidateQueries({ queryKey: ["ventas"] });
      void queryClient.invalidateQueries({ queryKey: ["caja"] });
      void queryClient.invalidateQueries({ queryKey: ["pos", "catalogo"] });
      onCerrar();
    } catch (e) {
      if (e instanceof ApiError && e.datos?.autorizable) setPedido({ permiso: "pos.anular_venta", motivo: e.message });
      else setError(mensajeError(e));
    } finally {
      setEnviando(false);
    }
  };

  const confirmar = () => {
    if (motivo.trim().length < 5) return setError("Escribe por qué se anula (mínimo 5 letras)");
    if (!tiene("pos.anular_venta")) return setPedido({ permiso: "pos.anular_venta", motivo: "Anular una venta necesita autorización" });
    void anular(null);
  };

  return (
    <>
      <Dialog open={abierto && !pedido} onOpenChange={(a) => !a && onCerrar()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Anular {venta.comprobante}</DialogTitle>
            <DialogDescription>
              Se devuelve el stock y {soles(venta.a_cobrar)} deja de contar en la caja. Entrega el dinero al cliente.
            </DialogDescription>
          </DialogHeader>
          <div className="my-2 flex flex-col gap-1.5">
            <Label htmlFor="motivo-anular">Motivo</Label>
            <Input id="motivo-anular" value={motivo} onChange={(e) => setMotivo(e.target.value)} maxLength={300} autoFocus />
          </div>
          {error && <p className="rounded-xl bg-pill-negative-bg px-3 py-2 text-sm font-semibold text-pill-negative-ink">{error}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={onCerrar}>
              Volver
            </Button>
            <Button variant="destructive" disabled={enviando} onClick={confirmar}>
              {enviando && <Loader2 className="animate-spin" />} Anular venta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <AutorizacionDialog
        pedido={pedido}
        onCerrar={() => setPedido(null)}
        onAutorizado={(token, supervisor) => {
          setPedido(null);
          toast.success(`Autorizó ${supervisor}`);
          void anular(token);
        }}
      />
    </>
  );
}
