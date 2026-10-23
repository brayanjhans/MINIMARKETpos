"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

/** Pide el motivo al rechazar un ajuste o devolver un conteo (queda en la auditoría). */
export function RechazoDialog({
  abierto,
  titulo,
  descripcion,
  boton,
  enviando,
  onCerrar,
  onConfirmar,
}: {
  abierto: boolean;
  titulo: string;
  descripcion: string;
  boton: string;
  enviando: boolean;
  onCerrar: () => void;
  onConfirmar: (motivo: string) => void;
}) {
  const [motivo, setMotivo] = useState("");
  return (
    <Dialog open={abierto} onOpenChange={(a) => !a && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (motivo.trim().length >= 3) onConfirmar(motivo.trim());
          }}
        >
          <DialogHeader>
            <DialogTitle>{titulo}</DialogTitle>
            <DialogDescription>{descripcion}</DialogDescription>
          </DialogHeader>
          <textarea
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            maxLength={300}
            rows={3}
            autoFocus
            aria-label="Motivo"
            placeholder="Motivo (mínimo 3 letras)"
            className="my-4 w-full resize-none rounded-[10px] border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCerrar}>
              Cancelar
            </Button>
            <Button type="submit" variant="destructive" disabled={motivo.trim().length < 3 || enviando}>
              {boton}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
