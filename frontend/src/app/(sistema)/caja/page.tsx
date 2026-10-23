"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { ArrowDownLeft, ArrowUpRight, Loader2, Lock, ReceiptText, ShoppingCart } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { AbrirCaja } from "@/components/caja/AbrirCaja";
import { PildoraDiferencia } from "@/components/caja/PildoraDiferencia";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { Indicador } from "@/components/comunes/Indicador";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError, nuevaClave } from "@/lib/api";
import { cn, fechaYHora, recencia, soles } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";
import type { Sesion, SesionDetalle } from "@/types/ventas";

const TAMANIO = 15;
const TODOS = "todos";

export default function CajaPage() {
  return (
    <RequierePermiso permiso="caja.ver">
      <Caja />
    </RequierePermiso>
  );
}

function Caja() {
  const { tiene } = useAuth();
  const estado = useQuery({ queryKey: ["caja", "actual"], queryFn: cajaService.actual });
  const sesionId = estado.data?.sesion?.id;
  const detalle = useQuery({
    queryKey: ["caja", "sesion", sesionId],
    queryFn: () => cajaService.sesion(sesionId!),
    enabled: !!sesionId,
  });

  return (
    <>
      <PageHeader
        titulo="Caja"
        linea={
          estado.data?.sesion
            ? `${estado.data.sesion.caja} abierta desde ${fechaYHora(estado.data.sesion.fecha_apertura).hora} · ${estado.data.sesion.sucursal}`
            : "Abre tu turno con el sencillo inicial y ciérralo contando lo que hay"
        }
        acciones={
          <>
            {tiene("pos.vender") && (
              <Button variant="outline" asChild>
                <Link href="/ventas">
                  <ReceiptText /> Ventas
                </Link>
              </Button>
            )}
            {estado.data?.sesion && tiene("pos.vender") && (
              <Button asChild>
                <Link href="/pos">
                  <ShoppingCart strokeWidth={2.4} /> Ir a vender
                </Link>
              </Button>
            )}
          </>
        }
      />

      {estado.isLoading ? (
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      ) : estado.data?.sesion ? (
        <TurnoAbierto sesion={detalle.data ?? null} resumen={estado.data.sesion} />
      ) : (
        <AbrirCaja className="mb-6 max-w-xl" />
      )}

      <Historial />
    </>
  );
}

function TurnoAbierto({ sesion, resumen }: { sesion: SesionDetalle | null; resumen: Sesion }) {
  const { tiene } = useAuth();
  const s = sesion ?? resumen;
  return (
    <div className="mb-6 grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Indicador
            oscuro
            etiqueta="Efectivo en caja"
            valor={s.efectivo_esperado !== null ? soles(s.efectivo_esperado) : "Al cerrar"}
            detalle={s.efectivo_esperado !== null ? "esperado según el sistema" : "cierre ciego: cuentas sin verlo"}
          />
          <Indicador etiqueta="Ventas del turno" valor={s.ventas} detalle={s.anuladas ? `${s.anuladas} anulada(s)` : "sin anulaciones"} />
          <Indicador etiqueta="Sencillo inicial" valor={soles(s.monto_inicial)} detalle={recencia(s.fecha_apertura)} />
          <Indicador
            etiqueta="Ingresos − egresos"
            valor={soles(Number(s.ingresos) - Number(s.egresos))}
            detalle={`+${soles(s.ingresos)} / −${soles(s.egresos)}`}
          />
        </div>

        <section className="tarjeta overflow-hidden">
          <h2 className="px-5 pt-4 pb-2 font-extrabold">Movimientos de efectivo</h2>
          {!sesion ? (
            <Loader2 className="m-5 size-5 animate-spin text-muted-foreground" />
          ) : sesion.movimientos.length === 0 ? (
            <p className="px-5 pb-5 text-sm text-muted-foreground">Sin ingresos ni egresos en este turno.</p>
          ) : (
            <ul>
              {sesion.movimientos.map((m) => (
                <li key={m.id} className="flex items-center gap-3 border-t border-rule px-5 py-3">
                  <span
                    className={cn(
                      "grid size-8 place-items-center rounded-lg",
                      m.tipo === "INGRESO" ? "bg-pill-positive-bg text-pill-positive-ink" : "bg-pill-negative-bg text-pill-negative-ink",
                    )}
                  >
                    {m.tipo === "INGRESO" ? <ArrowDownLeft className="size-4" /> : <ArrowUpRight className="size-4" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold">{m.concepto}</p>
                    <p className="text-xs text-muted-foreground">
                      {m.usuario} · {fechaYHora(m.creado_en).hora}
                    </p>
                  </div>
                  <b className={cn("tabular", m.tipo === "EGRESO" && "text-destructive")}>
                    {m.tipo === "EGRESO" ? "−" : "+"}
                    {soles(m.monto)}
                  </b>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="flex flex-col gap-4">
        {tiene("caja.movimientos") && <NuevoMovimiento />}
        {tiene("caja.cerrar") && (
          <Button asChild className="h-14 bg-navy text-[15px] font-extrabold text-white hover:bg-navy/90 dark:bg-navy-2">
            <Link href={`/caja/${s.id}/cerrar`}>
              <Lock /> Cerrar caja y contar
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}

function NuevoMovimiento() {
  const queryClient = useQueryClient();
  const [clave, setClave] = useState(nuevaClave);
  const [tipo, setTipo] = useState<"INGRESO" | "EGRESO">("EGRESO");
  const [monto, setMonto] = useState("");
  const [concepto, setConcepto] = useState("");
  const [error, setError] = useState<string | null>(null);

  const guardar = useMutation({
    mutationFn: () => {
      if (!/^\d{1,6}([.,]\d{1,2})?$/.test(monto.trim()) || Number(monto.replace(",", ".")) <= 0) throw new Error("Escribe el monto");
      if (concepto.trim().length < 3) throw new Error("Escribe el motivo (ej. pago de hielo)");
      return cajaService.movimiento({ tipo, monto: monto.trim().replace(",", "."), concepto: concepto.trim() }, clave);
    },
    onSuccess: () => {
      toast.success(tipo === "INGRESO" ? "Ingreso registrado" : "Egreso registrado");
      setMonto("");
      setConcepto("");
      setClave(nuevaClave());
      void queryClient.invalidateQueries({ queryKey: ["caja"] });
    },
    onError: (e) => setError(mensajeError(e)),
  });

  return (
    <form
      className="tarjeta flex flex-col gap-3 p-5"
      onSubmit={(e) => {
        e.preventDefault();
        setError(null);
        guardar.mutate();
      }}
    >
      <h2 className="font-extrabold">Ingreso o egreso</h2>
      <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Tipo de movimiento">
        {(["EGRESO", "INGRESO"] as const).map((t) => (
          <button
            key={t}
            type="button"
            role="radio"
            aria-checked={tipo === t}
            onClick={() => setTipo(t)}
            className={cn(
              "h-10 rounded-xl border-2 text-sm font-bold",
              tipo === t ? "border-navy bg-navy text-amarillo dark:border-amarillo dark:bg-navy-2" : "border-border hover:bg-muted",
            )}
          >
            {t === "EGRESO" ? "Sale dinero" : "Entra dinero"}
          </button>
        ))}
      </div>
      <Input value={monto} onChange={(e) => setMonto(e.target.value)} inputMode="decimal" placeholder="Monto S/" className="h-11 tabular" aria-label="Monto" />
      <Input
        value={concepto}
        onChange={(e) => setConcepto(e.target.value)}
        maxLength={200}
        placeholder={tipo === "EGRESO" ? "Motivo, ej. pago al de los huevos" : "Motivo, ej. sencillo del banco"}
        aria-label="Motivo"
      />
      {error && <p className="rounded-xl bg-pill-negative-bg px-3 py-2 text-sm font-semibold text-pill-negative-ink">{error}</p>}
      <Button type="submit" variant="outline" disabled={guardar.isPending}>
        {guardar.isPending && <Loader2 className="animate-spin" />} Registrar
      </Button>
    </form>
  );
}

function Historial() {
  const { tiene } = useAuth();
  const todas = tiene("caja.ver_todas");
  const [pagina, setPagina] = useState(1);
  const [cajero, setCajero] = useState(TODOS);
  const cajeros = useQuery({ queryKey: ["caja", "cajeros"], queryFn: cajaService.cajeros, enabled: todas });
  const lista = useQuery({
    queryKey: ["caja", "sesiones", pagina, cajero],
    queryFn: () =>
      cajaService.sesiones({ pagina, tamanio: TAMANIO, usuario_id: cajero === TODOS ? undefined : Number(cajero) }),
    placeholderData: keepPreviousData,
  });

  const columnas = useMemo<ColumnDef<Sesion, unknown>[]>(
    () => [
      {
        id: "turno",
        header: "Turno",
        cell: ({ row: { original: s } }) => (
          <Link href={`/caja/${s.id}`} className="group block">
            <p className="font-bold group-hover:underline">
              {s.caja} · {fechaYHora(s.fecha_apertura).fecha}
            </p>
            <p className="text-xs text-muted-foreground tabular">
              {fechaYHora(s.fecha_apertura).hora} – {s.fecha_cierre ? fechaYHora(s.fecha_cierre).hora : "abierta"}
            </p>
          </Link>
        ),
      },
      { id: "cajero", header: "Cajero", cell: ({ row }) => row.original.usuario },
      {
        id: "ventas",
        header: "Ventas",
        meta: { numero: true, className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => row.original.ventas,
      },
      {
        id: "vendido",
        header: "Vendido",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) => (row.original.total_vendido !== null ? soles(row.original.total_vendido) : "—"),
      },
      {
        id: "arqueo",
        header: "Arqueo",
        cell: ({ row }) => <PildoraDiferencia diferencia={row.original.diferencia} />,
      },
    ],
    [],
  );

  return (
    <>
      <h2 className="mb-3 text-lg font-extrabold">{todas ? "Turnos de la sucursal" : "Mis turnos"}</h2>
      <DataTable
        columnas={columnas}
        datos={lista.data?.items}
        cargando={lista.isLoading}
        total={lista.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio="Todavía no hay turnos de caja."
        barra={
          todas && (
            <Select
              value={cajero}
              onValueChange={(v) => {
                setCajero(v);
                setPagina(1);
              }}
            >
              <SelectTrigger className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos los cajeros</SelectItem>
                {(cajeros.data ?? []).map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.nombre} ({c.turnos})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )
        }
      />
    </>
  );
}
