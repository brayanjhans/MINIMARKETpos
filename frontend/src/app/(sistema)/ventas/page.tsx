"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Loader2, QrCode, Search, ShieldAlert, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pildora } from "@/components/comunes/Pildora";
import { Pestanas } from "@/components/comunes/Pestanas";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { METODOS } from "@/lib/ventas";
import { mensajeError } from "@/lib/api";
import { cn, fechaHora, recencia, soles } from "@/lib/utils";
import { ventasService } from "@/services/ventas.service";
import type { EstadoVenta, VentaListado, VerificacionTicket } from "@/types/ventas";

const TAMANIO = 20;
type Filtro = "todas" | "COMPLETADA" | "ANULADA";

export default function VentasPage() {
  return (
    <RequierePermiso permiso="pos.vender">
      <Ventas />
    </RequierePermiso>
  );
}

function Ventas() {
  const { tiene } = useAuth();
  const [pagina, setPagina] = useState(1);
  const [filtro, setFiltro] = useState<Filtro>("todas");
  const [texto, setTexto] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const busqueda = useDebounce(texto.trim(), 250);
  const lista = useQuery({
    queryKey: ["ventas", "lista", pagina, filtro, busqueda, desde, hasta],
    queryFn: ({ signal }) =>
      ventasService.listar(
        {
          pagina,
          tamanio: TAMANIO,
          estado: filtro === "todas" ? undefined : (filtro as EstadoVenta),
          busqueda: busqueda || undefined,
          desde: desde || undefined,
          hasta: hasta || undefined,
        },
        signal,
      ),
    placeholderData: keepPreviousData,
  });

  const columnas = useMemo<ColumnDef<VentaListado, unknown>[]>(
    () => [
      {
        id: "comprobante",
        header: "Ticket",
        cell: ({ row: { original: v } }) => (
          <Link href={`/ventas/${v.id}`} className="group block">
            <p className="font-bold tabular group-hover:underline">{v.comprobante}</p>
            <p className="text-xs text-muted-foreground">
              {recencia(v.fecha)} · {v.caja}
            </p>
          </Link>
        ),
      },
      {
        id: "cliente",
        header: "Cliente",
        meta: { className: "hidden md:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => row.original.cliente ?? <span className="text-muted-foreground">Varios</span>,
      },
      {
        id: "cajero",
        header: "Cajero",
        meta: { className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => row.original.usuario,
      },
      {
        id: "pago",
        header: "Pago",
        meta: { className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => (
          <span className="text-[13px] font-semibold">
            {row.original.metodos.map((m) => (
              <span key={m} className={`${METODOS[m].color} mr-2`}>
                {METODOS[m].corto}
              </span>
            ))}
          </span>
        ),
      },
      {
        id: "estado",
        header: "Estado",
        cell: ({ row }) =>
          row.original.estado === "ANULADA" ? <Pildora tono="negativo">Anulada</Pildora> : <Pildora tono="positivo">Pagada</Pildora>,
      },
      {
        id: "total",
        header: "Total",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) => (
          <b className={row.original.estado === "ANULADA" ? "text-muted-foreground line-through" : ""}>{soles(row.original.a_cobrar)}</b>
        ),
      },
    ],
    [],
  );

  const reiniciar = <T,>(f: (v: T) => void) => (v: T) => {
    f(v);
    setPagina(1);
  };

  return (
    <>
      <PageHeader
        titulo="Historial de tickets"
        linea={tiene("caja.ver_todas") ? "Todos los tickets de la sucursal, también los anulados" : "Tus tickets, también los anulados"}
      />
      <VerificarTicket />
      <DataTable
        columnas={columnas}
        datos={lista.data?.items}
        cargando={lista.isLoading}
        total={lista.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio="No hay ventas con estos filtros."
        barra={
          <div className="flex flex-wrap items-center gap-2">
            <Pestanas
              etiqueta="Estado"
              valor={filtro}
              onCambiar={reiniciar(setFiltro)}
              opciones={[
                { valor: "todas", etiqueta: "Todas" },
                { valor: "COMPLETADA", etiqueta: "Pagadas" },
                { valor: "ANULADA", etiqueta: "Anuladas" },
              ]}
            />
            <div className="relative ml-auto">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={texto}
                onChange={(e) => reiniciar(setTexto)(e.target.value)}
                placeholder="N.° de ticket o cliente"
                className="h-9 w-56 pl-9"
                aria-label="Buscar venta"
              />
            </div>
            <Input type="date" value={desde} onChange={(e) => reiniciar(setDesde)(e.target.value)} className="h-9 w-40" aria-label="Desde" />
            <Input type="date" value={hasta} onChange={(e) => reiniciar(setHasta)(e.target.value)} className="h-9 w-40" aria-label="Hasta" />
          </div>
        }
      />
    </>
  );
}

/** Escanea el QR de un ticket impreso (lector 2D o cámara) o escribe su número: dice si es auténtico. */
function VerificarTicket() {
  const [texto, setTexto] = useState("");
  const [resultado, setResultado] = useState<VerificacionTicket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [buscando, setBuscando] = useState(false);

  const verificar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (texto.trim().length < 3) return;
    setBuscando(true);
    setError(null);
    try {
      setResultado(await ventasService.verificar(texto.trim()));
      setTexto("");
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setBuscando(false);
    }
  };

  const ok = resultado?.valido && resultado.estado !== "ANULADA";
  return (
    <section className="tarjeta mb-4 flex flex-col gap-3 p-4 md:flex-row md:items-center">
      <form onSubmit={verificar} className="flex flex-1 items-center gap-2">
        <QrCode className="size-5 flex-none text-muted-foreground" />
        <Input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Verificar ticket: escanea su QR o escribe el número (T001-00000004)"
          className="h-10"
          aria-label="Verificar ticket"
          autoComplete="off"
        />
        <button type="submit" className="h-10 flex-none rounded-md bg-navy px-4 text-sm font-bold text-white dark:bg-navy-2" disabled={buscando}>
          {buscando ? <Loader2 className="size-4 animate-spin" /> : "Verificar"}
        </button>
      </form>
      {error && <p className="text-sm font-semibold text-destructive">{error}</p>}
      {resultado && (
        <div
          role="status"
          className={cn(
            "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm md:max-w-md",
            ok ? "bg-pill-positive-bg text-pill-positive-ink" : resultado.valido ? "bg-aviso-fondo text-amarillo-tinta" : "bg-pill-negative-bg text-pill-negative-ink",
          )}
        >
          {ok ? <ShieldCheck className="size-5 flex-none" /> : <ShieldAlert className="size-5 flex-none" />}
          <div className="min-w-0">
            <p className="font-bold">
              {resultado.motivo}
              {resultado.comprobante && ` · ${resultado.comprobante}`}
            </p>
            {resultado.fecha && (
              <p className="text-xs tabular">
                {fechaHora(resultado.fecha)} · {soles(resultado.total ?? 0)}
              </p>
            )}
          </div>
          {resultado.venta_id && (
            <Link href={`/ventas/${resultado.venta_id}`} className="ml-auto flex-none font-bold underline">
              Ver ticket
            </Link>
          )}
        </div>
      )}
    </section>
  );
}
