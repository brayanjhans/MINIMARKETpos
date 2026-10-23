import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Clientes"
      fase={5}
      descripcion="Clientes con DNI o RUC, su historial de compras y lo que deben."
      tareas={[
        "Ventas al fiado con límite de crédito",
        "Abonos que entran a la caja abierta",
      ]}
    />
  );
}