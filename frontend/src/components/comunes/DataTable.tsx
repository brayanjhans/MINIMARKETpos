"use client";

import { type ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface MetaColumna {
  /** Campo de orden en el backend; si falta, la columna no se ordena */
  orden?: string;
  /** Columna numérica: alineada a la derecha, cabecera incluida */
  numero?: boolean;
  className?: string;
}

interface Props<T> {
  columnas: ColumnDef<T, unknown>[];
  datos: T[] | undefined;
  cargando: boolean;
  total: number;
  pagina: number;
  tamanio: number;
  onPagina: (pagina: number) => void;
  /** Orden en formato del backend: "campo" o "-campo" */
  orden?: string;
  onOrden?: (orden: string | undefined) => void;
  /** Contenido cuando no hay filas: una frase que diga qué hacer */
  vacio: ReactNode;
  /** Buscador y filtros, dentro de la tarjeta sobre la tabla */
  barra?: ReactNode;
  /** Clases por fila (por ejemplo, resaltar un usuario bloqueado) */
  claseFila?: (fila: T) => string | undefined;
}

/** Tabla en tarjeta blanca con paginación y orden en el servidor (los listados nunca se cargan completos). */
export function DataTable<T>({
  columnas,
  datos,
  cargando,
  total,
  pagina,
  tamanio,
  onPagina,
  orden,
  onOrden,
  vacio,
  barra,
  claseFila,
}: Props<T>) {
  const tabla = useReactTable({
    data: datos ?? [],
    columns: columnas,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
  });

  const paginas = Math.max(1, Math.ceil(total / tamanio));
  const desde = total === 0 ? 0 : (pagina - 1) * tamanio + 1;
  const hasta = Math.min(pagina * tamanio, total);
  const filas = tabla.getRowModel().rows;

  const alternarOrden = (campo: string) => {
    if (!onOrden) return;
    if (orden === campo) onOrden(`-${campo}`);
    else if (orden === `-${campo}`) onOrden(undefined);
    else onOrden(campo);
  };

  return (
    <div className="tarjeta overflow-hidden">
      {barra && <div className="flex flex-col gap-2.5 p-4 sm:flex-row sm:flex-wrap sm:items-center">{barra}</div>}
      <div className="scrollbar-fino overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            {tabla.getHeaderGroups().map((grupo) => (
              <tr key={grupo.id}>
                {grupo.headers.map((header) => {
                  const meta = header.column.columnDef.meta as MetaColumna | undefined;
                  const campo = meta?.orden;
                  const activo = campo && (orden === campo || orden === `-${campo}`);
                  const contenido = flexRender(header.column.columnDef.header, header.getContext());
                  return (
                    <th
                      key={header.id}
                      scope="col"
                      aria-sort={activo ? (orden?.startsWith("-") ? "descending" : "ascending") : undefined}
                      className={cn(
                        "h-11 bg-cabecera-tabla px-4 text-left text-xs font-bold whitespace-nowrap text-muted-foreground",
                        meta?.numero && "text-right",
                        meta?.className,
                      )}
                    >
                      {campo && onOrden ? (
                        <button
                          type="button"
                          onClick={() => alternarOrden(campo)}
                          className={cn(
                            "-mx-1 inline-flex items-center gap-1 rounded px-1 transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                            activo && "text-foreground",
                          )}
                        >
                          {contenido}
                          {orden === campo && <ArrowUp className="size-3" />}
                          {orden === `-${campo}` && <ArrowDown className="size-3" />}
                        </button>
                      ) : (
                        contenido
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {cargando
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={`c-${i}`} className="border-t border-rule">
                    {columnas.map((_, j) => (
                      <td key={j} className="h-[62px] px-4">
                        <Skeleton className="h-4 w-full max-w-36 rounded-md" />
                      </td>
                    ))}
                  </tr>
                ))
              : filas.map((fila) => (
                  <tr key={fila.id} className={cn("border-t border-rule", claseFila?.(fila.original))}>
                    {fila.getVisibleCells().map((celda) => {
                      const meta = celda.column.columnDef.meta as MetaColumna | undefined;
                      return (
                        <td
                          key={celda.id}
                          className={cn(
                            "h-[62px] px-4 align-middle",
                            meta?.numero && "text-right tabular",
                            meta?.className,
                          )}
                        >
                          {flexRender(celda.column.columnDef.cell, celda.getContext())}
                        </td>
                      );
                    })}
                  </tr>
                ))}
          </tbody>
        </table>
        {!cargando && filas.length === 0 && (
          <div className="border-t border-rule px-5 py-12 text-center text-sm text-muted-foreground">{vacio}</div>
        )}
      </div>

      {total > tamanio && (
        <div className="flex items-center justify-between gap-3 border-t border-rule px-4 py-3 text-sm">
          <span className="font-medium text-muted-foreground tabular">
            {desde}–{hasta} de {total.toLocaleString("es-PE")}
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => onPagina(pagina - 1)}
              disabled={pagina <= 1 || cargando}
              aria-label="Página anterior"
            >
              <ChevronLeft />
            </Button>
            <span className="min-w-16 text-center font-semibold tabular">
              {pagina} de {paginas}
            </span>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => onPagina(pagina + 1)}
              disabled={pagina >= paginas || cargando}
              aria-label="Página siguiente"
            >
              <ChevronRight />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
