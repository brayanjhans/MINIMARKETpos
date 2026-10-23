import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Inventario"
      fase={3}
      descripcion="Stock en tiempo real por almacén y sucursal."
      tareas={[
        "Lotes con fecha de vencimiento y alerta de productos por vencer",
        "Kardex de entradas, salidas y ajustes",
        "Mermas, transferencias entre almacenes e inventario físico",
      ]}
    />
  );
}