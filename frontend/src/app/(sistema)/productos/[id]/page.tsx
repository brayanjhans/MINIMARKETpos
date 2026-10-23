"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { FormularioProducto } from "@/components/productos/FormularioProducto";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, mensajeError } from "@/lib/api";
import { productosService } from "@/services/productos.service";

export default function ProductoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="productos.ver">
      <Producto id={Number(id)} />
    </RequierePermiso>
  );
}

function Producto({ id }: { id: number }) {
  const consulta = useQuery({
    queryKey: ["productos", "detalle", id],
    queryFn: () => productosService.obtener(id),
    enabled: Number.isInteger(id) && id > 0,
  });

  if (consulta.isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-72 w-full rounded-[18px]" />
      </div>
    );
  }
  if (consulta.error || !consulta.data) {
    const noExiste = consulta.error instanceof ApiError && consulta.error.status === 404;
    return (
      <section className="tarjeta max-w-xl p-6">
        <h1 className="text-base font-semibold">{noExiste ? "Este producto no existe" : "No se pudo cargar el producto"}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {noExiste ? "Quizá se eliminó. " : `${mensajeError(consulta.error)} `}
          <Link href="/productos" className="font-bold text-foreground underline">
            Volver a productos
          </Link>
        </p>
      </section>
    );
  }
  // key: al guardar o recargar, el formulario toma la versión nueva del producto
  return <FormularioProducto key={`${consulta.data.id}-${consulta.data.version}`} producto={consulta.data} />;
}
