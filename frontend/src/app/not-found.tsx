import { SearchX } from "lucide-react";
import Link from "next/link";

import { PantallaAviso } from "@/components/comunes/PantallaAviso";
import { Button } from "@/components/ui/button";

export default function NoEncontrada() {
  return (
    <PantallaAviso
      codigo="404"
      icono={SearchX}
      titulo="Esta página no existe"
      mensaje="Puede que el enlace esté mal escrito o que la página se haya movido."
      acciones={
        <Button asChild>
          <Link href="/dashboard">Volver al inicio</Link>
        </Button>
      }
    />
  );
}
