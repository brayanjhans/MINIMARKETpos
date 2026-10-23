import { Proximamente } from "@/components/comunes/Proximamente";

export default function Pagina() {
  return (
    <Proximamente
      titulo="Categorías"
      fase={3}
      descripcion="Organización del catálogo por categoría y marca."
      tareas={[
        "Categorías con color para reconocerlas en el POS",
        "Marcas para filtrar y para los reportes",
      ]}
    />
  );
}