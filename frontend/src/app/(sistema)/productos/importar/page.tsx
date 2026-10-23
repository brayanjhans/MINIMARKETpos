"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, FileSpreadsheet, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Button } from "@/components/ui/button";
import { mensajeError, nuevaClave } from "@/lib/api";
import { cantidad } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { productosService } from "@/services/productos.service";
import type { FilaImportacion, ResultadoImportacion, VistaImportacion } from "@/types/productos";

type Filtro = "errores" | "todas";

export default function ImportarPage() {
  return (
    <RequierePermiso permiso="productos.importar">
      <Importar />
    </RequierePermiso>
  );
}

function Importar() {
  const queryClient = useQueryClient();
  const entrada = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [vista, setVista] = useState<VistaImportacion | null>(null);
  const [resultado, setResultado] = useState<ResultadoImportacion | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("errores");
  const [clave, setClave] = useState(nuevaClave);
  const [arrastrando, setArrastrando] = useState(false);

  const analizar = useMutation({
    mutationFn: (file: File) => productosService.vistaPrevia(file),
    onSuccess: (v, file) => {
      setArchivo(file);
      setVista(v);
      setResultado(null);
      setFiltro(v.errores ? "errores" : "todas");
      setClave(nuevaClave()); // cada archivo nuevo es una importación distinta
    },
    onError: (e) => toast.error(mensajeError(e), { duration: 8000 }),
  });
  const importar = useMutation({
    mutationFn: () => productosService.importar(archivo!, clave),
    onSuccess: (r) => {
      setResultado(r);
      void queryClient.invalidateQueries({ queryKey: ["productos"] });
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      void queryClient.invalidateQueries({ queryKey: ["categorias"] });
    },
    onError: (e) => toast.error(mensajeError(e), { duration: 8000 }),
  });
  const plantilla = useMutation({ mutationFn: productosService.plantilla, onError: (e) => toast.error(mensajeError(e)) });

  const elegir = (file: File | undefined) => {
    if (!file) return;
    if (!/\.xlsx$/i.test(file.name)) return toast.error("Usa un archivo de Excel (.xlsx)");
    if (file.size > 5 * 1024 * 1024) return toast.error("El archivo pesa más de 5 MB");
    analizar.mutate(file);
  };

  const paso = resultado ? 3 : vista ? 2 : 1;
  const aImportar = vista ? vista.nuevos + vista.actualizan : 0;
  const filas = (vista?.filas ?? []).filter((f) => filtro === "todas" || f.accion === "error");

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div>
          <Link href="/productos" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
            Productos ›
          </Link>
          <h1 className="text-[24px] font-extrabold tracking-[-0.02em]">Importar desde Excel</h1>
        </div>
        <ol className="flex items-center gap-3 lg:ml-auto">
          {["Subir archivo", "Revisar", "Importar"].map((texto, i) => {
            const n = i + 1;
            return (
              <li key={texto} className="flex items-center gap-2.5 text-[13px] font-bold">
                {i > 0 && <span aria-hidden className={cn("h-0.5 w-7", paso >= n ? "bg-primary" : "bg-input")} />}
                <span
                  className={cn(
                    "grid size-[26px] place-items-center rounded-full text-xs",
                    paso > n || (n === 3 && resultado) ? "bg-positive text-white" : paso === n ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                  )}
                >
                  {paso > n || (n === 3 && resultado) ? <Check className="size-3.5" strokeWidth={3} /> : n}
                </span>
                <span className={cn(paso < n && "text-muted-foreground")}>{texto}</span>
              </li>
            );
          })}
        </ol>
      </div>

      {!vista && (
        <section
          onDragOver={(e) => {
            e.preventDefault();
            setArrastrando(true);
          }}
          onDragLeave={() => setArrastrando(false)}
          onDrop={(e) => {
            e.preventDefault();
            setArrastrando(false);
            elegir(e.dataTransfer.files[0]);
          }}
          className={cn("tarjeta flex flex-col items-center gap-4 border-2 border-dashed border-input px-6 py-14 text-center", arrastrando && "border-primary bg-aviso-fondo")}
        >
          <span className="grid size-14 place-items-center rounded-2xl bg-p-verde text-p-verde-t">
            {analizar.isPending ? <Loader2 className="size-7 animate-spin" /> : <FileSpreadsheet className="size-7" />}
          </span>
          <div>
            <p className="text-lg font-extrabold">{analizar.isPending ? "Revisando el archivo…" : "Arrastra aquí tu Excel"}</p>
            <p className="text-sm text-muted-foreground">
              Primero verás qué se crea, qué se actualiza y qué tiene errores. Nada se guarda hasta que confirmes.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <Button disabled={analizar.isPending} onClick={() => entrada.current?.click()}>
              Elegir archivo
            </Button>
            <Button variant="outline" disabled={plantilla.isPending} onClick={() => plantilla.mutate()}>
              Descargar plantilla
            </Button>
          </div>
          <input
            ref={entrada}
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="hidden"
            onChange={(e) => {
              elegir(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </section>
      )}

      {vista && archivo && (
        <div className="flex flex-col gap-4">
          <div className="tarjeta flex flex-wrap items-center gap-3 px-4 py-3">
            <span className="grid size-10 place-items-center rounded-xl bg-p-verde text-xs font-extrabold text-p-verde-t">XLSX</span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-bold">{archivo.name}</p>
              <p className="text-xs text-muted-foreground tabular">{vista.total} filas</p>
            </div>
            {!resultado && (
              <button type="button" className="text-[13px] font-bold hover:underline" onClick={() => entrada.current?.click()}>
                Cambiar archivo
              </button>
            )}
            <button type="button" className="text-[13px] font-bold text-muted-foreground hover:underline" onClick={() => plantilla.mutate()}>
              Descargar plantilla
            </button>
            <input
              ref={entrada}
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={(e) => {
                elegir(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </div>

          {resultado ? (
            <section className="tarjeta flex flex-col items-center gap-3 px-6 py-12 text-center">
              <span className="grid size-14 place-items-center rounded-full bg-positive text-white">
                <Check className="size-7" strokeWidth={3} />
              </span>
              <p className="text-xl font-extrabold">
                {resultado.repetida ? "Esta importación ya se había hecho" : "Importación terminada"}
              </p>
              <p className="text-sm text-muted-foreground">
                {resultado.creados} productos nuevos · {resultado.actualizados} actualizados · {resultado.omitidos} filas con error
                omitidas
                {resultado.con_stock > 0 && ` · stock inicial de ${resultado.con_stock} productos (${soles(resultado.valor_stock)})`}
              </p>
              <div className="flex gap-2">
                <Button asChild>
                  <Link href="/productos">Ver productos</Link>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setVista(null);
                    setArchivo(null);
                    setResultado(null);
                  }}
                >
                  Importar otro archivo
                </Button>
              </div>
            </section>
          ) : (
            <>
              <section className="grid gap-3 sm:grid-cols-3">
                <Resumen tono="verde" texto="Productos nuevos" valor={vista.nuevos} />
                <Resumen tono="azul" texto="Ya existen (se actualiza su precio)" valor={vista.actualizan} />
                <Resumen tono="coral" texto="Con errores (no se importan)" valor={vista.errores} />
              </section>

              <section className="tarjeta overflow-hidden">
                <div className="flex gap-2 p-3">
                  {vista.errores > 0 && (
                    <button
                      type="button"
                      onClick={() => setFiltro("errores")}
                      className={cn("h-8 rounded-[10px] px-3 text-[13px] font-bold", filtro === "errores" ? "bg-pill-negative-bg text-pill-negative-ink" : "bg-muted")}
                    >
                      Ver errores {vista.errores}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setFiltro("todas")}
                    className={cn("h-8 rounded-[10px] px-3 text-[13px] font-semibold", filtro === "todas" ? "bg-navy font-bold text-white" : "bg-muted")}
                  >
                    Todas {vista.total}
                  </button>
                </div>
                <div className="scrollbar-fino max-h-[50vh] overflow-auto">
                  <table className="w-full min-w-[640px] text-sm">
                    <thead className="sticky top-0">
                      <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                        <th className="h-10 px-4">Fila</th>
                        <th className="px-3">Producto</th>
                        <th className="px-3">Código de barras</th>
                        <th className="px-3 text-right">Precio</th>
                        <th className="px-4">Qué pasa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filas.map((f) => (
                        <FilaVista key={f.fila} fila={f} />
                      ))}
                    </tbody>
                  </table>
                  {vista.total > vista.filas.length && (
                    <p className="border-t border-rule px-4 py-2.5 text-xs text-muted-foreground">
                      Se muestran {vista.filas.length} de {vista.total} filas (primero las que tienen error).
                    </p>
                  )}
                </div>
              </section>

              <footer className="flex flex-col gap-3 rounded-2xl bg-navy px-4 py-3 text-white sm:flex-row sm:items-center">
                <p className="flex-1 text-sm text-navy-ink">
                  Se guarda todo junto: si algo falla a la mitad, no queda nada a medias.
                  {vista.errores > 0 && ` Las ${vista.errores} filas con error se omiten (puedes corregirlas y subir el archivo de nuevo).`}
                </p>
                <Button
                  variant="ghost"
                  className="bg-sidebar-border text-white hover:bg-sidebar-border/80 hover:text-white"
                  onClick={() => {
                    setVista(null);
                    setArchivo(null);
                  }}
                >
                  Cancelar
                </Button>
                <Button className="font-extrabold" disabled={!aImportar || importar.isPending} onClick={() => importar.mutate()}>
                  {importar.isPending && <Loader2 className="animate-spin" />}
                  Importar {aImportar} producto{aImportar === 1 ? "" : "s"}
                </Button>
              </footer>
            </>
          )}
        </div>
      )}
    </>
  );
}

function Resumen({ tono, texto, valor }: { tono: "verde" | "azul" | "coral"; texto: string; valor: number }) {
  const clases = { verde: "bg-p-verde text-p-verde-t", azul: "bg-p-azul text-p-azul-t", coral: "bg-p-coral text-p-coral-t" }[tono];
  return (
    <div className={cn("flex flex-col rounded-2xl px-4 py-3.5", clases.split(" ")[0])}>
      <span className={cn("text-[13px] font-bold", clases.split(" ")[1])}>{texto}</span>
      <b className="text-[26px] text-foreground tabular">{valor}</b>
    </div>
  );
}

function FilaVista({ fila: f }: { fila: FilaImportacion }) {
  const etiqueta =
    f.accion === "error"
      ? { texto: f.errores.join(" · "), clase: "bg-pill-negative-bg text-pill-negative-ink" }
      : f.accion === "nuevo"
        ? { texto: f.stock_inicial ? `Nuevo · stock ${cantidad(f.stock_inicial)}` : "Nuevo", clase: "bg-pill-positive-bg text-pill-positive-ink" }
        : f.accion === "actualiza"
          ? { texto: f.stock_inicial ? `Actualiza · stock ${cantidad(f.stock_inicial)}` : "Actualiza el precio", clase: "bg-p-azul text-p-azul-t" }
          : { texto: "Sin cambios", clase: "bg-pill-neutral-bg text-pill-neutral-ink" };
  return (
    <tr className={cn("border-t border-rule", f.accion === "error" && "bg-pill-negative-bg/30")}>
      <td className="px-4 py-2 tabular">{f.fila}</td>
      <td className="px-3">{f.nombre ? <b>{f.nombre}</b> : <i className="text-destructive">(vacío)</i>}</td>
      <td className="px-3 tabular">{f.codigo_barras ?? "—"}</td>
      <td className="px-3 text-right tabular">
        {f.precio_venta !== null ? soles(f.precio_venta) : "—"}
        {f.precio_anterior !== null && f.precio_anterior !== f.precio_venta && (
          <span className="text-xs text-muted-foreground"> (antes {Number(f.precio_anterior).toFixed(2)})</span>
        )}
      </td>
      <td className="px-4 py-1.5">
        <span className={cn("inline-flex min-h-6 items-center rounded-lg px-2.5 py-0.5 text-xs font-bold", etiqueta.clase)}>{etiqueta.texto}</span>
      </td>
    </tr>
  );
}
