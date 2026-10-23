import { api } from "@/lib/api";
import type { Cliente, TipoDocumento } from "@/types/ventas";

export interface ClienteNuevo {
  tipo_documento: TipoDocumento;
  numero_documento: string | null;
  nombre: string;
  telefono?: string | null;
  permite_credito?: boolean;
  limite_credito?: string;
}

export const clientesService = {
  buscar: (texto: string, signal?: AbortSignal) => api<Cliente[]>("/clientes/buscar", { params: { texto }, signal }),
  crear: (datos: ClienteNuevo) => api<Cliente>("/clientes", { method: "POST", body: datos }),
};
