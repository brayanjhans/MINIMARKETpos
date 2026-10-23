import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Punto de venta"
      fase={4}
      descripcion="Venta con lector de código de barras y solo teclado: F2 para buscar, F4 para cobrar."
      tareas={[
        "Cobro en efectivo con cálculo del vuelto, tarjeta, Yape, Plin, pago mixto y fiado",
        "Ticket en impresora térmica de 80 mm",
        "Anulaciones y devoluciones solo con permiso",
      ]}
    />
  );
}