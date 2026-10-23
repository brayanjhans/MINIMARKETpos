"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { History, ImageUp, Loader2, Plus, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ReactNode, useRef, useState } from "react";
import { toast } from "sonner";

import { Pildora } from "@/components/comunes/Pildora";
import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/hooks/useAuth";
import { ApiError, mensajeError } from "@/lib/api";
import { cantidad, unidadCorta } from "@/lib/inventario";
import { cn, fecha, soles } from "@/lib/utils";
import { categoriasService } from "@/services/categorias.service";
import { productosService } from "@/services/productos.service";
import {
  type AfectacionIGV,
  type PresentacionEntrada,
  type ProductoDetalle,
  type ProductoEntrada,
  UNIDADES,
  type UnidadMedida,
} from "@/types/productos";

const SIN = "ninguna";
const PRECIO = /^\d{1,6}([.,]\d{1,2})?$/;
const COSTO = /^\d{1,6}([.,]\d{1,4})?$/;
const CODIGO = /^[0-9A-Za-z.-]{3,50}$/;
const num = (t: string) => t.trim().replace(",", ".");
/** "5.3000" -> "5.30", "4.1235" -> "4.1235" (el costo admite hasta 4 decimales) */
const montoEditable = (valor: string) => {
  const n = Number(valor);
  return Number.isInteger(Math.round(n * 10000) / 100) ? n.toFixed(2) : String(n);
};

interface Presentacion extends PresentacionEntrada {
  clave: string;
  codigo: string;
}

interface Estado {
  nombre: string;
  descripcion: string;
  codigo_interno: string;
  codigos: string[];
  categoria: string;
  marca: string;
  unidad_medida: UnidadMedida;
  precio_costo: string;
  precio_venta: string;
  stock_minimo: string;
  tipo_afectacion_igv: AfectacionIGV;
  afecto_icbper: boolean;
  maneja_lotes: boolean;
  permite_decimales: boolean;
  presentaciones: Presentacion[];
}

function estadoInicial(p?: ProductoDetalle): Estado {
  return {
    nombre: p?.nombre ?? "",
    descripcion: p?.descripcion ?? "",
    codigo_interno: p?.codigo_interno ?? "",
    codigos: p?.codigos.length ? p.codigos : [""],
    categoria: p?.categoria ? String(p.categoria.id) : SIN,
    marca: p?.marca ? String(p.marca.id) : SIN,
    unidad_medida: p?.unidad_medida ?? "UNIDAD",
    precio_costo: p?.precio_costo ? montoEditable(p.precio_costo) : "",
    precio_venta: p ? Number(p.precio_venta).toFixed(2) : "",
    stock_minimo: p ? String(Number(p.stock_minimo)) : "0",
    tipo_afectacion_igv: p?.tipo_afectacion_igv ?? "GRAVADO",
    afecto_icbper: p?.afecto_icbper ?? false,
    maneja_lotes: p?.maneja_lotes ?? false,
    permite_decimales: p?.permite_decimales ?? false,
    presentaciones: (p?.presentaciones ?? [])
      .filter((x) => x.activo)
      .map((x) => ({
        clave: String(x.id),
        id: x.id,
        nombre: x.nombre,
        factor: String(Number(x.factor)),
        precio_venta: Number(x.precio_venta).toFixed(2),
        codigo: x.codigos[0] ?? "",
        codigos: x.codigos,
      })),
  };
}

/** Errores de los campos (la API los valida otra vez; esto es para avisar antes de guardar). */
function validar(e: Estado): string | null {
  if (e.nombre.trim().length < 2) return "Escribe el nombre del producto";
  if (!PRECIO.test(e.precio_venta.trim())) return "El precio de venta debe ser un monto como 6.50";
  if (e.precio_costo.trim() && !COSTO.test(e.precio_costo.trim())) return "El costo debe ser un monto como 4.80";
  if (!/^\d{1,6}([.,]\d{1,3})?$/.test(e.stock_minimo.trim())) return "El stock mínimo debe ser un número";
  if (!e.permite_decimales && !Number.isInteger(Number(num(e.stock_minimo))))
    return "El stock mínimo debe ser entero (el producto no admite decimales)";
  const codigos = e.codigos.map((c) => c.trim()).filter(Boolean);
  for (const c of [...codigos, ...e.presentaciones.map((p) => p.codigo.trim()).filter(Boolean)]) {
    if (!CODIGO.test(c)) return `El código «${c}» no es válido (solo letras, números, punto y guion)`;
  }
  const todos = [...codigos, ...e.presentaciones.map((p) => p.codigo.trim()).filter(Boolean)].map((c) => c.toUpperCase());
  if (new Set(todos).size !== todos.length) return "Hay un código de barras repetido";
  for (const p of e.presentaciones) {
    if (!p.nombre.trim()) return "Escribe el nombre de cada presentación";
    if (!/^\d{1,6}$/.test(p.factor.trim()) || Number(p.factor) < 2)
      return `«${p.nombre}» debe contener 2 o más unidades`;
    if (!PRECIO.test(p.precio_venta.trim())) return `El precio de «${p.nombre}» no es válido`;
  }
  const nombres = e.presentaciones.map((p) => p.nombre.trim().toLowerCase());
  if (new Set(nombres).size !== nombres.length) return "Hay dos presentaciones con el mismo nombre";
  return null;
}

function aEntrada(e: Estado, incluirCosto: boolean): ProductoEntrada {
  return {
    nombre: e.nombre.trim(),
    descripcion: e.descripcion.trim() || null,
    codigo_interno: e.codigo_interno.trim() || null,
    codigos: e.codigos.map((c) => c.trim()).filter(Boolean),
    categoria_id: e.categoria === SIN ? null : Number(e.categoria),
    marca_id: e.marca === SIN ? null : Number(e.marca),
    unidad_medida: e.unidad_medida,
    precio_venta: num(e.precio_venta),
    ...(incluirCosto ? { precio_costo: num(e.precio_costo || "0") } : {}),
    stock_minimo: num(e.stock_minimo),
    tipo_afectacion_igv: e.tipo_afectacion_igv,
    afecto_icbper: e.afecto_icbper,
    maneja_lotes: e.maneja_lotes,
    permite_decimales: e.permite_decimales,
    presentaciones: e.presentaciones.map((p) => ({
      id: p.id ?? null,
      nombre: p.nombre.trim(),
      factor: p.factor.trim(),
      precio_venta: num(p.precio_venta),
      codigos: p.codigo.trim() ? [p.codigo.trim()] : [],
    })),
  };
}

export function FormularioProducto({ producto }: { producto?: ProductoDetalle }) {
  const { tiene } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [e, setE] = useState<Estado>(() => estadoInicial(producto));
  const [error, setError] = useState<string | null>(null);
  const esNuevo = !producto;
  const puedeEditar = esNuevo ? tiene("productos.crear") : tiene("productos.editar");
  const bloqueado = !!producto?.tiene_movimientos;
  const verCostos = tiene("productos.editar") || tiene("reportes.ganancias");

  const categorias = useQuery({ queryKey: ["categorias"], queryFn: () => categoriasService.listar(true) });
  const marcas = useQuery({ queryKey: ["marcas"], queryFn: () => categoriasService.marcas(true) });
  const historial = useQuery({
    queryKey: ["productos", producto?.id, "historial"],
    queryFn: () => productosService.historialPrecios(producto!.id),
    enabled: !!producto && tiene("productos.editar"),
  });

  const cambiar = <K extends keyof Estado>(campo: K, valor: Estado[K]) => {
    setE((x) => ({ ...x, [campo]: valor }));
    setError(null);
  };

  const guardar = useMutation({
    mutationFn: async () => {
      const problema = validar(e);
      if (problema) throw new Error(problema);
      if (esNuevo) return productosService.crear(aEntrada(e, true));
      return productosService.actualizar(producto.id, {
        ...aEntrada(e, !bloqueado),
        activo: undefined,
        version: producto.version,
      });
    },
    onSuccess: (resultado) => {
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
      queryClient.setQueryData(["productos", "detalle", resultado.id], resultado);
      toast.success(esNuevo ? `${resultado.nombre} se creó` : "Cambios guardados");
      if (esNuevo) router.replace(`/productos/${resultado.id}`);
      else setE(estadoInicial(resultado));
    },
    onError: (err) => {
      if (err instanceof ApiError && err.codigo === "version_desactualizada") {
        toast.error(err.message, {
          duration: 10_000,
          action: {
            label: "Recargar",
            onClick: () => void queryClient.invalidateQueries({ queryKey: ["productos", "detalle", producto?.id] }),
          },
        });
        return;
      }
      setError(mensajeError(err));
    },
  });

  const precio = Number(num(e.precio_venta)) || 0;
  const costo = Number(num(e.precio_costo)) || 0;
  const ganancia = precio - costo;

  return (
    <form
      onSubmit={(ev) => {
        ev.preventDefault();
        guardar.mutate();
      }}
    >
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="min-w-0">
          <Link href="/productos" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
            Productos ›
          </Link>
          <h1 className="flex flex-wrap items-center gap-2.5 text-[24px] leading-8 font-extrabold tracking-[-0.02em]">
            {esNuevo ? "Nuevo producto" : producto.nombre}
            {producto && (
              <Pildora tono={producto.activo ? "positivo" : "neutro"}>{producto.activo ? "Activo" : "Inactivo"}</Pildora>
            )}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
          {producto && tiene("inventario.kardex") && (
            <Button variant="outline" asChild>
              <Link href={`/inventario/kardex?producto=${producto.id}`}>
                <History /> Ver kardex
              </Link>
            </Button>
          )}
          <Button variant="outline" type="button" onClick={() => router.push("/productos")}>
            {puedeEditar ? "Cancelar" : "Volver"}
          </Button>
          {puedeEditar && (
            <Button type="submit" disabled={guardar.isPending}>
              {guardar.isPending && <Loader2 className="animate-spin" />}
              {esNuevo ? "Crear producto" : "Guardar cambios"}
            </Button>
          )}
        </div>
      </div>

      {error && (
        <p role="alert" className="mb-4 rounded-xl bg-pill-negative-bg px-4 py-3 text-sm font-semibold text-pill-negative-ink">
          {error}
        </p>
      )}

      <fieldset disabled={!puedeEditar || guardar.isPending} className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex min-w-0 flex-col gap-4">
          <Seccion titulo="Datos del producto">
            <div className="grid gap-3 sm:grid-cols-2">
              <Campo etiqueta="Nombre" className="sm:col-span-2">
                <Input
                  value={e.nombre}
                  onChange={(ev) => cambiar("nombre", ev.target.value)}
                  maxLength={200}
                  placeholder="Ej. Gaseosa Inca Kola 1.5 L"
                  autoFocus={esNuevo}
                />
              </Campo>
              <Campo etiqueta="Código de barras" ayuda="Escanéalo aquí. Puedes agregar otro si el producto trae dos.">
                <div className="flex flex-col gap-2">
                  {e.codigos.map((c, i) => (
                    <div key={i} className="flex gap-2">
                      <Input
                        value={c}
                        onChange={(ev) =>
                          cambiar(
                            "codigos",
                            e.codigos.map((x, j) => (j === i ? ev.target.value : x)),
                          )
                        }
                        onKeyDown={(ev) => ev.key === "Enter" && ev.preventDefault()}
                        maxLength={50}
                        inputMode="numeric"
                        className="tabular"
                        placeholder="7750182006116"
                        aria-label={`Código de barras ${i + 1}`}
                      />
                      {e.codigos.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          aria-label="Quitar código"
                          onClick={() => cambiar("codigos", e.codigos.filter((_, j) => j !== i))}
                        >
                          <X />
                        </Button>
                      )}
                    </div>
                  ))}
                  {e.codigos.length < 5 && (
                    <button
                      type="button"
                      onClick={() => cambiar("codigos", [...e.codigos, ""])}
                      className="self-start text-[13px] font-bold hover:underline"
                    >
                      + Otro código
                    </button>
                  )}
                </div>
              </Campo>
              <Campo etiqueta="Código interno" ayuda="Opcional. Útil para productos sin código de barras.">
                <Input value={e.codigo_interno} onChange={(ev) => cambiar("codigo_interno", ev.target.value)} maxLength={30} />
              </Campo>
              <Campo etiqueta="Categoría">
                <Select value={e.categoria} onValueChange={(v) => cambiar("categoria", v)}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SIN}>Sin categoría</SelectItem>
                    {(categorias.data ?? []).map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Campo>
              <Campo etiqueta="Marca">
                <SelectorMarca
                  valor={e.marca}
                  onCambiar={(v) => cambiar("marca", v)}
                  marcas={marcas.data ?? []}
                  puedeCrear={tiene("marcas.crear")}
                />
              </Campo>
              <Campo
                etiqueta="Unidad de medida"
                ayuda={bloqueado ? "No se cambia: el producto ya tiene movimientos de stock." : undefined}
              >
                <Select
                  value={e.unidad_medida}
                  disabled={bloqueado}
                  onValueChange={(v) => {
                    const unidad = v as UnidadMedida;
                    setE((x) => ({
                      ...x,
                      unidad_medida: unidad,
                      permite_decimales: ["KILOGRAMO", "LITRO"].includes(unidad) ? true : x.permite_decimales,
                    }));
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIDADES.map((u) => (
                      <SelectItem key={u.valor} value={u.valor}>
                        {u.etiqueta}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Campo>
            </div>
          </Seccion>

          <Seccion titulo="Precio e impuestos">
            <div className="grid gap-3 sm:grid-cols-2">
              {verCostos && (
                <Campo
                  etiqueta={bloqueado ? "Costo (promedio)" : "Costo"}
                  ayuda={bloqueado ? "Se actualiza solo con cada compra." : "Lo que te cuesta cada unidad."}
                >
                  <Dinero valor={e.precio_costo} onCambiar={(v) => cambiar("precio_costo", v)} disabled={bloqueado} />
                </Campo>
              )}
              <Campo etiqueta="Precio de venta (incluye IGV)">
                <Dinero valor={e.precio_venta} onCambiar={(v) => cambiar("precio_venta", v)} />
              </Campo>
            </div>
            {verCostos && precio > 0 && costo > 0 && (
              <p
                className={cn(
                  "mt-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold",
                  ganancia > 0 ? "bg-pill-positive-bg text-pill-positive-ink" : "bg-pill-negative-bg text-pill-negative-ink",
                )}
              >
                {ganancia > 0
                  ? `Ganas ${soles(ganancia)} por unidad · ${((ganancia / precio) * 100).toFixed(1)}%`
                  : `Pierdes ${soles(-ganancia)} por unidad: el precio está por debajo del costo`}
              </p>
            )}
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
              <span className="text-[13px] font-semibold">Afectación del IGV</span>
              <div role="radiogroup" aria-label="Afectación del IGV" className="flex flex-wrap gap-1.5">
                {(
                  [
                    ["GRAVADO", "Gravado 18%"],
                    ["EXONERADO", "Exonerado"],
                    ["INAFECTO", "Inafecto"],
                  ] as const
                ).map(([valor, texto]) => (
                  <button
                    key={valor}
                    type="button"
                    role="radio"
                    aria-checked={e.tipo_afectacion_igv === valor}
                    onClick={() => cambiar("tipo_afectacion_igv", valor)}
                    className={cn(
                      "h-[34px] rounded-[10px] px-3 text-[13px] font-semibold",
                      e.tipo_afectacion_igv === valor ? "bg-navy font-bold text-white dark:bg-secondary dark:text-secondary-foreground" : "bg-muted",
                    )}
                  >
                    {texto}
                  </button>
                ))}
              </div>
            </div>
            <Interruptor
              etiqueta="Cobrar impuesto a la bolsa (ICBPER)"
              ayuda="Solo para bolsas plásticas: se cobra por cada unidad vendida."
              valor={e.afecto_icbper}
              onCambiar={(v) => cambiar("afecto_icbper", v)}
            />
          </Seccion>

          <Seccion
            titulo="Presentaciones"
            accion={
              e.presentaciones.length < 10 && (
                <button
                  type="button"
                  className="text-[13px] font-bold hover:underline"
                  onClick={() =>
                    cambiar("presentaciones", [
                      ...e.presentaciones,
                      { clave: crypto.getRandomValues(new Uint32Array(1))[0]!.toString(36), nombre: "", factor: "6", precio_venta: "", codigo: "", codigos: [] },
                    ])
                  }
                >
                  + Agregar presentación
                </button>
              )
            }
          >
            <p className="mb-3 text-[13px] text-muted-foreground">
              Six pack, caja x12… Cada una tiene su propio código y precio; al venderla se descuentan sus unidades del
              stock.
            </p>
            <div className="scrollbar-fino overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead>
                  <tr className="text-left text-xs font-bold text-muted-foreground">
                    <th className="pb-2 font-bold">Nombre</th>
                    <th className="pb-2 font-bold">Código de barras</th>
                    <th className="pb-2 font-bold">Unidades</th>
                    <th className="pb-2 font-bold">Precio</th>
                    <th className="pb-2 text-right font-bold">Por unidad</th>
                    <th className="w-8" />
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-rule text-muted-foreground">
                    <td className="py-2.5 font-semibold text-foreground">Unidad</td>
                    <td className="tabular">{e.codigos[0] || "—"}</td>
                    <td className="tabular">1</td>
                    <td className="tabular">{precio ? soles(precio) : "—"}</td>
                    <td className="text-right tabular">{precio ? precio.toFixed(2) : "—"}</td>
                    <td />
                  </tr>
                  {e.presentaciones.map((p, i) => {
                    const actualizar = (cambio: Partial<Presentacion>) =>
                      cambiar(
                        "presentaciones",
                        e.presentaciones.map((x, j) => (j === i ? { ...x, ...cambio } : x)),
                      );
                    const porUnidad = Number(num(p.precio_venta)) / Number(p.factor);
                    return (
                      <tr key={p.clave} className="border-t border-rule">
                        <td className="py-2 pr-2">
                          <Input value={p.nombre} onChange={(ev) => actualizar({ nombre: ev.target.value })} placeholder="Six pack" maxLength={80} aria-label="Nombre de la presentación" />
                        </td>
                        <td className="pr-2">
                          <Input value={p.codigo} onChange={(ev) => actualizar({ codigo: ev.target.value })} onKeyDown={(ev) => ev.key === "Enter" && ev.preventDefault()} className="tabular" maxLength={50} aria-label="Código de la presentación" />
                        </td>
                        <td className="w-20 pr-2">
                          <Input value={p.factor} onChange={(ev) => actualizar({ factor: ev.target.value })} inputMode="numeric" className="tabular" aria-label="Unidades que contiene" />
                        </td>
                        <td className="w-28 pr-2">
                          <Dinero valor={p.precio_venta} onCambiar={(v) => actualizar({ precio_venta: v })} />
                        </td>
                        <td className="text-right text-muted-foreground tabular">
                          {Number.isFinite(porUnidad) && porUnidad > 0 ? porUnidad.toFixed(2) : "—"}
                        </td>
                        <td className="pl-1">
                          <Button type="button" variant="ghost" size="icon-sm" aria-label={`Quitar ${p.nombre || "presentación"}`} onClick={() => cambiar("presentaciones", e.presentaciones.filter((_, j) => j !== i))}>
                            <X />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Seccion>
        </div>

        <div className="flex min-w-0 flex-col gap-4">
          <Seccion titulo="Inventario">
            <Campo etiqueta="Stock mínimo (avisar desde)">
              <Input
                value={e.stock_minimo}
                onChange={(ev) => cambiar("stock_minimo", ev.target.value)}
                inputMode="decimal"
                className="tabular"
              />
            </Campo>
            <Interruptor
              etiqueta="Controlar lotes y vencimientos"
              ayuda={bloqueado ? "No se cambia: ya tiene movimientos de stock." : "Para lácteos, embutidos y todo lo que vence."}
              valor={e.maneja_lotes}
              onCambiar={(v) => cambiar("maneja_lotes", v)}
              disabled={bloqueado}
            />
            <Interruptor
              etiqueta="Se vende con decimales (kg, L)"
              ayuda={bloqueado ? "No se cambia: ya tiene movimientos de stock." : "Para productos a granel."}
              valor={e.permite_decimales}
              onCambiar={(v) => cambiar("permite_decimales", v)}
              disabled={bloqueado}
            />
          </Seccion>

          {producto ? (
            <SeccionImagen producto={producto} puedeEditar={puedeEditar} />
          ) : (
            <Seccion titulo="Imagen">
              <p className="text-sm text-muted-foreground">Podrás subir la foto después de crear el producto.</p>
            </Seccion>
          )}

          {producto && (
            <Seccion titulo="Stock por almacén">
              {producto.stock_por_almacen.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Aún no tiene stock.{" "}
                  {tiene("inventario.stock_inicial") && (
                    <Link href="/inventario/stock-inicial" className="font-bold text-foreground underline">
                      Cargar stock inicial
                    </Link>
                  )}
                </p>
              ) : (
                <ul className="flex flex-col">
                  {producto.stock_por_almacen.map((s) => (
                    <li key={s.almacen_id} className="flex justify-between border-b border-rule py-2 text-sm last:border-0">
                      <span>
                        {s.almacen}
                        <span className="text-muted-foreground"> · {s.sucursal}</span>
                      </span>
                      <b className={cn("tabular", Number(s.cantidad) < 0 && "text-destructive")}>
                        {cantidad(s.cantidad)} {unidadCorta(producto.unidad_medida)}
                      </b>
                    </li>
                  ))}
                  {verCostos && (
                    <li className="pt-2 text-xs text-muted-foreground">
                      Valor:{" "}
                      {soles(
                        producto.stock_por_almacen.reduce((t, s) => t + Math.max(Number(s.cantidad), 0), 0) *
                          Number(producto.precio_costo),
                      )}{" "}
                      al costo promedio
                    </li>
                  )}
                </ul>
              )}
            </Seccion>
          )}

          {producto && tiene("productos.editar") && (
            <Seccion titulo="Cambios de precio">
              {!historial.data?.length ? (
                <p className="text-sm text-muted-foreground">Sin cambios todavía.</p>
              ) : (
                <ul className="flex flex-col">
                  {historial.data.slice(0, 8).map((h) => {
                    const presentacion = producto.presentaciones.find((p) => p.id === h.presentacion_id);
                    return (
                      <li key={h.id} className="border-b border-rule py-2 text-sm last:border-0">
                        <p>
                          <b>{presentacion?.nombre ?? (h.tipo === "VENTA" ? "Venta" : "Costo")}</b>{" "}
                          <span className="tabular">
                            {Number(h.precio_anterior).toFixed(2)} → {Number(h.precio_nuevo).toFixed(2)}
                          </span>
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {fecha(h.creado_en)} · {h.origen === "MANUAL" ? (h.usuario ?? "—") : h.origen.toLowerCase().replace("_", " ")}
                        </p>
                      </li>
                    );
                  })}
                </ul>
              )}
            </Seccion>
          )}
        </div>
      </fieldset>
    </form>
  );
}

function SeccionImagen({ producto, puedeEditar }: { producto: ProductoDetalle; puedeEditar: boolean }) {
  const queryClient = useQueryClient();
  const archivo = useRef<HTMLInputElement>(null);
  const [arrastrando, setArrastrando] = useState(false);

  const subir = useMutation({
    mutationFn: (file: File | null) =>
      file ? productosService.subirImagen(producto.id, file) : productosService.quitarImagen(producto.id),
    onSuccess: (resultado) => {
      queryClient.setQueryData(["productos", "detalle", producto.id], resultado);
      void queryClient.invalidateQueries({ queryKey: ["productos", "lista"] });
      toast.success(resultado.imagen_url ? "Foto guardada" : "Foto quitada");
    },
    onError: (error) => toast.error(mensajeError(error)),
  });

  const elegir = (file: File | undefined) => {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) return toast.error("La foto pesa más de 10 MB");
    subir.mutate(file);
  };

  return (
    <Seccion titulo="Imagen">
      <div
        onDragOver={(ev) => {
          ev.preventDefault();
          if (puedeEditar) setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(ev) => {
          ev.preventDefault();
          setArrastrando(false);
          if (puedeEditar) elegir(ev.dataTransfer.files[0]);
        }}
        className={cn(
          "flex flex-col items-center gap-3 rounded-xl border-2 border-dashed border-input p-4 text-center",
          arrastrando && "border-primary bg-aviso-fondo",
        )}
      >
        {producto.imagen_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- WEBP de 800 px ya optimizado por el servidor
          <img src={producto.imagen_url} alt={producto.nombre} className="size-32 flex-none rounded-xl bg-muted object-cover" />
        ) : (
          <ImagenProducto id={producto.id} nombre={producto.nombre} url={null} className="size-24 text-lg" />
        )}
        <div className="text-[13px] text-muted-foreground">
          {puedeEditar ? (
            <>
              {!subir.isPending && (
                <Button type="button" variant="outline" size="sm" className="mb-2" onClick={() => archivo.current?.click()}>
                  <ImageUp /> {producto.imagen_url ? "Cambiar foto" : "Subir foto"}
                </Button>
              )}
              <p>Arrastra aquí o elige: JPG, PNG, WEBP o foto de iPhone (HEIC).</p>
              <p className="mt-1">Se convierte sola a WEBP liviano: una foto de 4 MB queda en unos 40 KB.</p>
              {producto.imagen_url && (
                <button type="button" className="mt-1.5 inline-flex items-center gap-1 font-bold text-destructive" onClick={() => subir.mutate(null)}>
                  <Trash2 className="size-3.5" /> Quitar foto
                </button>
              )}
            </>
          ) : (
            <p>{producto.imagen_url ? "" : "Sin foto"}</p>
          )}
          {subir.isPending && (
            <p className="mt-1 inline-flex items-center gap-1.5 font-semibold text-foreground">
              <Loader2 className="size-3.5 animate-spin" /> Optimizando foto…
            </p>
          )}
        </div>
        <input
          ref={archivo}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/heic,image/heif,.heic,.heif"
          className="hidden"
          onChange={(ev) => {
            elegir(ev.target.files?.[0]);
            ev.target.value = "";
          }}
        />
      </div>
    </Seccion>
  );
}

function SelectorMarca({
  valor,
  onCambiar,
  marcas,
  puedeCrear,
}: {
  valor: string;
  onCambiar: (v: string) => void;
  marcas: { id: number; nombre: string }[];
  puedeCrear: boolean;
}) {
  const queryClient = useQueryClient();
  const [nueva, setNueva] = useState<string | null>(null);
  const crear = useMutation({
    mutationFn: (nombre: string) => categoriasService.crearMarca(nombre),
    onSuccess: (marca) => {
      void queryClient.invalidateQueries({ queryKey: ["marcas"] });
      onCambiar(String(marca.id));
      setNueva(null);
    },
    onError: (error) => toast.error(mensajeError(error)),
  });

  if (nueva !== null) {
    return (
      <div className="flex gap-2">
        <Input
          value={nueva}
          autoFocus
          onChange={(ev) => setNueva(ev.target.value)}
          onKeyDown={(ev) => {
            if (ev.key === "Enter") {
              ev.preventDefault();
              if (nueva.trim()) crear.mutate(nueva.trim());
            }
            if (ev.key === "Escape") setNueva(null);
          }}
          placeholder="Nombre de la marca"
          maxLength={80}
        />
        <Button type="button" variant="navy" disabled={!nueva.trim() || crear.isPending} onClick={() => crear.mutate(nueva.trim())}>
          Crear
        </Button>
      </div>
    );
  }
  return (
    <Select value={valor} onValueChange={(v) => (v === "__nueva" ? setNueva("") : onCambiar(v))}>
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={SIN}>Sin marca</SelectItem>
        {marcas.map((m) => (
          <SelectItem key={m.id} value={String(m.id)}>
            {m.nombre}
          </SelectItem>
        ))}
        {puedeCrear && (
          <SelectItem value="__nueva">
            <Plus /> Nueva marca
          </SelectItem>
        )}
      </SelectContent>
    </Select>
  );
}

function Seccion({ titulo, accion, children }: { titulo: string; accion?: ReactNode; children: ReactNode }) {
  return (
    <section className="tarjeta p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-[15px] font-extrabold">{titulo}</h2>
        {accion}
      </div>
      {children}
    </section>
  );
}

function Campo({ etiqueta, ayuda, className, children }: { etiqueta: string; ayuda?: string; className?: string; children: ReactNode }) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label className="text-[13px] font-semibold">{etiqueta}</Label>
      {children}
      {ayuda && <p className="text-xs text-muted-foreground">{ayuda}</p>}
    </div>
  );
}

function Dinero({ valor, onCambiar, disabled }: { valor: string; onCambiar: (v: string) => void; disabled?: boolean }) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm text-muted-foreground">S/</span>
      <Input
        value={valor}
        onChange={(ev) => onCambiar(ev.target.value)}
        inputMode="decimal"
        disabled={disabled}
        className="pl-8 font-semibold tabular"
        placeholder="0.00"
      />
    </div>
  );
}

function Interruptor({
  etiqueta,
  ayuda,
  valor,
  onCambiar,
  disabled,
}: {
  etiqueta: string;
  ayuda?: string;
  valor: boolean;
  onCambiar: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className={cn("mt-3 flex items-start justify-between gap-3", disabled && "opacity-60")}>
      <span>
        <span className="block text-sm font-semibold">{etiqueta}</span>
        {ayuda && <span className="block text-xs text-muted-foreground">{ayuda}</span>}
      </span>
      <Switch checked={valor} onCheckedChange={onCambiar} disabled={disabled} />
    </label>
  );
}
