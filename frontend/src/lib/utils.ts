import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const formatoSoles = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
});

/** Formatea un monto en soles: 1234.5 -> "S/ 1,234.50" */
export function soles(valor: number | string | null | undefined): string {
  return formatoSoles.format(Number(valor ?? 0));
}

const formatoFechaHora = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "America/Lima",
});

const formatoFecha = new Intl.DateTimeFormat("es-PE", { dateStyle: "medium", timeZone: "America/Lima" });
// Una fecha sola ("2026-10-25", p. ej. un vencimiento) se lee como medianoche UTC: en Lima sería el día anterior
const formatoFechaSola = new Intl.DateTimeFormat("es-PE", { dateStyle: "medium", timeZone: "UTC" });
const SOLO_FECHA = /^\d{4}-\d{2}-\d{2}$/;

export function fechaHora(valor: string | Date | null | undefined): string {
  return valor ? formatoFechaHora.format(new Date(valor)) : "—";
}

export function fecha(valor: string | Date | null | undefined): string {
  if (!valor) return "—";
  if (typeof valor === "string" && SOLO_FECHA.test(valor)) return formatoFechaSola.format(new Date(valor));
  return formatoFecha.format(new Date(valor));
}

/** Fecha y hora por separado, para apilarlas en una celda: { fecha: "2026-10-22", hora: "17:43" } */
export function fechaYHora(valor: string): { fecha: string; hora: string } {
  const partes = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Lima",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(valor));
  const p = (t: string) => partes.find((x) => x.type === t)?.value ?? "";
  return { fecha: `${p("year")}-${p("month")}-${p("day")}`, hora: `${p("hour")}:${p("minute")}` };
}

/** Recencia en palabras: "Hoy, 17:43", "Ayer, 09:10", "hace 6 días", o la fecha ISO. */
export function recencia(valor: string | null | undefined): string {
  if (!valor) return "Nunca";
  const { fecha, hora } = fechaYHora(valor);
  const hoy = fechaYHora(new Date().toISOString()).fecha;
  const dias = Math.round((Date.parse(hoy) - Date.parse(fecha)) / 86_400_000);
  if (dias === 0) return `Hoy, ${hora}`;
  if (dias === 1) return `Ayer, ${hora}`;
  if (dias < 7) return `hace ${dias} días`;
  return fecha;
}

/** Tinte pálido y estable por persona (separados por el ángulo áureo: vecinos a más de 60°). */
export function tintePersona(id: number): { fondo: string; tinta: string } {
  const tono = Math.round((id * 137.508) % 360);
  return { fondo: `oklch(0.94 0.035 ${tono})`, tinta: `oklch(0.38 0.08 ${tono})` };
}

export function iniciales(nombre: string): string {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}
