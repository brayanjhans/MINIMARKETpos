import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Proveedores"
      fase={5}
      descripcion="Registro de proveedores con RUC y los productos que abastece cada uno."
      tareas={[
        "Último costo por proveedor",
        "Proveedor principal de cada producto",
      ]}
    />
  );
}