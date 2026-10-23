"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Wallet } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError, nuevaClave } from "@/lib/api";
import { cn, fechaYHora, soles } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";

const MONTO = /^\d{1,6}([.,]\d{1,2})?$/;

/** Apertura del turno: elegir una caja libre y contar el sencillo con que empieza. */
export function AbrirCaja({ className }: { className?: string }) {
  const { tiene } = useAuth();
  const queryClient = useQueryClient();
  const [clave] = useState(nuevaClave);
  const [cajaId, setCajaId] = useState<number | null>(null);
  const [monto, setMonto] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [error, setError] = useState<string | null>(null);
  const cajas = useQuery({ queryKey: ["caja", "cajas"], queryFn: cajaService.cajas });
  const libres = (cajas.data ?? []).filter((c) => !c.sesion_id);
  const elegida = cajaId ?? (libres.length === 1 ? libres[0]!.id : null);

  const abrir = useMutation({
    mutationFn: () => {
      if (!elegida) throw new Error("Elige la caja que vas a usar");
      if (!MONTO.test(monto.trim())) throw new Error("Escribe con cuánto sencillo empiezas (puede ser 0)");
      return cajaService.abrir(
        { caja_id: elegida, monto_inicial: monto.trim().replace(",", "."), observaciones: observaciones.trim() || null },
        clave,
      );
    },
    onSuccess: (s) => {
      toast.success(`${s.caja} abierta con ${soles(s.monto_inicial)}`);
      void queryClient.invalidateQueries({ queryKey: ["caja"] });
    },
    onError: (e) => setError(mensajeError(e)),
  });

  if (!tiene("caja.abrir")) {
    return (
      <div className={cn("tarjeta p-6 text-center text-sm text-muted-foreground", className)}>
        No tienes una caja abierta y tu usuario no puede abrir caja. Pide a un supervisor que la abra.
      </div>
    );
  }

  return (
    <form
      className={cn("tarjeta flex flex-col gap-4 p-6", className)}
      onSubmit={(e) => {
        e.preventDefault();
        setError(null);
        abrir.mutate();
      }}
    >
      <div className="flex items-center gap-3">
        <span className="grid size-11 place-items-center rounded-xl bg-primary text-primary-foreground">
          <Wallet className="size-5" />
        </span>
        <div>
          <h2 className="text-lg font-extrabold">Abrir caja</h2>
          <p className="text-sm text-muted-foreground">Sin caja abierta no se puede vender.</p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Label>Caja</Label>
        {cajas.isLoading ? (
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {(cajas.data ?? []).map((c) => {
              const ocupada = !!c.sesion_id;
              return (
                <button
                  key={c.id}
                  type="button"
                  disabled={ocupada}
                  aria-pressed={elegida === c.id}
                  onClick={() => setCajaId(c.id)}
                  className={cn(
                    "rounded-xl border-2 p-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-60",
                    elegida === c.id ? "border-primary bg-aviso-fondo" : "border-border hover:bg-muted",
                  )}
                >
                  <p className="font-bold">{c.nombre}</p>
                  <p className="text-xs text-muted-foreground">
                    {ocupada ? `En uso por ${c.abierta_por} desde ${fechaYHora(c.abierta_desde!).hora}` : c.descripcion || "Libre"}
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="monto-inicial">Sencillo con que empiezas (S/)</Label>
        <Input
          id="monto-inicial"
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          inputMode="decimal"
          placeholder="0.00"
          className="h-12 text-lg font-bold tabular"
          autoFocus
          autoComplete="off"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="obs-apertura">Observación (opcional)</Label>
        <Input id="obs-apertura" value={observaciones} onChange={(e) => setObservaciones(e.target.value)} maxLength={300} />
      </div>
      {error && <p className="rounded-xl bg-pill-negative-bg px-4 py-2.5 text-sm font-semibold text-pill-negative-ink">{error}</p>}
      <Button type="submit" className="h-12 text-[15px] font-extrabold" disabled={abrir.isPending}>
        {abrir.isPending && <Loader2 className="animate-spin" />} Abrir caja
      </Button>
    </form>
  );
}
