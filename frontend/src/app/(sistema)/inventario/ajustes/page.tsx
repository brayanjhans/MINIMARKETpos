"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Plus } from "lucide-react";
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
import { cantidad, ESTADOS_AJUSTE } from "@/lib/inventario";
import { cn, recencia, soles } from "@/lib/utils";
import { inventarioService } from "@/services/inventario.service";
import type { AjusteListado, EstadoDocumento } from "@/types/inventario";

const TAMANIO = 20;

export default function AjustesPage() {
  return (
    <RequierePermiso permiso="inventario.ver">
      <Ajustes />
    </RequierePermiso>
  );
}

function Ajustes() {
  const { tiene } = useAuth();
  const [estado, setEstado] = useState<EstadoDocumento | "todos">(tiene("inventario.aprobar_ajustes") ? "PENDIENTE_APROBACION" : "todos");
  const [pagina, setPagina] = useState(1);
  const params = { estado: estado === "todos" ? undefined : estado, pagina, tamanio: TAMANIO };
  const ajustes = useQuery({
    queryKey: ["inventario", "ajustes", params],
    queryFn: () => inventarioService.ajustes(params),
    placeholderData: keepPreviousData,
  });
  const pendientes = useQuery({
    queryKey: ["inventario", "ajustes", "pendientes"],
    queryFn: () => inventarioService.ajustes({ estado: "PENDIENTE_APROBACION", tamanio: 1 }),
  });

  const columnas = useMemo<ColumnDef<AjusteListado, unknown>[]>(
    () => [
      {
        id: "numero",
        header: "Ajuste",
        cell: ({ row: { original: a } }) => (
          <Link href={`/inventario/ajustes/${a.id}`} className="group block">
            <p className="font-bold tabular group-hover:underline">{a.numero}</p>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span aria-hidden className={cn("size-2 rounded-full", a.es_merma ? "bg-destructive" : "bg-muted-foreground/50")} />
              {a.motivo}
            </p>
          </Link>
        ),
      },
      {
        id: "estado",
        header: "Estado",
        cell: ({ row }) => <Pildora tono={ESTADOS_AJUSTE[row.original.estado].tono}>{ESTADOS_AJUSTE[row.original.estado].texto}</Pildora>,
      },
      {
        id: "usuario",
        header: "Registró",
        meta: { className: "hidden md:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: a } }) => (
          <div className="text-[13px]">
            <p className="font-semibold">{a.usuario}</p>
            <p className="text-xs text-muted-foreground">{recencia(a.creado_en)}</p>
          </div>
        ),
      },
      {
        id: "aprobo",
        header: "Aprobó",
        meta: { className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => <span className="text-[13px]">{row.original.aprobado_por ?? "—"}</span>,
      },
      {
        id: "unidades",
        header: "Unidades",
        meta: { numero: true, className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => cantidad(row.original.total_unidades),
      },
      {
        id: "valor",
        header: "Valor",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) =>
          row.original.valor === null ? "—" : (
            <b className={cn(Number(row.original.valor) < 0 && "text-destructive")}>{soles(row.original.valor)}</b>
          ),
      },
    ],
    [],
  );

  return (
    <>
      <PageHeader
        titulo="Ajustes y mermas"
        linea="Todo cambio manual de stock queda aquí y espera la aprobación de otra persona"
        acciones={
          tiene("inventario.ajustar") && (
            <Button asChild>
              <Link href="/inventario/ajustes/nuevo">
                <Plus strokeWidth={2.6} /> Ajuste o merma
              </Link>
            </Button>
          )
        }
      />
      <NavInventario pendientes={pendientes.data?.total} />
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
              { valor: "PENDIENTE_APROBACION", etiqueta: "Por aprobar", cantidad: pendientes.data?.total },
              { valor: "BORRADOR", etiqueta: "Borradores" },
              { valor: "APLICADO", etiqueta: "Aplicados" },
              { valor: "RECHAZADO", etiqueta: "Rechazados" },
              { valor: "todos", etiqueta: "Todos" },
            ]}
          />
        }
        columnas={columnas}
        datos={ajustes.data?.items}
        cargando={ajustes.isLoading}
        total={ajustes.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio={estado === "PENDIENTE_APROBACION" ? "No hay ajustes esperando aprobación." : "No hay ajustes en esta vista."}
      />
    </>
  );
}
