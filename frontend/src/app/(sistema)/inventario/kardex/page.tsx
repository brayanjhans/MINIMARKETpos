"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { PageHeader } from "@/components/comunes/PageHeader";
import { NavInventario } from "@/components/inventario/NavInventario";
import { SelectorAlmacen } from "@/components/inventario/SelectorAlmacen";
import { BuscadorProducto } from "@/components/productos/BuscadorProducto";
import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { cantidad, TIPOS_MOVIMIENTO, unidadCorta } from "@/lib/inventario";
import { cn, fechaYHora, soles } from "@/lib/utils";
import { type FiltrosKardex, inventarioService } from "@/services/inventario.service";
import { productosService } from "@/services/productos.service";
import type { Movimiento, TipoMovimiento } from "@/types/inventario";

const TAMANIO = 30;
const TODOS = "todos";
const entero = (v?: string) => (v && /^\d+$/.test(v) ? Number(v) : undefined);

export default function KardexPage({ searchParams }: { searchParams: Promise<{ producto?: string; almacen?: string }> }) {
  const { producto, almacen } = use(searchParams);
  return (
    <RequierePermiso permiso="inventario.kardex">
      <Kardex productoId={entero(producto)} almacenInicial={entero(almacen)} />
    </RequierePermiso>
  );
}

function Kardex({ productoId, almacenInicial }: { productoId?: number; almacenInicial?: number }) {
  const { tiene } = useAuth();
  const router = useRouter();
  const [almacen, setAlmacen] = useState<number | undefined>(almacenInicial);
  const [tipo, setTipo] = useState<string>(TODOS);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [pagina, setPagina] = useState(1);

  const producto = useQuery({
    queryKey: ["productos", "detalle", productoId],
    queryFn: () => productosService.obtener(productoId!),
    enabled: !!productoId,
  });
  const filtros: FiltrosKardex = {
    almacen_id: almacen,
    producto_id: productoId,
    tipo: tipo === TODOS ? undefined : (tipo as TipoMovimiento),
    desde: desde || undefined,
    hasta: hasta || undefined,
    pagina,
    tamanio: TAMANIO,
  };
  const movimientos = useQuery({
    queryKey: ["inventario", "kardex", filtros],
    queryFn: ({ signal }) => inventarioService.kardex(filtros, signal),
    placeholderData: keepPreviousData,
  });
  const p = producto.data;
  const stockAlmacen = p?.stock_por_almacen.find((s) => (almacen ? s.almacen_id === almacen : true));
  const unidad = p ? unidadCorta(p.unidad_medida) : "";

  const columnas = useMemo<ColumnDef<Movimiento, unknown>[]>(
    () => [
      {
        id: "fecha",
        header: "Fecha",
        cell: ({ row }) => {
          const { fecha, hora } = fechaYHora(row.original.creado_en);
          return (
            <span className="whitespace-nowrap tabular">
              {fecha.slice(8)}/{fecha.slice(5, 7)} <span className="text-muted-foreground">{hora}</span>
            </span>
          );
        },
      },
      {
        id: "tipo",
        header: "Movimiento",
        cell: ({ row: { original: m } }) => (
          <span className={cn("font-bold whitespace-nowrap", Number(m.cantidad) > 0 ? "text-positive" : "text-foreground")}>
            {TIPOS_MOVIMIENTO[m.tipo]}
          </span>
        ),
      },
      ...(!productoId
        ? ([
            {
              id: "producto",
              header: "Producto",
              cell: ({ row }) => (
                <Link href={`/inventario/kardex?producto=${row.original.producto_id}`} className="font-semibold hover:underline">
                  {row.original.producto}
                </Link>
              ),
            },
          ] satisfies ColumnDef<Movimiento, unknown>[])
        : []),
      {
        id: "documento",
        header: "Documento",
        cell: ({ row: { original: m } }) => {
          const enlace =
            m.referencia_tipo === "ajuste"
              ? `/inventario/ajustes/${m.referencia_id}`
              : m.referencia_tipo === "transferencia"
                ? `/inventario/transferencias/${m.referencia_id}`
                : m.referencia_tipo === "inventario_fisico"
                  ? `/inventario/fisicos/${m.referencia_id}`
                  : null;
          return m.documento && enlace ? (
            <Link href={enlace} className="font-semibold tabular hover:underline">
              {m.documento}
            </Link>
          ) : (
            <span className="text-muted-foreground">—</span>
          );
        },
      },
      {
        id: "detalle",
        header: "Detalle",
        meta: { className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: m } }) => (
          <span className="text-[13px] text-muted-foreground">
            {[m.motivo, m.lote && `lote ${m.lote}`, m.costo_unitario && Number(m.costo_unitario) > 0 && `${soles(m.costo_unitario)} c/u`]
              .filter(Boolean)
              .join(" · ") || "—"}
          </span>
        ),
      },
      {
        id: "entrada",
        header: "Entrada",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) =>
          Number(row.original.cantidad) > 0 ? <b className="text-positive">+{cantidad(row.original.cantidad)}</b> : <span className="text-muted-foreground">—</span>,
      },
      {
        id: "salida",
        header: "Salida",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) =>
          Number(row.original.cantidad) < 0 ? <b>−{cantidad(-Number(row.original.cantidad))}</b> : <span className="text-muted-foreground">—</span>,
      },
      {
        id: "saldo",
        header: "Saldo",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row }) => (
          <b className={cn(Number(row.original.stock_nuevo) < 0 && "text-destructive")}>{cantidad(row.original.stock_nuevo)}</b>
        ),
      },
      {
        id: "usuario",
        header: "Quién",
        meta: { className: "hidden md:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => <span className="whitespace-nowrap text-[13px]">{row.original.usuario ?? "—"}</span>,
      },
    ],
    [productoId],
  );

  const cambiar = (fn: () => void) => {
    fn();
    setPagina(1);
  };

  return (
    <>
      <PageHeader titulo={p ? `Kardex · ${p.nombre}` : "Kardex"} linea="Cada entrada y salida de stock, con el saldo después de cada una. No se puede modificar." />
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-start sm:justify-between">
        <NavInventario />
        <SelectorAlmacen valor={almacen} onCambiar={(id) => cambiar(() => setAlmacen(id))} />
      </div>

      <section className="tarjeta mb-4 flex flex-col gap-4 p-4 lg:flex-row lg:items-center">
        {p ? (
          <>
            <div className="flex min-w-0 items-center gap-3 lg:w-80">
              <ImagenProducto id={p.id} nombre={p.nombre} url={p.miniatura_url} className="size-12" />
              <div className="min-w-0">
                <p className="truncate font-extrabold">{p.nombre}</p>
                <p className="text-xs text-muted-foreground tabular">{p.codigo_barras ?? "Sin código"}</p>
              </div>
              <Button variant="ghost" size="icon-sm" aria-label="Ver otro producto" onClick={() => router.push("/inventario/kardex")}>
                <X />
              </Button>
            </div>
            <dl className="grid flex-1 grid-cols-2 gap-3 sm:grid-cols-3">
              <Dato titulo={`Stock actual${stockAlmacen ? ` · ${stockAlmacen.almacen}` : ""}`} valor={`${cantidad(stockAlmacen?.cantidad ?? 0)} ${unidad}`} />
              {p.precio_costo !== null && <Dato titulo="Costo promedio" valor={soles(p.precio_costo)} />}
              {p.precio_costo !== null && (
                <Dato titulo="Valor del stock" valor={soles(Math.max(Number(stockAlmacen?.cantidad ?? 0), 0) * Number(p.precio_costo))} />
              )}
            </dl>
          </>
        ) : (
          <div className="w-full">
            <p className="mb-2 text-sm text-muted-foreground">Elige un producto para ver su kardex, o revisa abajo todos los movimientos del almacén.</p>
            <BuscadorProducto onSeleccionar={(x) => router.push(`/inventario/kardex?producto=${x.id}${almacen ? `&almacen=${almacen}` : ""}`)} />
          </div>
        )}
      </section>

      <DataTable
        barra={
          <>
            <Select value={tipo} onValueChange={(v) => cambiar(() => setTipo(v))}>
              <SelectTrigger className="h-[34px] w-full rounded-[10px] border-0 bg-muted font-semibold sm:w-52" aria-label="Tipo de movimiento">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos los movimientos</SelectItem>
                {Object.entries(TIPOS_MOVIMIENTO).map(([valor, texto]) => (
                  <SelectItem key={valor} value={valor}>
                    {texto}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <label className="flex items-center gap-2 text-[13px] font-semibold sm:ml-auto">
              Desde
              <Input type="date" value={desde} max={hasta || undefined} onChange={(e) => cambiar(() => setDesde(e.target.value))} className="h-[34px] w-40" />
            </label>
            <label className="flex items-center gap-2 text-[13px] font-semibold">
              Hasta
              <Input type="date" value={hasta} min={desde || undefined} onChange={(e) => cambiar(() => setHasta(e.target.value))} className="h-[34px] w-40" />
            </label>
          </>
        }
        columnas={columnas}
        datos={movimientos.data?.items}
        cargando={movimientos.isLoading}
        total={movimientos.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio={
          p ? (
            <>
              {p.nombre} aún no tiene movimientos en este almacén.
              {tiene("inventario.stock_inicial") && (
                <>
                  {" "}
                  <Link href="/inventario/stock-inicial" className="font-bold text-foreground underline">
                    Cargar su stock inicial
                  </Link>
                </>
              )}
            </>
          ) : (
            "No hay movimientos con estos filtros."
          )
        }
      />
    </>
  );
}

function Dato({ titulo, valor }: { titulo: string; valor: string }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{titulo}</dt>
      <dd className="text-lg font-extrabold tabular">{valor}</dd>
    </div>
  );
}
