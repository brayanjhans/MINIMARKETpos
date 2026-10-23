"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { ArrowLeftRight, ClipboardList, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { Indicador } from "@/components/comunes/Indicador";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pestanas } from "@/components/comunes/Pestanas";
import { NavInventario } from "@/components/inventario/NavInventario";
import { SelectorAlmacen } from "@/components/inventario/SelectorAlmacen";
import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { cantidad, unidadCorta, vence } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { type FiltrosStock, inventarioService } from "@/services/inventario.service";
import type { StockFila } from "@/types/inventario";

const TAMANIO = 20;
type Vista = "todos" | NonNullable<FiltrosStock["estado"]>;

export default function InventarioPage() {
  return (
    <RequierePermiso permiso="inventario.ver">
      <Inventario />
    </RequierePermiso>
  );
}

function Inventario() {
  const { tiene } = useAuth();
  const [almacen, setAlmacen] = useState<number | undefined>();
  const [vista, setVista] = useState<Vista>("todos");
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(1);
  const [orden, setOrden] = useState<string | undefined>("nombre");
  const busquedaDebounced = useDebounce(busqueda);

  const filtros: FiltrosStock = {
    almacen_id: almacen,
    pagina,
    tamanio: TAMANIO,
    orden,
    busqueda: busquedaDebounced || undefined,
    estado: vista === "todos" ? undefined : vista,
  };
  const stock = useQuery({
    queryKey: ["inventario", "stock", filtros],
    queryFn: ({ signal }) => inventarioService.stock(filtros, signal),
    placeholderData: keepPreviousData,
  });
  const resumen = useQuery({ queryKey: ["inventario", "resumen", almacen], queryFn: () => inventarioService.resumen(almacen) });
  const r = resumen.data;
  const porVencer = useQuery({
    queryKey: ["inventario", "lotes", almacen, r?.dias_alerta],
    queryFn: () => inventarioService.lotes({ almacen_id: almacen, por_vencer_dias: r!.dias_alerta }),
    enabled: !!r,
  });

  const cambiarFiltro = (fn: () => void) => {
    fn();
    setPagina(1);
  };

  const columnas = useMemo<ColumnDef<StockFila, unknown>[]>(
    () => [
      {
        id: "nombre",
        header: "Producto",
        meta: { orden: "nombre", className: "sm:min-w-64" } satisfies MetaColumna,
        cell: ({ row: { original: f } }) => (
          <Link href={`/productos/${f.producto_id}`} className="group flex items-center gap-3">
            <ImagenProducto id={f.producto_id} nombre={f.nombre} url={f.miniatura_url} className="size-9" />
            <div className="min-w-0">
              <p className="truncate font-bold group-hover:underline">{f.nombre}</p>
              <p className="truncate text-xs text-muted-foreground">
                {f.categoria ?? "Sin categoría"}
                {Number(f.pendiente_lote) > 0 && (
                  <span className="font-semibold text-amarillo-tinta"> · {cantidad(f.pendiente_lote)} vendidas sin lote</span>
                )}
              </p>
            </div>
          </Link>
        ),
      },
      {
        id: "stock",
        header: "Stock",
        meta: { orden: "stock", numero: true } satisfies MetaColumna,
        cell: ({ row: { original: f } }) => (
          <span className={cn("font-extrabold whitespace-nowrap", (f.estado === "bajo" || Number(f.cantidad) <= 0) && "text-destructive")}>
            {cantidad(f.cantidad)} <span className="font-medium text-muted-foreground">{unidadCorta(f.unidad_medida)}</span>
          </span>
        ),
      },
      {
        id: "nivel",
        header: "Nivel",
        meta: { className: "hidden md:table-cell w-32" } satisfies MetaColumna,
        cell: ({ row: { original: f } }) => <Nivel fila={f} />,
      },
      {
        id: "minimo",
        header: "Mínimo",
        meta: { numero: true, className: "hidden md:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => <span className="text-muted-foreground">{cantidad(row.original.stock_minimo)}</span>,
      },
      {
        id: "valor",
        header: "Valor",
        meta: { orden: "valor", numero: true, className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => (row.original.valor === null ? "—" : soles(row.original.valor)),
      },
      {
        id: "kardex",
        header: () => <span className="sr-only">Kardex</span>,
        meta: { className: "w-px text-right" } satisfies MetaColumna,
        cell: ({ row }) =>
          tiene("inventario.kardex") && (
            <Link
              href={`/inventario/kardex?producto=${row.original.producto_id}${almacen ? `&almacen=${almacen}` : ""}`}
              className="text-[13px] font-bold hover:underline"
            >
              Kardex
            </Link>
          ),
      },
    ],
    [tiene, almacen],
  );

  return (
    <>
      <PageHeader
        titulo="Inventario"
        linea="Lo que hay en el almacén, lo que falta y lo que está por vencer"
        acciones={
          <>
            {tiene("inventario.inventario_fisico") && (
              <Button variant="outline" asChild>
                <Link href="/inventario/fisicos">
                  <ClipboardList /> Inventario físico
                </Link>
              </Button>
            )}
            {tiene("inventario.transferir") && (
              <Button variant="outline" asChild>
                <Link href="/inventario/transferencias/nueva">
                  <ArrowLeftRight /> Transferir
                </Link>
              </Button>
            )}
            {tiene("inventario.ajustar") && (
              <Button asChild>
                <Link href="/inventario/ajustes/nuevo">
                  <Plus strokeWidth={2.6} /> Ajuste o merma
                </Link>
              </Button>
            )}
          </>
        }
      />
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-start sm:justify-between">
        <NavInventario pendientes={r?.por_aprobar} />
        <SelectorAlmacen valor={almacen} onCambiar={(id) => cambiarFiltro(() => setAlmacen(id))} />
      </div>

      <section className="mb-4 grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-3 2xl:grid-cols-5">
        <Indicador
          oscuro
          className="col-span-2 lg:col-span-1"
          etiqueta={r?.valor_total === null ? "Productos con stock" : "Valor del inventario (al costo)"}
          valor={r ? (r.valor_total === null ? r.productos : soles(r.valor_total)) : undefined}
          detalle={r && `${r.productos} productos · ${cantidad(r.unidades)} unidades`}
        />
        <Indicador
          etiqueta="Stock bajo"
          valor={r?.stock_bajo}
          alerta={!!r?.stock_bajo}
          detalle={r?.sin_stock ? `y ${r.sin_stock} sin stock` : "por debajo del mínimo"}
          onClick={() => cambiarFiltro(() => setVista("bajo"))}
        />
        <Indicador
          aviso
          etiqueta={`Por vencer en ${r?.dias_alerta ?? 30} días`}
          valor={r ? `${r.lotes_por_vencer} lote${r.lotes_por_vencer === 1 ? "" : "s"}` : undefined}
          detalle={
            r && (r.lotes_vencidos ? `${r.lotes_vencidos} ya vencido(s)` : r.valor_por_vencer !== null ? `${soles(r.valor_por_vencer)} en riesgo` : undefined)
          }
        />
        <Indicador
          etiqueta="Mermas del mes"
          valor={r ? (r.mermas_mes === null ? r.ajustes_mes : soles(r.mermas_mes)) : undefined}
          detalle={
            r && (
              <>
                {r.ajustes_mes} ajuste{r.ajustes_mes === 1 ? "" : "s"}
                {r.por_aprobar > 0 && <b className="text-amarillo-tinta"> · {r.por_aprobar} por aprobar</b>}
              </>
            )
          }
        />
        <Indicador
          etiqueta="En tránsito"
          valor={r ? (r.transito_valor === null ? r.transito_documentos : soles(r.transito_valor)) : undefined}
          detalle={r && `${r.transito_documentos} transferencia${r.transito_documentos === 1 ? "" : "s"}`}
        />
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <DataTable
          barra={
            <>
              <Pestanas
                etiqueta="Filtrar stock"
                valor={vista}
                onCambiar={(v) => cambiarFiltro(() => setVista(v))}
                opciones={[
                  { valor: "todos", etiqueta: "Todo el stock" },
                  { valor: "bajo", etiqueta: "Stock bajo", cantidad: r?.stock_bajo },
                  { valor: "sin_stock", etiqueta: "Sin stock", cantidad: r?.sin_stock },
                  ...(r?.por_regularizar ? [{ valor: "por_regularizar" as const, etiqueta: "Por regularizar", cantidad: r.por_regularizar }] : []),
                ]}
              />
              <label className="flex h-[34px] items-center gap-2 rounded-[10px] bg-muted px-3 text-muted-foreground sm:ml-auto sm:w-56">
                <Search className="size-4 flex-none" />
                <Input
                  value={busqueda}
                  onChange={(e) => cambiarFiltro(() => setBusqueda(e.target.value))}
                  placeholder="Buscar producto"
                  className="h-auto border-0 bg-transparent p-0 text-foreground focus-visible:ring-0 dark:bg-transparent"
                  aria-label="Buscar producto"
                />
              </label>
            </>
          }
          columnas={columnas}
          datos={stock.data?.items}
          cargando={stock.isLoading}
          total={stock.data?.total ?? 0}
          pagina={pagina}
          tamanio={TAMANIO}
          onPagina={setPagina}
          orden={orden}
          onOrden={setOrden}
          claseFila={(f) =>
            f.estado === "por_regularizar" || f.estado === "negativo"
              ? "bg-aviso-fondo"
              : f.estado === "bajo"
                ? "bg-pill-negative-bg/40"
                : undefined
          }
          vacio={
            vista === "por_regularizar"
              ? "Nada por regularizar: no hay ventas sin stock pendientes."
              : vista === "bajo"
                ? "Ningún producto está por debajo de su mínimo."
                : busquedaDebounced
                  ? `Ningún producto coincide con «${busquedaDebounced}».`
                  : "No hay productos en esta vista."
          }
        />

        <section className="tarjeta flex flex-col p-5">
          <div className="flex items-baseline justify-between gap-2">
            <h2 className="text-base font-extrabold">Por vencer</h2>
            <span className="text-xs text-muted-foreground">lo que vence primero, sale primero</span>
          </div>
          <ul className="mt-2 flex flex-col">
            {porVencer.data?.length === 0 && (
              <li className="py-6 text-center text-sm text-muted-foreground">Nada vence en los próximos {r?.dias_alerta} días.</li>
            )}
            {porVencer.data?.slice(0, 8).map((l) => {
              const urgente = (l.dias_para_vencer ?? 99) <= 7;
              return (
                <li key={l.id} className="flex items-center gap-3 border-b border-rule py-2.5 last:border-0">
                  <div
                    className={cn(
                      "grid size-12 flex-none place-items-center content-center rounded-xl leading-none",
                      urgente ? "bg-pill-negative-bg text-pill-negative-ink" : "bg-pill-warning-bg text-pill-warning-ink",
                    )}
                    title={vence(l.dias_para_vencer)}
                  >
                    <b className="text-[17px] tabular">{Math.max(l.dias_para_vencer ?? 0, 0)}</b>
                    <span className="text-[10px] font-bold">{(l.dias_para_vencer ?? 0) < 0 ? "vencido" : "días"}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold">{l.producto}</p>
                    <p className="text-xs text-muted-foreground tabular">
                      Lote {l.numero_lote} · {cantidad(l.cantidad_actual)} und{l.valor !== null && ` · ${soles(l.valor)}`}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
          {tiene("inventario.ajustar") && !!porVencer.data?.length && (
            <Link
              href="/inventario/ajustes/nuevo?motivo=vencido"
              className="mt-auto inline-flex h-[38px] items-center justify-center rounded-[10px] bg-aviso-fondo text-[13px] font-bold text-amarillo-tinta"
            >
              Registrar como merma lo vencido
            </Link>
          )}
        </section>
      </div>
    </>
  );
}

function Nivel({ fila }: { fila: StockFila }) {
  const actual = Number(fila.cantidad);
  const minimo = Number(fila.stock_minimo);
  if (minimo <= 0) return <span className="text-xs text-muted-foreground">Sin mínimo</span>;
  const porcentaje = Math.max(0, Math.min(100, (actual / (minimo * 2)) * 100));
  const color = actual <= minimo ? "bg-destructive" : actual <= minimo * 1.5 ? "bg-warning" : "bg-positive";
  return (
    <div className="h-1.5 w-24 rounded-full bg-muted" role="img" aria-label={`${cantidad(actual)} de un mínimo de ${cantidad(minimo)}`}>
      <div className={cn("h-1.5 rounded-full", color)} style={{ width: `${porcentaje}%` }} />
    </div>
  );
}
