import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Configuración"
      fase={6}
      descripcion="Datos de la empresa y del funcionamiento de cada sucursal."
      tareas={[
        "RUC, logo, dirección e IGV",
        "Sucursales, almacenes, cajas, series e impresoras",
        "Parámetros: venta sin stock, redondeo, descuento máximo",
      ]}
    />
  );
}