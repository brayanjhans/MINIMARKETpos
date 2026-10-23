"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Ellipsis, KeyRound, LogOut, Pencil, Plus, Power, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { Inicial } from "@/components/comunes/Inicial";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pestanas } from "@/components/comunes/Pestanas";
import { Estado } from "@/components/comunes/Pildora";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { RestablecerPasswordDialog } from "@/components/usuarios/RestablecerPasswordDialog";
import { UsuarioFormDialog } from "@/components/usuarios/UsuarioFormDialog";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { mensajeError } from "@/lib/api";
import { colorRol } from "@/lib/colores";
import { cn, recencia } from "@/lib/utils";
import { rolesService } from "@/services/roles.service";
import { usuariosService } from "@/services/usuarios.service";
import type { UsuarioListado } from "@/types";

type Vista = "activos" | "inactivos" | "todos";
const TODOS = "todos";
const TAMANIO = 20;

const bloqueado = (u: UsuarioListado) => !!u.bloqueado_hasta && new Date(u.bloqueado_hasta) > new Date();
const minutosBloqueo = (u: UsuarioListado) =>
  Math.max(1, Math.ceil((new Date(u.bloqueado_hasta!).getTime() - Date.now()) / 60_000));

export default function UsuariosPage() {
  return (
    <RequierePermiso permiso="usuarios.ver">
      <Usuarios />
    </RequierePermiso>
  );
}

function Usuarios() {
  const { tiene, usuario: yo } = useAuth();
  const queryClient = useQueryClient();
  const [vista, setVista] = useState<Vista>("activos");
  const [busqueda, setBusqueda] = useState("");
  const [rol, setRol] = useState(TODOS);
  const [pagina, setPagina] = useState(1);
  const [orden, setOrden] = useState<string | undefined>("nombre");
  const [formulario, setFormulario] = useState<{ abierto: boolean; usuario: UsuarioListado | null }>({
    abierto: false,
    usuario: null,
  });
  const [restablecer, setRestablecer] = useState<UsuarioListado | null>(null);
  const busquedaDebounced = useDebounce(busqueda);

  const filtros = {
    pagina,
    tamanio: TAMANIO,
    orden,
    busqueda: busquedaDebounced || undefined,
    rol_id: rol === TODOS ? undefined : Number(rol),
    activo: vista === "todos" ? undefined : vista === "activos",
  };
  const consulta = useQuery({
    queryKey: ["usuarios", "lista", filtros],
    queryFn: ({ signal }) => usuariosService.listar(filtros, signal),
    placeholderData: keepPreviousData,
  });
  const resumen = useQuery({ queryKey: ["usuarios", "resumen"], queryFn: usuariosService.resumen });
  const roles = useQuery({ queryKey: ["roles"], queryFn: rolesService.listar });
  const total = consulta.data?.total ?? 0;
  const totalPersonas = (resumen.data?.con_acceso ?? 0) + (resumen.data?.sin_acceso ?? 0);

  const accion = useMutation({
    mutationFn: ({ fn }: { fn: () => Promise<unknown>; exito: string }) => fn(),
    onSuccess: (_, { exito }) => {
      toast.success(exito);
      void queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (error) => toast.error(mensajeError(error)),
  });

  const columnas = useMemo<ColumnDef<UsuarioListado, unknown>[]>(
    () => [
      {
        id: "nombre",
        header: "Persona",
        meta: { orden: "nombre", className: "sm:min-w-64" } satisfies MetaColumna,
        cell: ({ row: { original: u } }) => (
          <div className="flex items-center gap-3">
            <Inicial id={u.id} nombre={u.nombre_completo} color={colorRol(u.rol.nombre, u.rol.id)} className="size-[38px]" />
            <div className="min-w-0">
              <p className="truncate font-bold">
                {u.nombre_completo}
                {u.id === yo?.id && <span className="font-medium text-muted-foreground"> (tú)</span>}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                @{u.username}
                <span className="sm:hidden"> · {u.rol.nombre}</span>
              </p>
            </div>
          </div>
        ),
      },
      {
        id: "rol",
        header: "Rol",
        meta: { className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: u } }) => (
          <span
            className={cn(
              "inline-flex h-[26px] items-center rounded-lg px-2.5 text-xs font-bold whitespace-nowrap",
              u.activo ? colorRol(u.rol.nombre, u.rol.id) : "bg-muted text-muted-foreground",
            )}
          >
            {u.rol.nombre}
          </span>
        ),
      },
      {
        id: "sucursales",
        header: "Sucursal",
        meta: { className: "hidden xl:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => row.original.sucursales.map((s) => s.nombre).join(", "),
      },
      {
        id: "estado",
        header: "Estado",
        meta: { className: "hidden md:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: u } }) =>
          !u.activo ? (
            <Estado tono="neutro">Sin acceso</Estado>
          ) : bloqueado(u) ? (
            <Estado tono="negativo">Bloqueado {minutosBloqueo(u)} min</Estado>
          ) : (
            <Estado tono="positivo">Activo</Estado>
          ),
      },
      {
        id: "ultimo_acceso",
        header: "Último ingreso",
        meta: { orden: "ultimo_acceso", numero: true, className: "hidden lg:table-cell" } satisfies MetaColumna,
        cell: ({ row }) => (
          <span className={cn("font-medium", !row.original.ultimo_acceso && "text-muted-foreground")}>
            {recencia(row.original.ultimo_acceso)}
          </span>
        ),
      },
      {
        id: "acciones",
        header: () => <span className="sr-only">Acciones</span>,
        meta: { className: "w-px text-right" } satisfies MetaColumna,
        cell: ({ row: { original: u } }) => {
          if (!tiene("usuarios.editar")) return null;
          return (
            <div className="flex items-center justify-end gap-1">
              {bloqueado(u) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="font-bold"
                  onClick={() =>
                    accion.mutate({
                      fn: () => usuariosService.desbloquear(u.id),
                      exito: `${u.nombre_completo} ya puede ingresar`,
                    })
                  }
                >
                  Desbloquear
                </Button>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon-sm" aria-label={`Acciones de ${u.nombre_completo}`}>
                    <Ellipsis />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem onSelect={() => setFormulario({ abierto: true, usuario: u })}>
                    <Pencil /> Editar datos y rol
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={() => setRestablecer(u)}>
                    <KeyRound /> Asignar contraseña temporal
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onSelect={() =>
                      accion.mutate({
                        fn: () => usuariosService.cerrarSesiones(u.id),
                        exito: `Se cerraron las sesiones de ${u.nombre_completo}`,
                      })
                    }
                  >
                    <LogOut /> Cerrar sus sesiones
                  </DropdownMenuItem>
                  {u.id !== yo?.id && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        variant={u.activo ? "destructive" : "default"}
                        onSelect={() =>
                          accion.mutate({
                            fn: () => usuariosService.actualizar(u.id, { activo: !u.activo }),
                            exito: u.activo
                              ? `${u.nombre_completo} ya no puede ingresar`
                              : `${u.nombre_completo} puede ingresar de nuevo`,
                          })
                        }
                      >
                        <Power /> {u.activo ? "Quitar acceso" : "Devolver acceso"}
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          );
        },
      },
    ],
    [tiene, yo?.id, accion],
  );

  const cambiarFiltro = (fn: () => void) => {
    fn();
    setPagina(1);
  };

  return (
    <>
      <PageHeader
        titulo="Usuarios"
        linea="Personal que usa el sistema y lo que puede hacer"
        acciones={
          tiene("usuarios.crear") && (
            <Button onClick={() => setFormulario({ abierto: true, usuario: null })}>
              <Plus strokeWidth={2.6} /> Nuevo usuario
            </Button>
          )
        }
      />

      <section className="mb-4 grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
        <Contador etiqueta="Con acceso" valor={resumen.data?.con_acceso} oscuro />
        <Contador etiqueta="Ingresaron hoy" valor={resumen.data?.ingresaron_hoy} />
        <Contador etiqueta="Bloqueados por intentos" valor={resumen.data?.bloqueados} alerta />
        <Contador etiqueta="Sin acceso" valor={resumen.data?.sin_acceso} />
      </section>

      <DataTable
        barra={
          <>
            <label className="flex h-[38px] items-center gap-2 rounded-[10px] bg-muted px-3 text-muted-foreground sm:w-72">
              <Search className="size-4 flex-none" />
              <Input
                value={busqueda}
                onChange={(e) => cambiarFiltro(() => setBusqueda(e.target.value))}
                placeholder="Buscar por nombre o usuario"
                className="h-auto border-0 bg-transparent p-0 text-foreground focus-visible:ring-0 dark:bg-transparent"
                aria-label="Buscar usuarios"
              />
            </label>
            <Pestanas
              etiqueta="Filtrar por rol"
              valor={rol}
              onCambiar={(v) => cambiarFiltro(() => setRol(v))}
              opciones={[
                { valor: TODOS, etiqueta: "Todos", cantidad: resumen.data ? totalPersonas : undefined },
                ...(roles.data ?? []).map((r) => ({ valor: String(r.id), etiqueta: r.nombre, cantidad: r.total_usuarios })),
              ]}
            />
            <Select value={vista} onValueChange={(v) => cambiarFiltro(() => setVista(v as Vista))}>
              <SelectTrigger className="h-[34px] w-full rounded-[10px] border-0 bg-muted font-semibold sm:ml-auto sm:w-40" aria-label="Estado">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="activos">Con acceso</SelectItem>
                <SelectItem value="inactivos">Sin acceso</SelectItem>
                <SelectItem value="todos">Todos</SelectItem>
              </SelectContent>
            </Select>
          </>
        }
        columnas={columnas}
        datos={consulta.data?.items}
        cargando={consulta.isLoading}
        total={total}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        orden={orden}
        onOrden={setOrden}
        claseFila={(u) => (!u.activo ? "opacity-60" : bloqueado(u) ? "bg-pill-negative-bg/40" : undefined)}
        vacio={
          busquedaDebounced
            ? `Nadie coincide con «${busquedaDebounced}». Revisa la ortografía o busca por el usuario.`
            : vista === "inactivos"
              ? "Nadie está sin acceso. Cuando le quites el acceso a alguien aparecerá aquí."
              : "No hay usuarios en esta vista."
        }
      />

      <UsuarioFormDialog
        abierto={formulario.abierto}
        usuario={formulario.usuario}
        onCambiar={(abierto) => setFormulario((f) => ({ ...f, abierto }))}
      />
      <RestablecerPasswordDialog usuario={restablecer} onCerrar={() => setRestablecer(null)} />
    </>
  );
}

function Contador({
  etiqueta,
  valor,
  oscuro,
  alerta,
}: {
  etiqueta: string;
  valor: number | undefined;
  oscuro?: boolean;
  alerta?: boolean;
}) {
  return (
    <div className={cn("tarjeta px-[18px] py-4", oscuro && "bg-navy text-white dark:bg-navy-2")}>
      <p className={cn("text-[13px] font-medium", oscuro ? "text-navy-ink" : "text-muted-foreground")}>{etiqueta}</p>
      {valor === undefined ? (
        <Skeleton className="mt-1.5 h-8 w-10" />
      ) : (
        <p className={cn("text-[28px] leading-9 font-extrabold tabular", alerta && valor > 0 && "text-destructive")}>
          {valor}
        </p>
      )}
    </div>
  );
}
