"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { mensajeError } from "@/lib/api";
import { esquemaPassword, esquemaUsername } from "@/lib/validaciones";
import { rolesService } from "@/services/roles.service";
import { sucursalesService } from "@/services/sucursales.service";
import { usuariosService } from "@/services/usuarios.service";
import type { UsuarioListado } from "@/types";

const base = {
  nombre_completo: z.string().trim().min(3, "Mínimo 3 caracteres").max(150),
  email: z.union([z.literal(""), z.email("Correo no válido")]),
  rol_id: z.string().min(1, "Seleccione un rol"),
  sucursal_ids: z.array(z.number()).min(1, "Asigne al menos una sucursal"),
  sucursal_predeterminada_id: z.string().optional(),
};
const esquemaCrear = z.object({
  ...base,
  username: esquemaUsername,
  password: esquemaPassword,
  debe_cambiar_password: z.boolean(),
});
const esquemaEditar = z.object({
  ...base,
  username: z.string(),
  password: z.string().optional(),
  debe_cambiar_password: z.boolean(),
});
type Datos = z.infer<typeof esquemaCrear>;

interface Props {
  abierto: boolean;
  onCambiar: (abierto: boolean) => void;
  /** Si se indica, el diálogo edita este usuario; si no, crea uno nuevo */
  usuario?: UsuarioListado | null;
}

export function UsuarioFormDialog({ abierto, onCambiar, usuario }: Props) {
  const editando = !!usuario;
  const queryClient = useQueryClient();
  const roles = useQuery({ queryKey: ["roles"], queryFn: rolesService.listar, enabled: abierto });
  const sucursales = useQuery({ queryKey: ["sucursales"], queryFn: sucursalesService.listar, enabled: abierto });
  const detalle = useQuery({
    queryKey: ["usuarios", usuario?.id],
    queryFn: () => usuariosService.obtener(usuario!.id),
    enabled: abierto && editando,
  });

  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<Datos>({
    resolver: zodResolver((editando ? esquemaEditar : esquemaCrear) as typeof esquemaCrear),
  });

  // Carga los valores al abrir (vacíos para crear, del usuario para editar)
  useEffect(() => {
    if (!abierto) return;
    const d = detalle.data;
    reset({
      nombre_completo: d?.nombre_completo ?? "",
      username: d?.username ?? "",
      email: d?.email ?? "",
      password: "",
      rol_id: d ? String(d.rol.id) : "",
      sucursal_ids: d ? d.sucursales.map((s) => s.id) : sucursales.data?.length === 1 ? [sucursales.data[0]!.id] : [],
      sucursal_predeterminada_id: d?.sucursal_predeterminada_id ? String(d.sucursal_predeterminada_id) : undefined,
      debe_cambiar_password: true,
    });
  }, [abierto, detalle.data, sucursales.data, reset]);

  const seleccionadas = useWatch({ control, name: "sucursal_ids" }) ?? [];

  const guardar = useMutation({
    mutationFn: async (datos: Datos) => {
      const comunes = {
        nombre_completo: datos.nombre_completo,
        email: datos.email || null,
        rol_id: Number(datos.rol_id),
        sucursal_ids: datos.sucursal_ids,
        sucursal_predeterminada_id: datos.sucursal_predeterminada_id
          ? Number(datos.sucursal_predeterminada_id)
          : (datos.sucursal_ids[0] ?? null),
      };
      return editando
        ? usuariosService.actualizar(usuario!.id, comunes)
        : usuariosService.crear({
            ...comunes,
            username: datos.username,
            password: datos.password,
            debe_cambiar_password: datos.debe_cambiar_password,
          });
    },
    onSuccess: (u) => {
      toast.success(editando ? "Usuario actualizado" : `Usuario «${u.username}» creado`);
      void queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      onCambiar(false);
    },
    onError: (error) => setError("root", { message: mensajeError(error) }),
  });

  const cargando = (editando && detalle.isLoading) || roles.isLoading || sucursales.isLoading;

  return (
    <Dialog open={abierto} onOpenChange={onCambiar}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{editando ? "Editar usuario" : "Nuevo usuario"}</DialogTitle>
          <DialogDescription>
            {editando
              ? `Modifique los datos de @${usuario!.username}.`
              : "El usuario deberá cambiar la contraseña temporal en su primer ingreso."}
          </DialogDescription>
        </DialogHeader>

        {cargando ? (
          <div className="grid h-64 place-items-center">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <form
            id="form-usuario"
            onSubmit={handleSubmit((d) => guardar.mutate(d))}
            className="scrollbar-fino -mx-1 max-h-[65vh] space-y-4 overflow-y-auto px-1"
            noValidate
          >
            <Campo etiqueta="Nombre completo" error={errors.nombre_completo?.message} htmlFor="nombre_completo">
              <Input id="nombre_completo" autoFocus {...register("nombre_completo")} />
            </Campo>

            <div className="grid gap-4 sm:grid-cols-2">
              <Campo etiqueta="Usuario" error={errors.username?.message} htmlFor="username">
                <Input
                  id="username"
                  autoCapitalize="none"
                  spellCheck={false}
                  disabled={editando}
                  {...register("username")}
                />
              </Campo>
              <Campo etiqueta="Correo (opcional)" error={errors.email?.message} htmlFor="email">
                <Input id="email" type="email" {...register("email")} />
              </Campo>
            </div>

            {!editando && (
              <Campo etiqueta="Contraseña temporal" error={errors.password?.message} htmlFor="password">
                <Input id="password" type="text" autoComplete="new-password" {...register("password")} />
              </Campo>
            )}

            <Campo etiqueta="Rol" error={errors.rol_id?.message}>
              <Controller
                control={control}
                name="rol_id"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full" aria-invalid={!!errors.rol_id}>
                      <SelectValue placeholder="Seleccione un rol" />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.data
                        ?.filter((r) => r.activo)
                        .map((r) => (
                          <SelectItem key={r.id} value={String(r.id)}>
                            {r.nombre}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </Campo>

            <Campo etiqueta="Sucursales donde trabaja" error={errors.sucursal_ids?.message}>
              <Controller
                control={control}
                name="sucursal_ids"
                render={({ field }) => (
                  <div className="grid gap-2 rounded-lg border p-3 sm:grid-cols-2">
                    {sucursales.data?.map((s) => {
                      const marcada = field.value?.includes(s.id) ?? false;
                      return (
                        <label key={s.id} className="flex cursor-pointer items-center gap-2 text-sm">
                          <Checkbox
                            checked={marcada}
                            onCheckedChange={(v) =>
                              field.onChange(
                                v ? [...(field.value ?? []), s.id] : (field.value ?? []).filter((x) => x !== s.id),
                              )
                            }
                          />
                          {s.nombre}
                        </label>
                      );
                    })}
                  </div>
                )}
              />
            </Campo>

            {seleccionadas.length > 1 && (
              <Campo etiqueta="Sucursal al iniciar sesión">
                <Controller
                  control={control}
                  name="sucursal_predeterminada_id"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="La primera asignada" />
                      </SelectTrigger>
                      <SelectContent>
                        {sucursales.data
                          ?.filter((s) => seleccionadas.includes(s.id))
                          .map((s) => (
                            <SelectItem key={s.id} value={String(s.id)}>
                              {s.nombre}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </Campo>
            )}

            {!editando && (
              <Controller
                control={control}
                name="debe_cambiar_password"
                render={({ field }) => (
                  <label className="flex items-center justify-between gap-4 rounded-lg border p-3">
                    <span className="text-sm">
                      <span className="font-medium">Exigir cambio de contraseña</span>
                      <span className="block text-xs text-muted-foreground">En su primer inicio de sesión</span>
                    </span>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </label>
                )}
              />
            )}

            {errors.root && (
              <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {errors.root.message}
              </p>
            )}
          </form>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onCambiar(false)} disabled={guardar.isPending}>
            Cancelar
          </Button>
          <Button type="submit" form="form-usuario" disabled={guardar.isPending || cargando}>
            {guardar.isPending && <Loader2 className="animate-spin" />}
            {editando ? "Guardar cambios" : "Crear usuario"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Campo({
  etiqueta,
  error,
  htmlFor,
  children,
}: {
  etiqueta: string;
  error?: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{etiqueta}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
