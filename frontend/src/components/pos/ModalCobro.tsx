"use client";

import { Loader2, Plus, Trash2, UserRound } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { METODOS, aCentimos, aCobrar, desdeCentimos, sugerenciasEfectivo } from "@/lib/ventas";
import { cn, soles } from "@/lib/utils";
import type { Cliente, MetodoPago, PagoEntrada } from "@/types/ventas";

type Modo = MetodoPago | "MIXTO";

interface FilaMixta {
  metodo: MetodoPago;
  monto: string;
  recibido: string;
  referencia: string;
}

interface Props {
  abierto: boolean;
  /** Total de la venta en céntimos (antes del redondeo en efectivo) */
  total: number;
  redondeo: string;
  cliente: Cliente | null;
  enviando: boolean;
  error: string | null;
  onCobrar: (pagos: PagoEntrada[], aCobrar: string) => void;
  onElegirCliente: () => void;
  onCerrar: () => void;
}

const MODOS: Modo[] = ["EFECTIVO", "YAPE", "PLIN", "TARJETA", "TRANSFERENCIA", "CREDITO", "MIXTO"];
const MONTO = /^\d{1,6}([.,]\d{1,2})?$/;

export function ModalCobro(props: Props) {
  // El contenido se monta de nuevo en cada apertura: empieza siempre limpio
  return (
    <Dialog open={props.abierto} onOpenChange={(a) => !a && !props.enviando && props.onCerrar()}>
      <DialogContent className="sm:max-w-xl">{props.abierto && <Contenido {...props} />}</DialogContent>
    </Dialog>
  );
}

function Contenido({ total, redondeo, cliente, enviando, error, onCobrar, onElegirCliente }: Props) {
  const { tiene } = useAuth();
  const [modo, setModo] = useState<Modo>("EFECTIVO");
  const [recibido, setRecibido] = useState("");
  const [referencia, setReferencia] = useState("");
  const [filas, setFilas] = useState<FilaMixta[]>([
    { metodo: "EFECTIVO", monto: "", recibido: "", referencia: "" },
    { metodo: "YAPE", monto: "", recibido: "", referencia: "" },
  ]);

  const cobrar = modo === "EFECTIVO" ? aCobrar(total, redondeo, true) : total;
  const recibidoC = recibido.trim() ? (MONTO.test(recibido.trim()) ? aCentimos(recibido) : -1) : cobrar;
  const vuelto = modo === "EFECTIVO" && recibidoC >= cobrar ? recibidoC - cobrar : 0;
  const sumaMixta = filas.reduce((t, f) => t + (MONTO.test(f.monto.trim()) ? aCentimos(f.monto) : 0), 0);
  const faltaMixto = total - sumaMixta;
  const efectivoMixto = filas.find((f) => f.metodo === "EFECTIVO");
  const vueltoMixto =
    efectivoMixto && efectivoMixto.recibido.trim() && MONTO.test(efectivoMixto.recibido.trim())
      ? Math.max(aCentimos(efectivoMixto.recibido) - aCentimos(efectivoMixto.monto || "0"), 0)
      : 0;

  const problema = useMemo((): string | null => {
    if (modo === "CREDITO") {
      if (!cliente) return "Elige el cliente al que se le fía (F6)";
      if (!cliente.permite_credito) return `A ${cliente.nombre} no se le puede fiar`;
    }
    if (modo === "EFECTIVO" && recibidoC < cobrar) return recibidoC < 0 ? "Monto recibido no válido" : "El monto recibido no alcanza";
    if (modo === "MIXTO") {
      if (filas.some((f) => f.monto.trim() && !MONTO.test(f.monto.trim()))) return "Hay un monto no válido";
      if (filas.filter((f) => f.metodo === "EFECTIVO").length > 1) return "Usa una sola fila de efectivo";
      if (faltaMixto !== 0) return faltaMixto > 0 ? `Falta ${soles(desdeCentimos(faltaMixto))}` : "Los pagos superan el total";
      if (filas.some((f) => f.metodo === "CREDITO") && !cliente?.permite_credito) return "El fiado necesita un cliente al que se le pueda fiar";
      if (efectivoMixto?.recibido.trim() && aCentimos(efectivoMixto.recibido) < aCentimos(efectivoMixto.monto || "0"))
        return "El efectivo recibido no alcanza";
    }
    return null;
  }, [modo, cliente, recibidoC, cobrar, filas, faltaMixto, efectivoMixto]);

  const confirmar = () => {
    if (problema || enviando) return;
    let pagos: PagoEntrada[];
    if (modo === "MIXTO") {
      pagos = filas
        .filter((f) => MONTO.test(f.monto.trim()) && aCentimos(f.monto) > 0)
        .map((f) => ({
          metodo: f.metodo,
          monto: desdeCentimos(aCentimos(f.monto)),
          monto_recibido: f.metodo === "EFECTIVO" && f.recibido.trim() ? desdeCentimos(aCentimos(f.recibido)) : null,
          referencia: f.referencia.trim() || null,
        }));
    } else {
      pagos = [
        {
          metodo: modo,
          monto: desdeCentimos(cobrar),
          monto_recibido: modo === "EFECTIVO" ? desdeCentimos(recibidoC) : null,
          referencia: referencia.trim() || null,
        },
      ];
    }
    onCobrar(pagos, desdeCentimos(cobrar));
  };

  const disponibles = MODOS.filter((m) => m !== "CREDITO" || tiene("clientes.ver"));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        confirmar();
      }}
    >
      <DialogHeader>
        <DialogTitle className="flex items-baseline justify-between gap-3 pr-8">
          Cobrar
          <span className="text-[28px] font-extrabold tracking-[-0.02em] tabular">{soles(desdeCentimos(cobrar))}</span>
        </DialogTitle>
        <DialogDescription>
          {cobrar !== total ? `Redondeado en efectivo (total ${soles(desdeCentimos(total))}). ` : ""}Enter para confirmar.
        </DialogDescription>
      </DialogHeader>

      <div role="radiogroup" aria-label="Forma de pago" className="my-4 grid grid-cols-4 gap-2 sm:grid-cols-7">
        {disponibles.map((m) => (
          <button
            key={m}
            type="button"
            role="radio"
            aria-checked={modo === m}
            onClick={() => setModo(m)}
            className={cn(
              "h-12 rounded-xl border-2 text-[13px] font-bold transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
              modo === m
                ? "border-navy bg-navy text-amarillo dark:border-amarillo dark:bg-navy-2"
                : cn("border-border bg-card hover:bg-muted", m !== "MIXTO" && METODOS[m].color),
            )}
          >
            {m === "MIXTO" ? "Mixto" : METODOS[m].corto}
          </button>
        ))}
      </div>

      {modo === "EFECTIVO" && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="recibido">Con cuánto paga</Label>
            <Input
              id="recibido"
              value={recibido}
              onChange={(e) => setRecibido(e.target.value)}
              placeholder={desdeCentimos(cobrar)}
              inputMode="decimal"
              className="h-14 text-[24px] font-extrabold tabular"
              autoFocus
              autoComplete="off"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {sugerenciasEfectivo(cobrar).map((c) => (
              <Button key={c} type="button" variant="outline" className="tabular" onClick={() => setRecibido(desdeCentimos(c))}>
                {c === cobrar ? "Exacto" : soles(desdeCentimos(c))}
              </Button>
            ))}
          </div>
          <div className="flex items-center justify-between rounded-2xl bg-navy px-5 py-4 text-white dark:bg-navy-2">
            <span className="text-sm font-semibold text-navy-ink">Vuelto</span>
            <span className="text-[32px] font-extrabold text-amarillo tabular">{soles(desdeCentimos(vuelto))}</span>
          </div>
        </div>
      )}

      {(modo === "YAPE" || modo === "PLIN" || modo === "TARJETA" || modo === "TRANSFERENCIA") && (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="referencia">N.° de operación (opcional)</Label>
          <Input
            id="referencia"
            value={referencia}
            onChange={(e) => setReferencia(e.target.value)}
            maxLength={100}
            className="h-12 tabular"
            autoFocus
            autoComplete="off"
          />
          <p className="text-[13px] text-muted-foreground">Confirma en la app o el POS del banco que el pago llegó antes de cobrar.</p>
        </div>
      )}

      {modo === "CREDITO" && (
        <div className="flex items-center gap-3 rounded-2xl bg-muted p-4">
          <UserRound className="size-5 text-muted-foreground" />
          <div className="min-w-0 flex-1">
            {cliente ? (
              <>
                <p className="truncate font-bold">{cliente.nombre}</p>
                <p className="text-[13px] text-muted-foreground tabular">
                  Debe {soles(cliente.deuda)}
                  {Number(cliente.limite_credito) > 0 && ` · límite ${soles(cliente.limite_credito)}`}
                </p>
              </>
            ) : (
              <p className="font-semibold">Sin cliente</p>
            )}
          </div>
          <Button type="button" variant="outline" onClick={onElegirCliente}>
            {cliente ? "Cambiar" : "Elegir"} (F6)
          </Button>
        </div>
      )}

      {modo === "MIXTO" && (
        <div className="flex flex-col gap-2">
          {filas.map((f, i) => (
            <div key={i} className="grid grid-cols-[130px_1fr_1fr_36px] items-center gap-2">
              <select
                value={f.metodo}
                onChange={(e) => setFilas((fs) => fs.map((x, j) => (j === i ? { ...x, metodo: e.target.value as MetodoPago } : x)))}
                className="h-10 rounded-md border border-input bg-card px-2 text-sm font-semibold"
                aria-label="Método"
              >
                {(Object.keys(METODOS) as MetodoPago[]).map((m) => (
                  <option key={m} value={m}>
                    {METODOS[m].texto}
                  </option>
                ))}
              </select>
              <Input
                value={f.monto}
                onChange={(e) => setFilas((fs) => fs.map((x, j) => (j === i ? { ...x, monto: e.target.value } : x)))}
                placeholder={i === filas.length - 1 && faltaMixto > 0 ? desdeCentimos(faltaMixto + aCentimos(f.monto || "0")) : "Monto"}
                inputMode="decimal"
                className="h-10 tabular"
                aria-label="Monto"
                autoFocus={i === 0}
              />
              <Input
                value={f.metodo === "EFECTIVO" ? f.recibido : f.referencia}
                onChange={(e) =>
                  setFilas((fs) =>
                    fs.map((x, j) => (j === i ? { ...x, [f.metodo === "EFECTIVO" ? "recibido" : "referencia"]: e.target.value } : x)),
                  )
                }
                placeholder={f.metodo === "EFECTIVO" ? "Recibe" : "N.° operación"}
                inputMode={f.metodo === "EFECTIVO" ? "decimal" : "text"}
                className="h-10 tabular"
                aria-label={f.metodo === "EFECTIVO" ? "Efectivo recibido" : "Referencia"}
              />
              <Button type="button" variant="ghost" size="icon" aria-label="Quitar pago" disabled={filas.length <= 2} onClick={() => setFilas((fs) => fs.filter((_, j) => j !== i))}>
                <Trash2 />
              </Button>
            </div>
          ))}
          <div className="flex items-center justify-between">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={filas.length >= 4}
              onClick={() => setFilas((fs) => [...fs, { metodo: "TARJETA", monto: "", recibido: "", referencia: "" }])}
            >
              <Plus /> Otro pago
            </Button>
            <p className="text-sm font-semibold tabular">
              {faltaMixto > 0 ? `Falta ${soles(desdeCentimos(faltaMixto))}` : faltaMixto < 0 ? "Se pasa del total" : "Completo"}
              {vueltoMixto > 0 && ` · vuelto ${soles(desdeCentimos(vueltoMixto))}`}
            </p>
          </div>
        </div>
      )}

      {(error || problema) && (
        <p
          role="alert"
          className={cn(
            "mt-4 rounded-xl px-4 py-2.5 text-sm font-semibold",
            error ? "bg-pill-negative-bg text-pill-negative-ink" : "bg-muted text-muted-foreground",
          )}
        >
          {error ?? problema}
        </p>
      )}

      <Button type="submit" className="mt-4 h-14 w-full text-[16px] font-extrabold" disabled={!!problema || enviando}>
        {enviando ? <Loader2 className="animate-spin" /> : null}
        {enviando ? "Registrando…" : `Confirmar cobro · ${soles(desdeCentimos(cobrar))}`}
      </Button>
    </form>
  );
}
