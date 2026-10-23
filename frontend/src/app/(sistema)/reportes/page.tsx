import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Reportes"
      fase={6}
      descripcion="Ventas, ganancias y movimiento de productos, en PDF y Excel."
      tareas={[
        "Ventas por día, cajero, método de pago y categoría",
        "Productos más vendidos y sin movimiento",
        "Ganancia: venta menos costo, y mermas",
      ]}
    />
  );
}