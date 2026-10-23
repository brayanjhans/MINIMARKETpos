"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Download, Ellipsis, FileSpreadsheet, History, Pencil, Plus, Power, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { Indicador } from "@/components/comunes/Indicador";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pestanas } from "@/components/comunes/Pestanas";
import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { mensajeError } from "@/lib/api";
import { cantidad, unidadCorta } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { categoriasService } from "@/services/categorias.service";
import { type FiltrosProductos, productosService } from "@/services/productos.service";
import type { ProductoListado } from "@/types/productos";

const TAMANIO = 20;
const TODAS = "todas";
type Estado = NonNullable<FiltrosProductos["estado"]> | "todos" | "inactivos";

export default function ProductosPage() {
  return (
    <RequierePermiso permiso="productos.ver">
      <Productos />
    </RequierePermiso>
  );
}

function Productos() {
  const { tiene } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [busqueda, setBusqueda] = useState("");
  const [categoria, setCategoria] = useState(TODAS);
  const [estado, setEstado] = useState<Estado>("todos");
  const [pagina, setPagina] = useState(1);
  const [orden, setOrden] = useState<string | undefined>("nombre");
  const busquedaDebounced = useDebounce(busqueda);
  const verCostos = tiene("productos.editar") || tiene("reportes.ganancias");

  const filtros: FiltrosProductos = {
    pagina,
    tamanio: TAMANIO,
    orden,
    busqueda: busquedaDebounced || undefined,
    categoria_id: categoria === TODAS ? undefined : Number(categoria),
    estado: estado === "todos" || estado === "inactivos" ? undefined : estado,
    activo: estado !== "inactivos",
  };
  const consulta = useQuery({
    queryKey: ["productos", "lista", filtros],
    queryFn: ({ signal }) => productosService.listar(filtros, signal),
    placeholderData: keepPreviousData,
  });
  const resumen = useQuery({ queryKey: ["productos", "resumen"], queryFn: productosService.resumen });
  const categorias = useQuery({ queryKey: ["categorias"], queryFn: () => categoriasService.listar(true) });

  const accion = useMutation({
    mutationFn: ({ fn }: { fn: () => Promise<unknown>; exito: string }) => fn(),
    onSuccess: (_, { exito }) => {
      toast.success(exito);
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
    },
    onError: (error) => toast.error(mensajeError(error)),
  });

  const exportar = useMutation({
    mutationFn: () => productosService.exportar(),
    onError: (error) => toast.error(mensajeError(error)),
  });

  const cambiarFiltro = (fn: () => void) => {
    fn();
    setPagina(1);
  };

  const columnas = useMemo<ColumnDef<ProductoListado, unknown>[]>(
    () => [
      {
        id: "nombre",
        header: "Producto",
        meta: { orden: "nombre", className: "sm:min-w-72" } satisfies MetaColumna,
        cell: ({ row: { original: p } }) => (
          <Link href={`/productos/${p.id}`} className="group flex items-center gap-3">
            <ImagenProducto id={p.id} nombre={p.nombre} url={p.miniatura_url} />
            <div className="min-w-0">
              <p className="truncate font-bold group-hover:underline">{p.nombre}</p>
              <p className="truncate text-xs text-muted-foreground tabular">
                {p.codigo_barras ?? (p.codigo_interno ? `Interno ${p.codigo_interno}` : "Sin código")}
                {p.maneja_lotes && " · con lotes"}
              </p>
            </div>
          </Link>
        ),
      },
      {
        id: "categoria",
        header: "Categoría",
        meta: { className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: p } }) =>
          p.categoria ? (
            <span className="inline-flex items-center gap-2 text-[13px] font-semibold whitespace-nowrap">
              <span aria-hidden className="size-2 rounded-full" style={{ background: p.categoria.color ?? "#8a93a6" }} />
              {p.categoria.nombre}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        id: "precio",
        header: "Precio venta",
        meta: { orden: "precio", numero: true } satisfies MetaColumna,
        cell: ({ row }) => <span className="font-bold">{soles(row.original.precio_venta)}</span>,
      },
      ...(verCostos
        ? ([
            {
              id: "costo",
              header: "Costo",
              meta: { numero: true, className: "hidden md:table-cell" } satisfies MetaColumna,
              cell: ({ row }) => <span className="text-muted-foreground">{Number(row.original.precio_costo).toFixed(2)}</span>,
            },
            {
              id: "margen",
              header: "Margen",
              meta: { numero: true, className: "hidden md:table-cell" } satisfies MetaColumna,
              cell: ({ row }) =>
                row.original.margen === null ? (
                  <span className="text-muted-foreground">—</span>
                ) : (
                  <span className={cn("font-semibold", Number(row.original.margen) < 10 && "text-destructive")}>
                    {row.original.margen}%
                  </span>
                ),
            },
          ] satisfies ColumnDef<ProductoListado, unknown>[])
        : []),
      {
        id: "stock",
        header: "Stock",
        meta: { orden: "stock", numero: true } satisfies MetaColumna,
        cell: ({ row: { original: p } }) => <CeldaStock producto={p} />,
      },
      {
        id: "acciones",
        header: () => <span className="sr-only">Acciones</span>,
        meta: { className: "w-px text-right" } satisfies MetaColumna,
        cell: ({ row: { original: p } }) => (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-sm" aria-label={`Acciones de ${p.nombre}`}>
                <Ellipsis />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuItem onSelect={() => router.push(`/productos/${p.id}`)}>
                <Pencil /> {tiene("productos.editar") ? "Ver y editar" : "Ver ficha"}
              </DropdownMenuItem>
              {tiene("inventario.kardex") && (
                <DropdownMenuItem onSelect={() => router.push(`/inventario/kardex?producto=${p.id}`)}>
                  <History /> Ver kardex
                </DropdownMenuItem>
              )}
              {tiene("productos.editar") && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={async () => {
                      const detalle = await productosService.obtener(p.id);
                      accion.mutate({
                        fn: () => productosService.actualizar(p.id, { version: detalle.version, activo: !p.activo }),
                        exito: p.activo ? `${p.nombre} ya no aparece en ventas` : `${p.nombre} se activó`,
                      });
                    }}
                  >
                    <Power /> {p.activo ? "Desactivar" : "Activar"}
                  </DropdownMenuItem>
                </>
              )}
              {tiene("productos.eliminar") && (
                <DropdownMenuItem
                  variant="destructive"
                  onSelect={() =>
                    accion.mutate({ fn: () => productosService.eliminar(p.id), exito: `${p.nombre} se eliminó` })
                  }
                >
                  <Trash2 /> Eliminar
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ],
    [verCostos, tiene, router, accion],
  );

  const totalCategorias = categorias.data?.length ?? 0;
  const principales = (categorias.data ?? []).filter((c) => c.productos > 0).sort((a, b) => b.productos - a.productos);

  return (
    <>
      <PageHeader
        titulo="Productos"
        linea={
          resumen.data
            ? `${resumen.data.activos} productos activos en ${totalCategorias} categorías`
            : "Catálogo de la tienda"
        }
        acciones={
          <>
            {tiene("productos.importar") && (
              <Button variant="outline" asChild>
                <Link href="/productos/importar">
                  <FileSpreadsheet /> Importar Excel
                </Link>
              </Button>
            )}
            {tiene("productos.exportar") && (
              <Button variant="outline" onClick={() => exportar.mutate()} disabled={exportar.isPending}>
                <Download /> Exportar
              </Button>
            )}
            {tiene("productos.crear") && (
              <Button asChild>
                <Link href="/productos/nuevo">
                  <Plus strokeWidth={2.6} /> Nuevo producto
                </Link>
              </Button>
            )}
          </>
        }
      />

      <section className="mb-4 grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
        <Indicador etiqueta="Activos" valor={resumen.data?.activos} oscuro onClick={() => cambiarFiltro(() => setEstado("todos"))} />
        <Indicador
          etiqueta="Stock bajo"
          valor={resumen.data?.stock_bajo}
          alerta={!!resumen.data?.stock_bajo}
          detalle="por debajo del mínimo"
          onClick={() => cambiarFiltro(() => setEstado("bajo"))}
        />
        <Indicador
          etiqueta="Sin stock"
          valor={resumen.data?.sin_stock}
          detalle={resumen.data?.negativos ? `${resumen.data.negativos} en negativo` : "en el almacén de venta"}
          onClick={() => cambiarFiltro(() => setEstado("sin_stock"))}
        />
        <Indicador
          etiqueta="Sin código de barras"
          valor={resumen.data?.sin_codigo}
          detalle="se buscan por nombre"
          onClick={() => cambiarFiltro(() => setEstado("sin_codigo"))}
        />
      </section>

      <DataTable
        barra={
          <>
            <label className="flex h-[38px] items-center gap-2 rounded-[10px] bg-muted px-3 text-muted-foreground sm:w-72">
              <Search className="size-4 flex-none" />
              <Input
                value={busqueda}
                onChange={(e) => cambiarFiltro(() => setBusqueda(e.target.value))}
                placeholder="Nombre o código de barras"
                className="h-auto border-0 bg-transparent p-0 text-foreground focus-visible:ring-0 dark:bg-transparent"
                aria-label="Buscar productos"
              />
            </label>
            <Pestanas
              etiqueta="Filtrar por categoría"
              valor={principales.slice(0, 3).some((c) => String(c.id) === categoria) || categoria === TODAS ? categoria : TODAS}
              onCambiar={(v) => cambiarFiltro(() => setCategoria(v))}
              opciones={[
                { valor: TODAS, etiqueta: "Todas" },
                ...principales.slice(0, 3).map((c) => ({ valor: String(c.id), etiqueta: c.nombre, cantidad: c.productos })),
              ]}
            />
            <Select value={categoria} onValueChange={(v) => cambiarFiltro(() => setCategoria(v))}>
              <SelectTrigger className="h-[34px] w-full rounded-[10px] border-0 bg-muted font-semibold sm:w-40" aria-label="Categoría">
                <SelectValue placeholder="Más" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODAS}>Todas</SelectItem>
                {(categorias.data ?? []).map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.nombre} ({c.productos})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={estado} onValueChange={(v) => cambiarFiltro(() => setEstado(v as Estado))}>
              <SelectTrigger className="h-[34px] w-full rounded-[10px] border-0 bg-muted font-semibold sm:ml-auto sm:w-36" aria-label="Mostrar">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todo el stock</SelectItem>
                <SelectItem value="bajo">Stock bajo</SelectItem>
                <SelectItem value="sin_stock">Sin stock</SelectItem>
                <SelectItem value="negativo">En negativo</SelectItem>
                <SelectItem value="sin_codigo">Sin código</SelectItem>
                <SelectItem value="inactivos">Inactivos</SelectItem>
              </SelectContent>
            </Select>

          </>
        }
        columnas={columnas}
        datos={consulta.data?.items}
        cargando={consulta.isLoading}
        total={consulta.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        orden={orden}
        onOrden={setOrden}
        claseFila={(p) =>
          !p.activo ? "opacity-60" : p.estado_stock === "bajo" || p.estado_stock === "negativo" ? "bg-pill-negative-bg/40" : undefined
        }
        vacio={
          busquedaDebounced ? (
            `Ningún producto coincide con «${busquedaDebounced}». Prueba con otra palabra o escanea el código.`
          ) : tiene("productos.crear") ? (
            <>
              No hay productos en esta vista.{" "}
              <Link href="/productos/nuevo" className="font-bold text-foreground underline">
                Crea el primero
              </Link>{" "}
              o impórtalos desde Excel.
            </>
          ) : (
            "No hay productos en esta vista."
          )
        }
      />
    </>
  );
}

function CeldaStock({ producto: p }: { producto: ProductoListado }) {
  const unidad = unidadCorta(p.unidad_medida);
  if (p.estado_stock === "sin_stock") return <span className="font-bold text-destructive">Sin stock</span>;
  if (p.estado_stock === "negativo")
    return (
      <span className="font-bold text-destructive" title="Se vendió sin stock: regularizar con una compra o ajuste">
        {cantidad(p.stock)} {unidad}
      </span>
    );
  if (p.estado_stock === "bajo")
    return (
      <span className="font-bold whitespace-nowrap text-destructive">
        {cantidad(p.stock)} <span className="font-medium text-muted-foreground">/ mín {cantidad(p.stock_minimo)}</span>
      </span>
    );
  return (
    <span className="font-bold whitespace-nowrap">
      {cantidad(p.stock)} <span className="font-medium text-muted-foreground">{unidad}</span>
    </span>
  );
}
