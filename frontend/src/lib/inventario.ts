import type { EstadoDocumento, EstadoFisico, EstadoTransferencia, TipoMovimiento } from "@/types/inventario";
import { UNIDADES, type UnidadMedida } from "@/types/productos";

/** Cantidad legible: "12.000" -> "12", "1.250" -> "1.25". */
export function cantidad(valor: string | number | null | undefined): string {
  const n = Number(valor ?? 0);
  return n.toLocaleString("es-PE", { maximumFractionDigits: 3 });
}

export function unidadCorta(unidad: UnidadMedida): string {
  return UNIDADES.find((u) => u.valor === unidad)?.corta ?? "und";
}

/** Texto de un tipo de movimiento del kardex y si suma o resta. */
export const TIPOS_MOVIMIENTO: Record<TipoMovimiento, string> = {
  STOCK_INICIAL: "Stock inicial",
  ENTRADA_COMPRA: "Compra",
  ANULACION_COMPRA: "Anulación de compra",
  SALIDA_VENTA: "Venta",
  ANULACION_VENTA: "Venta anulada",
  DEVOLUCION_VENTA: "Devolución",
  AJUSTE_ENTRADA: "Ajuste (entrada)",
  AJUSTE_SALIDA: "Ajuste o merma",
  INVENTARIO_FISICO: "Inventario físico",
  TRANSFERENCIA_SALIDA: "Transferencia enviada",
  TRANSFERENCIA_ENTRADA: "Transferencia recibida",
  TRANSFERENCIA_ANULADA: "Transferencia anulada",
};

type Tono = "positivo" | "negativo" | "aviso" | "neutro";

export const ESTADOS_AJUSTE: Record<EstadoDocumento, { texto: string; tono: Tono }> = {
  BORRADOR: { texto: "Borrador", tono: "neutro" },
  PENDIENTE_APROBACION: { texto: "Por aprobar", tono: "aviso" },
  APLICADO: { texto: "Aplicado", tono: "positivo" },
  RECHAZADO: { texto: "Rechazado", tono: "negativo" },
  ANULADO: { texto: "Anulado", tono: "neutro" },
};

export const ESTADOS_TRANSFERENCIA: Record<EstadoTransferencia, { texto: string; tono: Tono }> = {
  PENDIENTE: { texto: "Preparada", tono: "neutro" },
  EN_TRANSITO: { texto: "En camino", tono: "aviso" },
  RECIBIDA: { texto: "Recibida", tono: "positivo" },
  ANULADA: { texto: "Anulada", tono: "neutro" },
};

export const ESTADOS_FISICO: Record<EstadoFisico, { texto: string; tono: Tono }> = {
  EN_PROCESO: { texto: "En proceso", tono: "aviso" },
  PENDIENTE_APROBACION: { texto: "Por aprobar", tono: "aviso" },
  APLICADO: { texto: "Aplicado", tono: "positivo" },
  CANCELADO: { texto: "Cancelado", tono: "neutro" },
};

/** Días que faltan para vencer, en palabras. */
export function vence(dias: number | null): string {
  if (dias === null) return "Sin fecha";
  if (dias < 0) return `Venció hace ${-dias} día${dias === -1 ? "" : "s"}`;
  if (dias === 0) return "Vence hoy";
  return `${dias} día${dias === 1 ? "" : "s"}`;
}

/** Valida una cantidad escrita: número >= 0 con 3 decimales como máximo (enteros si no admite decimales). */
export function cantidadValida(texto: string, decimales: boolean): boolean {
  const patron = decimales ? /^\d{1,6}([.,]\d{1,3})?$/ : /^\d{1,6}$/;
  return patron.test(texto.trim());
}

export const normalizarNumero = (texto: string) => texto.trim().replace(",", ".");
