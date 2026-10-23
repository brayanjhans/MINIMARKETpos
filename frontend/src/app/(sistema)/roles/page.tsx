"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Lock, Plus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { PageHeader } from "@/components/comunes/PageHeader";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";
import { colorRol } from "@/lib/colores";
import { cn } from "@/lib/utils";
import { rolesService } from "@/services/roles.service";

const ROL_ADMIN = "Administrador";

/** Barra de progreso del color del rol */
const BARRA: Record<string, string> = { Administrador: "bg-navy dark:bg-secondary", Cajero: "bg-amarillo", Almacenero: "bg-p-azul-t" };

export default function RolesPage() {
  return (
    <RequierePermiso permiso="roles.ver">
      <Roles />
    </RequierePermiso>
  );
}

function Roles() {
  const { tiene } = useAuth();
  const puedeGestionar = tiene("roles.gestionar");
  const queryClient = useQueryClient();
  const [seleccionado, setSeleccionado] = useState<number | null>(null);
  const [nuevoAbierto, setNuevoAbierto] = useState(false);
  const [confirmarEliminar, setConfirmarEliminar] = useState(false);

  const roles = useQuery({ queryKey: ["roles"], queryFn: rolesService.listar });
  const catalogo = useQuery({
    queryKey: ["roles", "catalogo"],
    queryFn: rolesService.catalogoPermisos,
    staleTime: Infinity,
  });
  const rolId = seleccionado ?? roles.data?.[0]?.id ?? null;
  const detalle = useQuery({
    queryKey: ["roles", rolId],
    queryFn: () => rolesService.obtener(rolId!),
    enabled: rolId !== null,
  });

  const [marcados, setMarcados] = useState<Set<string>>(new Set());
  useEffect(() => setMarcados(new Set(detalle.data?.permisos ?? [])), [detalle.data]);

  const original = useMemo(() => new Set(detalle.data?.permisos ?? []), [detalle.data]);
  const cambios =
    [...marcados].filter((p) => !original.has(p)).length + [...original].filter((p) => !marcados.has(p)).length;
  const esAdmin = detalle.data?.nombre === ROL_ADMIN;
  const editable = puedeGestionar && !esAdmin;
  const totalPermisos = catalogo.data?.reduce((n, m) => n + m.permisos.length, 0) ?? 0;

  const invalidar = () => queryClient.invalidateQueries({ queryKey: ["roles"] });

  const guardar = useMutation({
    mutationFn: () => rolesService.actualizar(rolId!, { permisos: [...marcados] }),
    onSuccess: (rol) => {
      toast.success(`Permisos de ${rol.nombre} guardados`, {
        description: "Aplican desde la siguiente acción de cada persona con este rol.",
      });
      void invalidar();
    },
    onError: (e) => toast.error(mensajeError(e)),
  });

  const eliminar = useMutation({
    mutationFn: () => rolesService.eliminar(rolId!),
    onSuccess: () => {
      toast.success(`Rol ${detalle.data?.nombre} eliminado`);
      setSeleccionado(null);
      void invalidar();
    },
    onError: (e) => toast.error(mensajeError(e)),
    onSettled: () => setConfirmarEliminar(false),
  });

  const fijar = (codigos: string[], valor: boolean) =>
    setMarcados((prev) => {
      const s = new Set(prev);
      codigos.forEach((c) => (valor ? s.add(c) : s.delete(c)));
      return s;
    });

  return (
    <>
      <PageHeader
        titulo="Roles y permisos"
        linea="Define qué puede hacer cada tipo de trabajador"
        acciones={
          puedeGestionar && (
            <Button variant="outline" onClick={() => setNuevoAbierto(true)}>
              <Plus strokeWidth={2.6} /> Nuevo rol
            </Button>
          )
        }
      />

      <div className="grid items-start gap-[18px] lg:grid-cols-[280px_minmax(0,1fr)]">
        {/* Roles */}
        <nav aria-label="Roles" className="flex flex-col gap-3">
          {roles.isLoading
            ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-[104px] rounded-[16px]" />)
            : roles.data?.map((r) => {
                const activo = r.id === rolId;
                const porcentaje = totalPermisos ? Math.round((r.total_permisos / totalPermisos) * 100) : 0;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setSeleccionado(r.id)}
                    aria-current={activo ? "true" : undefined}
                    className={cn(
                      "flex flex-col gap-2.5 rounded-[16px] border-2 bg-card p-4 text-left transition-colors",
                      "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                      activo ? "border-amarillo bg-aviso-fondo" : "border-transparent hover:border-border",
                    )}
                  >
                    <span className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "grid size-9 place-items-center rounded-[11px] font-extrabold",
                          colorRol(r.nombre, r.id),
                        )}
                      >
                        {r.nombre[0]}
                      </span>
                      <span>
                        <span className="block font-bold">{r.nombre}</span>
                        <span className="block text-xs text-muted-foreground tabular">
                          {r.total_usuarios} {r.total_usuarios === 1 ? "persona" : "personas"}
                        </span>
                      </span>
                    </span>
                    <span className="h-1.5 rounded-full bg-muted">
                      <span
                        className={cn("block h-1.5 rounded-full", BARRA[r.nombre] ?? "bg-p-lila-t")}
                        style={{ width: `${porcentaje}%` }}
                      />
                    </span>
                    <span className="text-xs text-muted-foreground tabular">
                      {r.total_permisos} de {totalPermisos || "—"} permisos
                    </span>
                  </button>
                );
              })}
        </nav>

        {/* Permisos del rol */}
        <section className="tarjeta p-5" aria-labelledby="titulo-rol">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 id="titulo-rol" className="text-[19px] font-extrabold">
                {detalle.data?.nombre ?? " "}
              </h2>
              <p className="text-[13px] text-muted-foreground">
                {esAdmin ? (
                  <span className="inline-flex items-center gap-1.5">
                    <Lock className="size-3.5" /> Tiene todos los permisos siempre. No se puede modificar.
                  </span>
                ) : (
                  (detalle.data?.descripcion ?? "Sin descripción")
                )}
              </p>
            </div>
            {editable && (
              <div className="flex items-center gap-2 sm:ml-auto">
                {cambios > 0 && (
                  <span className="rounded-[10px] bg-amarillo-suave px-3 py-1.5 text-[13px] font-bold text-amarillo-tinta">
                    {cambios} {cambios === 1 ? "cambio sin guardar" : "cambios sin guardar"}
                  </span>
                )}
                {!detalle.data?.es_sistema && (
                  <Button variant="ghost" className="text-destructive hover:text-destructive" onClick={() => setConfirmarEliminar(true)}>
                    Eliminar
                  </Button>
                )}
                <Button variant="navy" onClick={() => guardar.mutate()} disabled={cambios === 0 || guardar.isPending}>
                  {guardar.isPending && <Loader2 className="animate-spin" />}
                  Guardar
                </Button>
              </div>
            )}
          </div>

          {detalle.isLoading || catalogo.isLoading ? (
            <div className="grid gap-3 md:grid-cols-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-40 rounded-[14px]" />
              ))}
            </div>
          ) : (
            <div className="grid items-start gap-3 md:grid-cols-2">
              {catalogo.data?.map((modulo) => {
                const codigos = modulo.permisos.map((p) => p.codigo);
                const cuantos = codigos.filter((c) => marcados.has(c)).length;
                const todos = cuantos === codigos.length;
                return (
                  <div key={modulo.modulo} className="rounded-[14px] bg-muted px-4 py-3.5">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="text-sm font-extrabold">{modulo.etiqueta}</span>
                      <span className="flex items-center gap-2 text-[13px] font-semibold text-muted-foreground tabular">
                        {cuantos} de {codigos.length}
                        {editable && (
                          <button
                            type="button"
                            onClick={() => fijar(codigos, !todos)}
                            className="rounded px-1 text-xs font-bold text-foreground hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                          >
                            {todos ? "Ninguno" : "Todos"}
                          </button>
                        )}
                      </span>
                    </div>
                    <ul>
                      {modulo.permisos.map((p) => {
                        const marcado = marcados.has(p.codigo);
                        const cambiado = marcado !== original.has(p.codigo);
                        return (
                          <li key={p.codigo}>
                            <label
                              className={cn(
                                "flex items-center justify-between gap-3 py-[7px] text-[13.5px]",
                                editable ? "cursor-pointer" : "cursor-default",
                                !marcado && "text-muted-foreground",
                              )}
                            >
                              <span>
                                {p.descripcion}
                                {cambiado && (
                                  <span className="ml-1.5 text-xs font-bold text-amarillo-tinta">
                                    {marcado ? "nuevo" : "se quita"}
                                  </span>
                                )}
                              </span>
                              <Switch
                                checked={marcado}
                                onCheckedChange={(v) => fijar([p.codigo], v)}
                                disabled={!editable}
                                className={cn(cambiado && "ring-2 ring-navy ring-offset-2 ring-offset-muted dark:ring-secondary")}
                              />
                            </label>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>

      <NuevoRolDialog
        abierto={nuevoAbierto}
        onCambiar={setNuevoAbierto}
        onCreado={(id) => {
          setSeleccionado(id);
          void invalidar();
        }}
      />

      <AlertDialog open={confirmarEliminar} onOpenChange={setConfirmarEliminar}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar el rol {detalle.data?.nombre}</AlertDialogTitle>
            <AlertDialogDescription>
              Se borra el rol y sus permisos. Solo se puede si nadie lo tiene asignado. No se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Conservar</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                eliminar.mutate();
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {eliminar.isPending && <Loader2 className="animate-spin" />}
              Eliminar rol
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function NuevoRolDialog({
  abierto,
  onCambiar,
  onCreado,
}: {
  abierto: boolean;
  onCambiar: (v: boolean) => void;
  onCreado: (id: number) => void;
}) {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState<string | null>(null);

  const crear = useMutation({
    mutationFn: () =>
      rolesService.crear({ nombre: nombre.trim(), descripcion: descripcion.trim() || null, permisos: [] }),
    onSuccess: (rol) => {
      toast.success(`Rol ${rol.nombre} creado`, { description: "Ahora activa lo que puede hacer." });
      onCreado(rol.id);
      cerrar();
    },
    onError: (e) => setError(mensajeError(e)),
  });

  const cerrar = () => {
    setNombre("");
    setDescripcion("");
    setError(null);
    onCambiar(false);
  };

  return (
    <Dialog open={abierto} onOpenChange={(v) => (v ? onCambiar(true) : cerrar())}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuevo rol</DialogTitle>
          <DialogDescription>Por ejemplo: Supervisor de turno, Cajero de fin de semana.</DialogDescription>
        </DialogHeader>
        <form
          id="form-rol"
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (nombre.trim().length < 3) return setError("El nombre debe tener al menos 3 caracteres");
            crear.mutate();
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="nombre-rol">Nombre</Label>
            <Input id="nombre-rol" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={50} autoFocus />
          </div>
          <div className="space-y-2">
            <Label htmlFor="desc-rol">Para qué sirve (opcional)</Label>
            <Input id="desc-rol" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} maxLength={200} />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={cerrar}>
            Cancelar
          </Button>
          <Button type="submit" form="form-rol" disabled={crear.isPending}>
            {crear.isPending && <Loader2 className="animate-spin" />}
            Crear rol
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
