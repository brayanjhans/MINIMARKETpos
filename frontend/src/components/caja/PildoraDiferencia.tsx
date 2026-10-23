import { Pildora } from "@/components/comunes/Pildora";
import { soles } from "@/lib/utils";

/** Resultado del arqueo: cuadra, falta o sobra (null = turno abierto). */
export function PildoraDiferencia({ diferencia }: { diferencia: string | null }) {
  if (diferencia === null) return <Pildora>Abierta</Pildora>;
  const d = Number(diferencia);
  if (d === 0) return <Pildora tono="positivo">Cuadra</Pildora>;
  return <Pildora tono={d < 0 ? "negativo" : "aviso"}>{d < 0 ? `Falta ${soles(-d)}` : `Sobra ${soles(d)}`}</Pildora>;
}
