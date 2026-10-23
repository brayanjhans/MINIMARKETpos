"use client";

import { CheckCircle2, Printer, ShoppingCart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { METODOS } from "@/lib/ventas";
import { soles } from "@/lib/utils";
import type { VentaDetalle } from "@/types/ventas";

interface Props {
  venta: VentaDetalle | null;
  onImprimir: () => void;
  onSiguiente: () => void;
}

/** Al cobrar: el vuelto en grande y dos caminos. Enter = siguiente venta, P = imprimir el ticket. */
export function VentaTerminada({ venta, onImprimir, onSiguiente }: Props) {
  const vuelto = Number(venta?.vuelto ?? 0);
  return (
    <Dialog open={!!venta} onOpenChange={(a) => !a && onSiguiente()}>
      <DialogContent
        className="sm:max-w-md"
        onKeyDown={(e) => {
          if (e.key.toLowerCase() === "p" || e.key === "F9") {
            e.preventDefault();
            onImprimir();
          }
        }}
      >
        {venta && (
          <>
            <DialogHeader className="items-center text-center">
              <CheckCircle2 className="size-12 text-positive" />
              <DialogTitle className="text-xl">Venta registrada</DialogTitle>
              <DialogDescription className="tabular">
                {venta.comprobante} · {venta.pagos.map((p) => METODOS[p.metodo].texto).join(" + ")} ·{" "}
                {soles(venta.a_cobrar)}
              </DialogDescription>
            </DialogHeader>
            {vuelto > 0 && (
              <div className="flex items-center justify-between rounded-2xl bg-navy px-5 py-4 text-white dark:bg-navy-2">
                <span className="text-sm font-semibold text-navy-ink">Vuelto</span>
                <span className="text-[34px] font-extrabold text-amarillo tabular">{soles(vuelto)}</span>
              </div>
            )}
            <div className="mt-2 grid grid-cols-2 gap-2">
              <Button variant="outline" className="h-14 text-[15px] font-bold" onClick={onImprimir}>
                <Printer /> Imprimir ticket
                <kbd className="ml-1 rounded bg-muted px-1.5 text-[11px]">P</kbd>
              </Button>
              <Button className="h-14 text-[15px] font-extrabold" onClick={onSiguiente} autoFocus>
                <ShoppingCart /> Siguiente venta
                <kbd className="ml-1 rounded bg-black/10 px-1.5 text-[11px]">Enter</kbd>
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
