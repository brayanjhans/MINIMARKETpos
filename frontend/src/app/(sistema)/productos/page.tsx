import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Productos"
      fase={3}
      descripcion="El catálogo de la tienda: códigos de barras, presentaciones (six-pack, caja x24) y precios."
      tareas={[
        "Afectación de IGV por producto y bolsas con ICBPER",
        "Historial de cambios de precio",
        "Importar y exportar en Excel",
      ]}
    />
  );
}