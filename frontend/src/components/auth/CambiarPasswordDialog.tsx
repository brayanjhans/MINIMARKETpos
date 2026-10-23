"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

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
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/authStore";

const esquema = z
  .object({
    password_actual: z.string().min(1, "Ingrese su contraseña actual"),
    password_nueva: esquemaPassword,
    confirmacion: z.string(),
  })
  .refine((d) => d.password_nueva === d.confirmacion, {
    path: ["confirmacion"],
    message: "Las contraseñas no coinciden",
  });

type Datos = z.infer<typeof esquema>;

interface Props {
  abierto: boolean;
  onCambiar: (abierto: boolean) => void;
  /** Cambio obligatorio (primer ingreso): no se puede cerrar sin completarlo */
  obligatorio?: boolean;
}

export function CambiarPasswordDialog({ abierto, onCambiar, obligatorio = false }: Props) {
  const setSesion = useAuthStore((s) => s.setSesion);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Datos>({ resolver: zodResolver(esquema) });

  const enviar = async (datos: Datos) => {
    try {
      const respuesta = await authService.cambiarPassword(datos.password_actual, datos.password_nueva);
      setSesion(respuesta);
      toast.success("Contraseña actualizada", { description: "Se cerraron sus sesiones en otros equipos." });
      reset();
      onCambiar(false);
    } catch (error) {
      setError("root", { message: mensajeError(error) });
    }
  };

  return (
    <Dialog open={abierto} onOpenChange={(v) => (!obligatorio || !v ? onCambiar(v) : undefined)}>
      <DialogContent
        className="sm:max-w-md"
        showCloseButton={!obligatorio}
        onEscapeKeyDown={(e) => obligatorio && e.preventDefault()}
        onInteractOutside={(e) => obligatorio && e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{obligatorio ? "Cree una nueva contraseña" : "Cambiar contraseña"}</DialogTitle>
          <DialogDescription>
            {obligatorio
              ? "Por seguridad, debe cambiar la contraseña temporal antes de continuar."
              : "Use al menos 8 caracteres, con letras y números."}
          </DialogDescription>
        </DialogHeader>

        <form id="form-password" onSubmit={handleSubmit(enviar)} className="space-y-4" noValidate>
          <Campo id="password_actual" etiqueta="Contraseña actual" error={errors.password_actual?.message}>
            <Input id="password_actual" type="password" autoComplete="current-password" autoFocus {...register("password_actual")} />
          </Campo>
          <Campo id="password_nueva" etiqueta="Nueva contraseña" error={errors.password_nueva?.message}>
            <Input id="password_nueva" type="password" autoComplete="new-password" {...register("password_nueva")} />
          </Campo>
          <Campo id="confirmacion" etiqueta="Repita la nueva contraseña" error={errors.confirmacion?.message}>
            <Input id="confirmacion" type="password" autoComplete="new-password" {...register("confirmacion")} />
          </Campo>
          {errors.root && (
            <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {errors.root.message}
            </p>
          )}
        </form>

        <DialogFooter>
          {!obligatorio && (
            <Button variant="outline" onClick={() => onCambiar(false)} disabled={isSubmitting}>
              Cancelar
            </Button>
          )}
          <Button type="submit" form="form-password" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="animate-spin" />}
            Guardar contraseña
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Campo({
  id,
  etiqueta,
  error,
  children,
}: {
  id: string;
  etiqueta: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{etiqueta}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
