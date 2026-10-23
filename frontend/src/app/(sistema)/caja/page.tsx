import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Caja"
      fase={4}
      descripcion="Apertura con monto inicial, ingresos y egresos durante el turno, y cierre con arqueo."
      tareas={[
        "Arqueo billete por billete y moneda por moneda",
        "Esperado contra contado, por método de pago",
        "Historial de turnos por cajero",
      ]}
    />
  );
}