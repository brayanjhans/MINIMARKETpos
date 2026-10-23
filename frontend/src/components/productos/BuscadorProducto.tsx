"use client";

import { useQuery } from "@tanstack/react-query";
import { Barcode, Loader2 } from "lucide-react";
import { useId, useRef, useState } from "react";
import { toast } from "sonner";

import { ImagenProducto } from "@/components/productos/ImagenProducto";
import { useDebounce } from "@/hooks/useDebounce";
import { ApiError, mensajeError } from "@/lib/api";
import { cantidad, unidadCorta } from "@/lib/inventario";
import { cn, soles } from "@/lib/utils";
import { productosService } from "@/services/productos.service";
import type { ProductoListado } from "@/types/productos";

interface Props {
  onSeleccionar: (producto: ProductoListado) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

// Los lectores de código de barras "escriben" el código y mandan Enter
const PARECE_CODIGO = /^[0-9A-Za-z.-]{6,50}$/;

/**
 * Campo para agregar productos: escanea un código (Enter) o escribe parte del nombre y elige de la lista.
 * Se usa en ajustes, transferencias, stock inicial e inventario físico.
 */
export function BuscadorProducto({ onSeleccionar, placeholder, className, autoFocus }: Props) {
  const [texto, setTexto] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(0);
  const [buscandoCodigo, setBuscandoCodigo] = useState(false);
  const entrada = useRef<HTMLInputElement>(null);
  const idLista = useId();
  const busqueda = useDebounce(texto.trim(), 200);

  const resultados = useQuery({
    queryKey: ["productos", "buscador", busqueda],
    queryFn: ({ signal }) => productosService.listar({ busqueda, tamanio: 8 }, signal),
    enabled: busqueda.length >= 2,
    staleTime: 30_000,
  });
  const opciones = resultados.data?.items ?? [];

  const elegir = (producto: ProductoListado) => {
    onSeleccionar(producto);
    setTexto("");
    setAbierto(false);
    setActivo(0);
    entrada.current?.focus();
  };

  const alPresionar = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      setAbierto(true);
      const n = opciones.length || 1;
      setActivo((i) => (i + (e.key === "ArrowDown" ? 1 : n - 1)) % n);
      return;
    }
    if (e.key === "Escape") return setAbierto(false);
    if (e.key !== "Enter") return;
    e.preventDefault();
    const valor = texto.trim();
    if (!valor) return;
    // Si la lista está abierta y hay una opción resaltada que coincide con lo escrito, se elige esa
    if (abierto && opciones[activo] && busqueda === valor) return elegir(opciones[activo]);
    if (!PARECE_CODIGO.test(valor)) return setAbierto(true);
    setBuscandoCodigo(true);
    try {
      const { producto } = await productosService.porCodigo(valor);
      elegir(producto);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        toast.error(`No hay ningún producto con el código ${valor}`);
        setTexto("");
      } else {
        toast.error(mensajeError(error));
      }
    } finally {
      setBuscandoCodigo(false);
    }
  };

  return (
    <div className={cn("relative", className)}>
      <label className="flex h-11 items-center gap-2.5 rounded-xl border-2 border-primary bg-muted px-3">
        {buscandoCodigo ? (
          <Loader2 className="size-5 flex-none animate-spin" />
        ) : (
          <Barcode className="size-5 flex-none" />
        )}
        <input
          ref={entrada}
          value={texto}
          autoFocus={autoFocus}
          onChange={(e) => {
            setTexto(e.target.value);
            setAbierto(true);
            setActivo(0);
          }}
          onFocus={() => texto && setAbierto(true)}
          onBlur={() => setTimeout(() => setAbierto(false), 150)}
          onKeyDown={alPresionar}
          placeholder={placeholder ?? "Escanea o busca el producto"}
          aria-label="Escanear o buscar producto"
          role="combobox"
          aria-expanded={abierto && opciones.length > 0}
          aria-controls={idLista}
          aria-autocomplete="list"
          className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
      </label>
      {abierto && busqueda.length >= 2 && (
        <ul
          id={idLista}
          role="listbox"
          className="absolute inset-x-0 top-full z-30 mt-1.5 max-h-80 overflow-y-auto rounded-xl border bg-popover p-1.5 shadow-lg"
        >
          {resultados.isLoading && <li className="px-3 py-2.5 text-sm text-muted-foreground">Buscando…</li>}
          {!resultados.isLoading && opciones.length === 0 && (
            <li className="px-3 py-2.5 text-sm text-muted-foreground">Ningún producto coincide con «{busqueda}»</li>
          )}
          {opciones.map((p, i) => (
            <li
              key={p.id}
              role="option"
              aria-selected={i === activo}
              onMouseDown={(e) => {
                e.preventDefault();
                elegir(p);
              }}
              onMouseEnter={() => setActivo(i)}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-lg px-2.5 py-2",
                i === activo && "bg-accent",
              )}
            >
              <ImagenProducto id={p.id} nombre={p.nombre} url={p.miniatura_url} className="size-8 rounded-lg" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-bold">{p.nombre}</p>
                <p className="truncate text-xs text-muted-foreground tabular">
                  {p.codigo_barras ?? "Sin código"} · stock {cantidad(p.stock)} {unidadCorta(p.unidad_medida)}
                </p>
              </div>
              <span className="text-sm font-semibold tabular">{soles(p.precio_venta)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
