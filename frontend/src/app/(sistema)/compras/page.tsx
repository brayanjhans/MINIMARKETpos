import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Compras"
      fase={5}
      descripcion="Órdenes de compra y recepción de mercadería que suma al stock."
      tareas={[
        "Recepción parcial con lotes y vencimientos",
        "Cuentas por pagar y pagos a proveedores",
      ]}
    />
  );
}