"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Lock } from "lucide-react";
import Link from "next/link";
import { use, useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { PildoraDiferencia } from "@/components/caja/PildoraDiferencia";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { mensajeError, nuevaClave } from "@/lib/api";
import { METODOS, aCentimos, desdeCentimos } from "@/lib/ventas";
import { cn, soles } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";
import type { MetodoPago, SesionDetalle } from "@/types/ventas";

const DECLARABLES: MetodoPago[] = ["TARJETA", "YAPE", "PLIN", "TRANSFERENCIA"];
const MONTO = /^\d{1,6}([.,]\d{1,2})?$/;

export default function CerrarCajaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="caja.cerrar">
      <Cerrar id={Number(id)} />
    </RequierePermiso>
  );
}

function Cerrar({ id }: { id: number }) {
  const queryClient = useQueryClient();
  const [clave] = useState(nuevaClave);
  const [conteo, setConteo] = useState<Record<string, string>>({});
  const [declarados, setDeclarados] = useState<Partial<Record<MetodoPago, string>>>({});
  const [observaciones, setObservaciones] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<SesionDetalle | null>(null);
  const sesion = useQuery({ queryKey: ["caja", "sesion", id], queryFn: () => cajaService.sesion(id) });

  const contado = useMemo(
    () =>
      Object.entries(conteo).reduce((t, [d, n]) => t + (/^\d{1,5}$/.test(n.trim()) ? aCentimos(d) * Number(n) : 0), 0),
    [conteo],
  );
  // Métodos que tuvieron ventas en el turno: el cajero declara cuánto dicen los vouchers o la app
  const usados = (sesion.data?.metodos ?? []).map((m) => m.metodo).filter((m) => DECLARABLES.includes(m));

  const cerrar = useMutation({
    mutationFn: () => {
      if (Object.values(conteo).some((n) => n.trim() && !/^\d{1,5}$/.test(n.trim()))) throw new Error("Revisa las cantidades del conteo");
      if (Object.values(declarados).some((m) => m?.trim() && !MONTO.test(m.trim()))) throw new Error("Revisa los montos declarados");
      return cajaService.cerrar(
        id,
        {
          arqueo: Object.entries(conteo)
            .filter(([, n]) => /^\d{1,5}$/.test(n.trim()) && Number(n) > 0)
            .map(([denominacion, n]) => ({ denominacion, cantidad: Number(n) })),
          declarados: (Object.entries(declarados) as [MetodoPago, string][])
            .filter(([, m]) => m.trim())
            .map(([metodo, monto]) => ({ metodo, monto: monto.trim().replace(",", ".") })),
          observaciones: observaciones.trim() || null,
        },
        clave,
      );
    },
    onSuccess: (s) => {
      setResultado(s);
      void queryClient.invalidateQueries({ queryKey: ["caja"] });
    },
    onError: (e) => setError(mensajeError(e)),
  });

  if (sesion.isLoading) return <Loader2 className="size-6 animate-spin text-muted-foreground" />;
  if (!sesion.data) return <p className="text-sm text-muted-foreground">{mensajeError(sesion.error)}</p>;
  const s = resultado ?? sesion.data;

  if (s.estado === "CERRADA") return <Resultado sesion={s} />;

  return (
    <>
      <div className="mb-5">
        <p className="text-[13px] text-muted-foreground">
          <Link href="/caja" className="hover:underline">
            Caja
          </Link>{" "}
          ›
        </p>
        <h1 className="text-[26px] leading-8 font-extrabold tracking-[-0.02em]">Cerrar {s.caja}</h1>
        <p className="text-sm text-muted-foreground">
          Cuenta los billetes y monedas que hay en el cajón. El sistema compara al final: así el arqueo es honesto.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section className="tarjeta p-5">
          <h2 className="mb-3 font-extrabold">Efectivo en el cajón</h2>
          <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
            {s.denominaciones.map((d) => {
              const n = conteo[d] ?? "";
              const sub = /^\d{1,5}$/.test(n.trim()) ? aCentimos(d) * Number(n) : 0;
              const billete = Number(d) >= 10;
              return (
                <div key={d} className="grid grid-cols-[96px_90px_1fr] items-center gap-3">
                  <span
                    className={cn(
                      "inline-flex h-9 items-center justify-center rounded-lg text-sm font-extrabold tabular",
                      billete ? "bg-p-verde text-p-verde-t" : "bg-p-amarillo text-p-amarillo-t",
                    )}
                  >
                    {soles(d)}
                  </span>
                  <Input
                    value={n}
                    onChange={(e) => setConteo((c) => ({ ...c, [d]: e.target.value }))}
                    inputMode="numeric"
                    placeholder="0"
                    className="h-9 text-center font-bold tabular"
                    aria-label={`Cantidad de ${billete ? "billetes" : "monedas"} de ${soles(d)}`}
                  />
                  <span className="text-right text-sm text-muted-foreground tabular">{sub ? desdeCentimos(sub) : "—"}</span>
                </div>
              );
            })}
          </div>
        </section>

        <div className="flex flex-col gap-4">
          <section className="tarjeta bg-navy p-5 text-white dark:bg-navy-2">
            <p className="text-[13px] text-navy-ink">Efectivo contado</p>
            <p className="mt-1 text-[32px] leading-[1.15] font-extrabold tracking-[-0.02em] tabular">{soles(desdeCentimos(contado))}</p>
            <p className="mt-1 text-xs text-navy-ink">Incluye el sencillo con el que abriste.</p>
          </section>

          {usados.length > 0 && (
            <section className="tarjeta flex flex-col gap-3 p-5">
              <div>
                <h2 className="font-extrabold">Otros cobros del turno</h2>
                <p className="text-xs text-muted-foreground">Lo que dicen los vouchers del POS del banco o la app.</p>
              </div>
              {usados.map((m) => (
                <div key={m} className="flex items-center justify-between gap-3">
                  <Label htmlFor={`dec-${m}`} className={METODOS[m].color}>
                    {METODOS[m].texto}
                  </Label>
                  <Input
                    id={`dec-${m}`}
                    value={declarados[m] ?? ""}
                    onChange={(e) => setDeclarados((d) => ({ ...d, [m]: e.target.value }))}
                    inputMode="decimal"
                    placeholder="0.00"
                    className="h-9 w-28 text-right tabular"
                  />
                </div>
              ))}
            </section>
          )}

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="obs-cierre">Observación (opcional)</Label>
            <Input id="obs-cierre" value={observaciones} onChange={(e) => setObservaciones(e.target.value)} maxLength={300} />
          </div>
          {error && <p className="rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">{error}</p>}
          <Button
            className="h-14 text-[15px] font-extrabold"
            disabled={cerrar.isPending}
            onClick={() => {
              setError(null);
              cerrar.mutate();
            }}
          >
            {cerrar.isPending ? <Loader2 className="animate-spin" /> : <Lock />} Cerrar caja con {soles(desdeCentimos(contado))}
          </Button>
          <p className="text-center text-xs text-muted-foreground">Después de cerrar ya no se puede vender ni anular en este turno.</p>
        </div>
      </div>
    </>
  );
}

function Resultado({ sesion: s }: { sesion: SesionDetalle }) {
  const d = Number(s.diferencia ?? 0);
  return (
    <div className="mx-auto flex max-w-xl flex-col gap-4">
      <div className="tarjeta flex flex-col items-center gap-2 p-8 text-center">
        <span className={cn("grid size-14 place-items-center rounded-2xl", d === 0 ? "bg-pill-positive-bg text-pill-positive-ink" : "bg-aviso-fondo text-amarillo-tinta")}>
          <Lock className="size-6" />
        </span>
        <h1 className="text-2xl font-extrabold">{s.caja} cerrada</h1>
        <PildoraDiferencia diferencia={s.diferencia} />
        <dl className="mt-3 grid w-full grid-cols-3 gap-2 text-sm">
          <div className="rounded-xl bg-muted p-3">
            <dt className="text-xs text-muted-foreground">Esperado</dt>
            <dd className="font-extrabold tabular">{soles(s.efectivo_esperado ?? 0)}</dd>
          </div>
          <div className="rounded-xl bg-muted p-3">
            <dt className="text-xs text-muted-foreground">Contado</dt>
            <dd className="font-extrabold tabular">{soles(s.monto_contado ?? 0)}</dd>
          </div>
          <div className={cn("rounded-xl p-3", d < 0 ? "bg-pill-negative-bg" : d > 0 ? "bg-aviso-fondo" : "bg-pill-positive-bg")}>
            <dt className="text-xs text-muted-foreground">Diferencia</dt>
            <dd className="font-extrabold tabular">{soles(d)}</dd>
          </div>
        </dl>
      </div>
      <div className="flex justify-center gap-2">
        <Button variant="outline" asChild>
          <Link href={`/caja/${s.id}`}>Ver el detalle del turno</Link>
        </Button>
        <Button asChild>
          <Link href="/caja">Volver a Caja</Link>
        </Button>
      </div>
    </div>
  );
}
