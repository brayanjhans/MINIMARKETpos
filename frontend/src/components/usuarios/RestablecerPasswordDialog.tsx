"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { mensajeError } from "@/lib/api";
import { esquemaPassword } from "@/lib/validaciones";
import { usuariosService } from "@/services/usuarios.service";
import type { UsuarioListado } from "@/types";

interface Props {
  usuario: UsuarioListado | null;
  onCerrar: () => void;
}

export function RestablecerPasswordDialog({ usuario, onCerrar }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutacion = useMutation({
    mutationFn: () => usuariosService.restablecerPassword(usuario!.id, password),
    onSuccess: (r) => {
      toast.success(r.mensaje);
      cerrar();
    },
    onError: (e) => setError(mensajeError(e)),
  });

  const cerrar = () => {
    setPassword("");
    setError(null);
    onCerrar();
  };

  const enviar = (e: React.FormEvent) => {
    e.preventDefault();
    const validacion = esquemaPassword.safeParse(password);
    if (!validacion.success) return setError(validacion.error.issues[0]!.message);
    mutacion.mutate();
  };

  return (
    <Dialog open={!!usuario} onOpenChange={(v) => !v && cerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Asignar contraseña temporal</DialogTitle>
          <DialogDescription>
            Asigne una contraseña temporal a <strong>{usuario?.nombre_completo}</strong>. Deberá cambiarla al ingresar y
            se cerrarán sus sesiones abiertas.
          </DialogDescription>
        </DialogHeader>
        <form id="form-restablecer" onSubmit={enviar} className="space-y-1.5">
          <Label htmlFor="nueva">Contraseña temporal</Label>
          <Input id="nueva" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus autoComplete="off" />
          {error && <p className="text-xs text-destructive">{error}</p>}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={cerrar}>
            Cancelar
          </Button>
          <Button type="submit" form="form-restablecer" disabled={mutacion.isPending}>
            {mutacion.isPending && <Loader2 className="animate-spin" />}
            Asignar contraseña
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
