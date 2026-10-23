"use client";

import { Check, ChevronDown, KeyRound, LogOut, Monitor, Moon, Sun } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useTheme } from "next-themes";
import { useState } from "react";
import { toast } from "sonner";

import { CambiarPasswordDialog } from "@/components/auth/CambiarPasswordDialog";
import { Marca } from "@/components/comunes/Marca";
import { BotonMenu } from "@/components/layout/BotonMenu";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";
import { cn, fechaYHora, iniciales } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";

/** Barra superior: la caja y la sucursal a la izquierda; el tema y el usuario a la derecha. */
export function Topbar() {
  const { usuario, logout, cambiarSucursal, tiene } = useAuth();
  const [dialogoPassword, setDialogoPassword] = useState(false);

  if (!usuario) return null;
  const variasSucursales = usuario.sucursales.length > 1;

  const elegirSucursal = async (id: number) => {
    if (id === usuario.sucursal_actual.id) return;
    try {
      const r = await cambiarSucursal(id);
      toast.success(`Ahora trabajas en ${r.usuario.sucursal_actual.nombre}`);
    } catch (error) {
      toast.error(mensajeError(error));
    }
  };

  return (
    <header className="flex h-16 shrink-0 items-center gap-2.5 px-4 md:px-7">
      <BotonMenu className="-ml-1 hover:bg-card lg:hidden" />
      <Marca className="md:hidden" />

      <div className="hidden items-center gap-2 md:flex">
        {tiene("caja.ver") && <EstadoCaja />}
        <DropdownMenu>
          <DropdownMenuTrigger asChild disabled={!variasSucursales}>
            <button
              type="button"
              className="inline-flex h-9 items-center gap-1.5 rounded-[10px] bg-card px-3 text-[13px] font-semibold transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:hover:bg-card"
            >
              Sucursal {usuario.sucursal_actual.nombre}
              {variasSucursales && <ChevronDown className="size-3.5 text-muted-foreground" />}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-60">
            <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">Trabajar en</DropdownMenuLabel>
            {usuario.sucursales.map((s) => (
              <DropdownMenuItem key={s.id} onSelect={() => elegirSucursal(s.id)}>
                <span className="flex-1 truncate">{s.nombre}</span>
                <span className="text-xs text-muted-foreground tabular">{s.codigo}</span>
                {s.id === usuario.sucursal_actual.id && <Check />}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="ml-auto flex items-center gap-2">
        <SelectorTema />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex h-11 items-center gap-2.5 rounded-[12px] p-1 pr-1 text-left transition-colors hover:bg-card focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none md:pr-3"
              aria-label="Menú de usuario"
            >
              <span className="grid size-9 place-items-center rounded-[11px] bg-navy text-xs font-extrabold text-amarillo dark:bg-navy-2">
                {iniciales(usuario.nombre_completo)}
              </span>
              <span className="hidden leading-tight md:block">
                <span className="block max-w-44 truncate text-sm font-bold">{usuario.nombre_completo}</span>
                <span className="block text-xs text-muted-foreground">{usuario.rol.nombre}</span>
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            <DropdownMenuLabel className="font-normal">
              <p className="font-bold">{usuario.nombre_completo}</p>
              <p className="text-xs text-muted-foreground">
                {usuario.rol.nombre} · @{usuario.username}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => setDialogoPassword(true)}>
              <KeyRound /> Cambiar contraseña
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => logout()}>
              <LogOut /> Cerrar sesión
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <CambiarPasswordDialog abierto={dialogoPassword} onCambiar={setDialogoPassword} />
    </header>
  );
}

/** La caja del usuario: abierta (con la hora) o cerrada; lleva a la pantalla de Caja. */
function EstadoCaja() {
  const estado = useQuery({ queryKey: ["caja", "actual"], queryFn: cajaService.actual, staleTime: 30_000 });
  const sesion = estado.data?.sesion;
  return (
    <Link
      href="/caja"
      className="inline-flex h-9 items-center gap-2 rounded-[10px] bg-card px-3 text-[13px] font-semibold transition-colors hover:bg-accent"
    >
      <span aria-hidden className={cn("size-2 rounded-full", sesion ? "bg-positive" : "bg-muted-foreground/50")} />
      {sesion ? `${sesion.caja} · abierta ${fechaYHora(sesion.fecha_apertura).hora}` : "Caja cerrada"}
    </Link>
  );
}

function SelectorTema() {
  const { setTheme } = useTheme();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Cambiar tema" className="rounded-[12px] hover:bg-card">
          <Sun className="dark:hidden" />
          <Moon className="hidden dark:block" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={() => setTheme("light")}>
          <Sun /> Claro
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => setTheme("dark")}>
          <Moon /> Oscuro
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => setTheme("system")}>
          <Monitor /> Según el equipo
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
