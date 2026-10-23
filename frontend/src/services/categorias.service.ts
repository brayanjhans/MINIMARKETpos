import { api } from "@/lib/api";
import type { Mensaje } from "@/types";
import type { Categoria, Marca } from "@/types/productos";

export interface CategoriaEntrada {
  nombre?: string;
  descripcion?: string | null;
  color?: string | null;
  activo?: boolean;
}

export const categoriasService = {
  listar: (activo?: boolean) => api<Categoria[]>("/categorias", { params: { activo } }),
  crear: (datos: CategoriaEntrada) => api<Categoria>("/categorias", { method: "POST", body: datos }),
  actualizar: (id: number, datos: CategoriaEntrada) =>
    api<Categoria>(`/categorias/${id}`, { method: "PATCH", body: datos }),
  eliminar: (id: number) => api<Mensaje>(`/categorias/${id}`, { method: "DELETE" }),

  marcas: (activo?: boolean) => api<Marca[]>("/marcas", { params: { activo } }),
  crearMarca: (nombre: string) => api<Marca>("/marcas", { method: "POST", body: { nombre } }),
  actualizarMarca: (id: number, datos: { nombre?: string; activo?: boolean }) =>
    api<Marca>(`/marcas/${id}`, { method: "PATCH", body: datos }),
  eliminarMarca: (id: number) => api<Mensaje>(`/marcas/${id}`, { method: "DELETE" }),
};
