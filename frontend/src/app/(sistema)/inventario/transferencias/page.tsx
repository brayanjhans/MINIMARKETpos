"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { ArrowRight, Plus } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pestanas } from "@/components/comunes/Pestanas";
import { Pildora } from "@/components/comunes/Pildora";
import { NavInventario } from "@/components/inventario/NavInventario";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { ESTADOS_TRANSFERENCIA } from "@/lib/inventario";
import { recencia, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { EstadoTransferencia, TransferenciaListado } from "@/types/inventario";

const TAMANIO = 20;

export default function TransferenciasPage() {
  return (
    <RequierePermiso permiso="inventario.ver">
      <Transferencias />
    </RequierePermiso>
  );
}

function Transferencias() {
  const { tiene } = useAuth();
  const [estado, setEstado] = useState<EstadoTransferencia | "todos">("EN_TRANSITO");
  const [pagina, setPagina] = useState(1);
  const params = { estado: estado === "todos" ? undefined : estado, pagina, tamanio: TAMANIO };
  const lista = useQuery({
    queryKey: ["inventario", "transferencias", params],
    queryFn: () => inventarioService.transferencias(params),
    placeholderData: keepPreviousData,
  });
  const enCamino = useQuery({
    queryKey: ["inventario", "transferencias", "en-camino"],
    queryFn: () => inventarioService.transferencias({ estado: "EN_TRANSITO", tamanio: 1 }),
  });

  const columnas = useMemo<ColumnDef<TransferenciaListado, unknown>[]>(
    () => [
      {
        id: "numero",
        header: "Transferencia",
        cell: ({ row: { original: t } }) => (
          <Link href={`/inventario/transferencias/${t.id}`} className="group block">
            <p className="font-bold tabular group-hover:underline">{t.numero}</p>
            <p className="text-xs text-muted-foreground">
              {t.productos} producto{t.productos === 1 ? "" : "s"} · {recencia(t.fecha_envio ?? t.creado_en)}
            </p>
          </Link>
        ),
      },
      {
        id: "ruta",
        header: "Ruta",
        cell: ({ row: { original: t } }) => (
          <span className="inline-flex flex-wrap items-center gap-1.5 text-[13px] font-semibold">
            {t.almacen_origen} <span className="font-normal text-muted-foreground">({t.sucursal_origen})</span>
            <ArrowRight className="size-3.5 text-muted-foreground" />
            {t.almacen_destino} <span className="font-normal text-muted-foreground">({t.sucursal_destino})</span>
          </span>
        ),
      },
      {
        id: "estado",
        header: "Estado",
        cell: ({ row }) => (
          <Pildora tono={ESTADOS_TRANSFERENCIA[row.original.estado].tono}>{ESTADOS_TRANSFERENCIA[row.original.estado].texto}</Pildora>
        ),
      },
      {
        id: "personas",
        header: "Envió / recibió",
        meta: { className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: t } }) => (
          <span className="text-[13px]">
            {t.usuario}
            {t.usuario_recibe && <span className="text-muted-foreground"> → {t.usuario_recibe}</span>}
          </span>
        ),
      },
      {
        id: "valor",
        header: "Valor",
        meta: { numero: true, className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => (row.original.valor === null ? "—" : soles(row.original.valor)),
      },
    ],
    [],
  );

  return (
    <>
      <PageHeader
        titulo="Transferencias"
        linea="Mercadería que se mueve entre almacenes: sale del origen, viaja y se confirma al recibirla"
        acciones={
          tiene("inventario.transferir") && (
            <Button asChild>
              <Link href="/inventario/transferencias/nueva">
                <Plus strokeWidth={2.6} /> Nueva transferencia
              </Link>
            </Button>
          )
        }
      />
      <NavInventario />
      <DataTable
        barra={
          <Pestanas
            etiqueta="Estado"
            valor={estado}
            onCambiar={(v) => {
              setEstado(v);
              setPagina(1);
            }}
            opciones={[
              { valor: "EN_TRANSITO", etiqueta: "En camino", cantidad: enCamino.data?.total },
              { valor: "RECIBIDA", etiqueta: "Recibidas" },
              { valor: "PENDIENTE", etiqueta: "Preparadas" },
              { valor: "ANULADA", etiqueta: "Anuladas" },
              { valor: "todos", etiqueta: "Todas" },
            ]}
          />
        }
        columnas={columnas}
        datos={lista.data?.items}
        cargando={lista.isLoading}
        total={lista.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio={estado === "EN_TRANSITO" ? "No hay mercadería en camino." : "No hay transferencias en esta vista."}
      />
    </>
  );
}
