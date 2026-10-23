"use client";

import { useQuery } from "@tanstack/react-query";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { inventarioService } from "@/services/inventario.service";

/** Almacén que se consulta. Sin el permiso sucursales.todas solo aparecen los de la sucursal actual. */
export function SelectorAlmacen({ valor, onCambiar }: { valor: number | undefined; onCambiar: (id: number) => void }) {
  const { tiene } = useAuth();
  const almacenes = useQuery({ queryKey: ["almacenes"], queryFn: inventarioService.almacenes, staleTime: 300_000 });
  const visibles = (almacenes.data ?? []).filter((a) => a.es_sucursal_actual || tiene("sucursales.todas"));
  const actual = valor ?? visibles.find((a) => a.es_sucursal_actual && a.es_almacen_venta)?.id;
  if (visibles.length <= 1) return null;
  return (
    <Select value={actual ? String(actual) : undefined} onValueChange={(v) => onCambiar(Number(v))}>
      <SelectTrigger className="h-[34px] w-full rounded-[10px] border-0 bg-card font-semibold sm:w-60" aria-label="Almacén">
        <SelectValue placeholder="Almacén" />
      </SelectTrigger>
      <SelectContent>
        {visibles.map((a) => (
          <SelectItem key={a.id} value={String(a.id)}>
            {a.nombre}
            {!a.es_sucursal_actual && ` · ${a.sucursal}`}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
