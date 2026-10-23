// Cálculo de la venta en el navegador: es EXACTAMENTE el mismo que hace el servidor (app/services/ventas.py).
// Se trabaja con enteros (céntimos y milésimas) para no arrastrar errores de coma flotante; el servidor
// rechaza la venta si su total no coincide con el que vio el cliente.

import type { Afectacion, MetodoPago } from "@/types/ventas";

/** "12.5" -> 1250 (con `decimales` = 2). Acepta coma o punto. */
export function aEntero(valor: string | number, decimales: number): number {
  const texto = String(valor).trim().replace(",", ".");
  const negativo = texto.startsWith("-");
  const [ent = "0", frac = ""] = texto.replace("-", "").split(".");
  const n = Number(ent || "0") * 10 ** decimales + Number((frac + "0".repeat(decimales)).slice(0, decimales) || "0");
  return negativo ? -n : n;
}

/** a / b redondeado al entero más cercano (mitades hacia arriba), para a >= 0 y b > 0. */
function dividir(a: number, b: number): number {
  return Math.floor((2 * a + b) / (2 * b));
}

export const aCentimos = (valor: string | number) => aEntero(valor, 2);
const aMilesimas = (valor: string | number) => aEntero(valor, 3);

/** 1250 -> "12.50" */
export function desdeCentimos(c: number): string {
  const signo = c < 0 ? "-" : "";
  const abs = Math.abs(c);
  return `${signo}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}`;
}

export interface LineaPos {
  cantidad: string;
  precio: string;
  descuento: string;
  afectacion: Afectacion;
  /** Unidades afectas al ICBPER (bolsas): cantidad × factor si el producto es una bolsa */
  bolsas: string;
}

export interface LineaCalculada {
  bruto: number;
  descuentoTotal: number;
  base: number;
  igv: number;
  icbper: number;
  total: number;
}

export interface Totales {
  lineas: LineaCalculada[];
  bruto: number;
  descuento: number;
  gravadas: number;
  exoneradas: number;
  inafectas: number;
  igv: number;
  icbper: number;
  total: number;
  /** Mensaje si los descuentos no son válidos */
  error: string | null;
}

export function calcular(
  lineas: LineaPos[],
  descuentoGlobal: string,
  igvPorcentaje: string,
  icbperMonto: string,
  preciosIncluyenIgv = true,
): Totales {
  const tasa = aCentimos(igvPorcentaje); // 18.00 -> 1800 (centésimas de punto porcentual)
  const icbper = aCentimos(icbperMonto);
  const global = aCentimos(descuentoGlobal || "0");
  let error: string | null = null;

  const brutos = lineas.map((l) => dividir(aMilesimas(l.cantidad) * aCentimos(l.precio), 1000));
  const netos = lineas.map((l, i) => {
    const descuento = aCentimos(l.descuento || "0");
    if (descuento > brutos[i]!) error = "El descuento de una línea no puede ser mayor que su importe";
    return brutos[i]! - descuento;
  });
  const sumaNetos = netos.reduce((a, b) => a + b, 0);
  if (global > sumaNetos) error = "El descuento no puede ser mayor que el total";

  const partes = lineas.map(() => 0);
  if (global > 0 && sumaNetos > 0 && !error) {
    netos.forEach((neto, i) => (partes[i] = dividir(global * neto, sumaNetos)));
    let mayor = 0;
    netos.forEach((neto, i) => {
      if (neto > netos[mayor]!) mayor = i;
    });
    partes[mayor]! += global - partes.reduce((a, b) => a + b, 0);
  }

  const t: Totales = {
    lineas: [],
    bruto: brutos.reduce((a, b) => a + b, 0),
    descuento: 0,
    gravadas: 0,
    exoneradas: 0,
    inafectas: 0,
    igv: 0,
    icbper: 0,
    total: 0,
    error,
  };
  lineas.forEach((l, i) => {
    const importe = Math.max(netos[i]! - partes[i]!, 0);
    let base = importe;
    let igv = 0;
    if (l.afectacion === "GRAVADO") {
      if (preciosIncluyenIgv) {
        base = dividir(importe * 10000, 10000 + tasa);
        igv = importe - base;
      } else {
        igv = dividir(importe * tasa, 10000);
      }
      t.gravadas += base;
    } else if (l.afectacion === "EXONERADO") {
      t.exoneradas += importe;
    } else {
      t.inafectas += importe;
    }
    const bolsa = dividir(aMilesimas(l.bolsas || "0") * icbper, 1000);
    const descuentoTotal = aCentimos(l.descuento || "0") + partes[i]!;
    const total = base + igv + bolsa;
    t.lineas.push({ bruto: brutos[i]!, descuentoTotal, base, igv, icbper: bolsa, total });
    t.igv += igv;
    t.icbper += bolsa;
    t.descuento += descuentoTotal;
    t.total += total;
  });
  return t;
}

/** Monto a cobrar: solo en efectivo y con redondeo configurado, se redondea hacia abajo (a favor del cliente). */
export function aCobrar(total: number, redondeo: string, soloEfectivo: boolean): number {
  const paso = aCentimos(redondeo || "0");
  if (paso <= 0 || !soloEfectivo) return total;
  return Math.floor(total / paso) * paso;
}

export const METODOS: Record<MetodoPago, { texto: string; color: string; corto: string }> = {
  EFECTIVO: { texto: "Efectivo", color: "text-foreground", corto: "Efectivo" },
  YAPE: { texto: "Yape", color: "text-p-lila-t", corto: "Yape" },
  PLIN: { texto: "Plin", color: "text-p-agua-t", corto: "Plin" },
  TARJETA: { texto: "Tarjeta", color: "text-p-azul-t", corto: "Tarjeta" },
  TRANSFERENCIA: { texto: "Transferencia", color: "text-p-verde-t", corto: "Transf." },
  CREDITO: { texto: "Fiado", color: "text-p-coral-t", corto: "Fiado" },
};

/** Billetes y monedas sugeridos para el pago en efectivo: el total exacto y los billetes que lo cubren. */
export function sugerenciasEfectivo(centimos: number): number[] {
  const billetes = [1000, 2000, 5000, 10000, 20000];
  const opciones = new Set<number>([centimos]);
  for (const redondo of [100, 500, 1000]) opciones.add(Math.ceil(centimos / redondo) * redondo);
  for (const b of billetes) if (b > centimos) opciones.add(b);
  return [...opciones].filter((c) => c >= centimos).sort((a, b) => a - b).slice(0, 5);
}
