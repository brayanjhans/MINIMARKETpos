"use client";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { FormularioProducto } from "@/components/productos/FormularioProducto";

export default function NuevoProductoPage() {
  return (
    <RequierePermiso permiso="productos.crear">
      <FormularioProducto />
    </RequierePermiso>
  );
}
