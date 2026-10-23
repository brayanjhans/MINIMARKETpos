"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { mensajeError } from "@/lib/api";
import { ventasService } from "@/services/ventas.service";

export interface PedidoAutorizacion {
  permiso: string;
  /** Por qué se necesita (lo que respondió el servidor) */
  motivo: string;
}

interface Props {
  pedido: PedidoAutorizacion | null;
  onAutorizado: (token: string, supervisor: string) => void;
  onCerrar: () => void;
}

const ACCIONES: Record<string, string> = {
  "pos.anular_venta": "anular la venta",
  "pos.aplicar_descuento": "aplicar el descuento",
  "pos.vender_sin_stock": "vender sin stock",
  "pos.venta_credito": "vender al fiado",
};

/** El supervisor escribe su usuario y contraseña en la misma caja; queda en la auditoría quién autorizó. */
export function AutorizacionDialog({ pedido, onAutorizado, onCerrar }: Props) {
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const cerrar = () => {
    setUsuario("");
    setClave("");
    setError(null);
    onCerrar();
  };

  const autorizar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pedido || !usuario.trim() || !clave) return;
    setEnviando(true);
    setError(null);
    try {
      const r = await ventasService.autorizar(usuario.trim(), clave, pedido.permiso);
      setUsuario("");
      setClave("");
      onAutorizado(r.token, r.supervisor);
    } catch (err) {
      setError(mensajeError(err));
      setClave("");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Dialog open={!!pedido} onOpenChange={(a) => !a && cerrar()}>
      <DialogContent className="sm:max-w-sm">
        <form onSubmit={autorizar}>
          <DialogHeader>
            <span className="mb-1 grid size-11 place-items-center rounded-xl bg-navy text-amarillo dark:bg-navy-2">
              <ShieldCheck className="size-5" />
            </span>
            <DialogTitle>Autorización del supervisor</DialogTitle>
            <DialogDescription>
              {pedido?.motivo}. Para {ACCIONES[pedido?.permiso ?? ""] ?? "continuar"}, un supervisor escribe aquí su
              usuario y contraseña.
            </DialogDescription>
          </DialogHeader>
          <div className="my-4 flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sup-usuario">Usuario del supervisor</Label>
              <Input
                id="sup-usuario"
                value={usuario}
                onChange={(e) => setUsuario(e.target.value)}
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                autoFocus
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="sup-clave">Contraseña</Label>
              <Input
                id="sup-clave"
                type="password"
                value={clave}
                onChange={(e) => setClave(e.target.value)}
                autoComplete="off"
              />
            </div>
            {error && (
              <p role="alert" className="rounded-xl bg-pill-negative-bg px-3 py-2 text-sm font-semibold text-pill-negative-ink">
                {error}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={cerrar}>
              Cancelar
            </Button>
            <Button type="submit" disabled={enviando || !usuario.trim() || !clave}>
              {enviando && <Loader2 className="animate-spin" />} Autorizar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
