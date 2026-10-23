"use client";

import { TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

/** Si una pantalla del sistema falla al mostrarse, se ve este aviso y el menú sigue funcionando. */
export default function ErrorPantalla({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <section className="tarjeta mx-auto mt-6 max-w-lg p-8 text-center">
      <span className="mx-auto grid size-12 place-items-center rounded-[14px] bg-pill-negative-bg">
        <TriangleAlert className="size-6 text-pill-negative-ink" aria-hidden />
      </span>
      <h1 className="mt-4 text-[22px] font-extrabold">Esta pantalla tuvo un problema</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        No se perdió ningún dato. Intenta cargarla de nuevo; si se repite, avisa al administrador
        {error.digest && (
          <>
            {" "}
            con el código <span className="font-bold text-foreground tabular">{error.digest}</span>
          </>
        )}
        .
      </p>
      <div className="mt-6 flex justify-center gap-2">
        <Button onClick={reset}>Intentar de nuevo</Button>
        <Button variant="outline" asChild>
          <Link href="/dashboard">Ir al inicio</Link>
        </Button>
      </div>
    </section>
  );
}
