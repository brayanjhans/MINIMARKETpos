"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Search } from "lucide-react";
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
import { recencia, soles } from "@/lib/utils";
import { ventasService } from "@/services/ventas.service";
import type { EstadoVenta, VentaListado } from "@/types/ventas";

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
        titulo="Ventas"
        linea={tiene("caja.ver_todas") ? "Todas las ventas de la sucursal" : "Tus ventas"}
      />
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
