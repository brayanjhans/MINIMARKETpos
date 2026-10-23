"use client";

import { Menu } from "lucide-react";
import { useState } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

/** Botón ☰ que abre el menú completo en un panel (pantallas sin menú lateral fijo y el punto de venta). */
export function BotonMenu({ className }: { className?: string }) {
  const [abierto, setAbierto] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setAbierto(true)}
        aria-label="Abrir el menú"
        className={cn(
          "grid size-10 flex-none place-items-center rounded-[12px] transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
          className,
        )}
      >
        <Menu className="size-5" />
      </button>
      <Sheet open={abierto} onOpenChange={setAbierto}>
        <SheetContent side="left" className="w-72 border-0 bg-navy p-0">
          <SheetTitle className="sr-only">Menú principal</SheetTitle>
          <Sidebar movil alNavegar={() => setAbierto(false)} />
        </SheetContent>
      </Sheet>
    </>
  );
}
