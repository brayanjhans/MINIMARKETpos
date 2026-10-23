import { api } from "@/lib/api";
import type { SucursalResumen } from "@/types";

export const sucursalesService = {
  listar: () => api<SucursalResumen[]>("/sucursales"),
};
