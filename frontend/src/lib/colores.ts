/** Parejas pastel del estilo Bodega (fondo + tinta) para roles, personas, categorías y eventos. */
export const PASTELES = {
  amarillo: "bg-p-amarillo text-p-amarillo-t",
  azul: "bg-p-azul text-p-azul-t",
  coral: "bg-p-coral text-p-coral-t",
  agua: "bg-p-agua text-p-agua-t",
  lila: "bg-p-lila text-p-lila-t",
  naranja: "bg-p-naranja text-p-naranja-t",
  verde: "bg-p-verde text-p-verde-t",
} as const;

export type Pastel = keyof typeof PASTELES;

const ORDEN: Pastel[] = ["amarillo", "azul", "coral", "agua", "lila", "naranja"];

/** Color estable para cualquier id (personas, categorías…). */
export function pastelPorId(id: number): string {
  return PASTELES[ORDEN[Math.abs(id) % ORDEN.length]!];
}

/** Colores fijos para los roles del sistema; los roles propios toman uno estable por id. */
export function colorRol(nombre: string, id: number): string {
  if (nombre === "Administrador") return "bg-navy text-amarillo dark:bg-navy-2";
  if (nombre === "Cajero") return PASTELES.amarillo;
  if (nombre === "Almacenero") return PASTELES.azul;
  return pastelPorId(id + 2);
}
