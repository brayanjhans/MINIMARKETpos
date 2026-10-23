import {
  Building2,
  KeyRound,
  Lock,
  LockOpen,
  LogIn,
  LogOut,
  type LucideIcon,
  Pencil,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  UserPlus,
  X,
} from "lucide-react";

import { PASTELES } from "@/lib/colores";

interface Accion {
  texto: string;
  riesgo?: boolean;
  icono: LucideIcon;
  color: string;
}

/** Cada acción auditada en palabras del negocio, con su ícono y color de la línea de tiempo. */
export const ACCIONES: Record<string, Accion> = {
  LOGIN: { texto: "Ingresó", icono: LogIn, color: PASTELES.verde },
  LOGOUT: { texto: "Cerró sesión", icono: LogOut, color: "bg-muted text-muted-foreground" },
  LOGIN_FALLIDO: { texto: "Ingreso fallido", riesgo: true, icono: X, color: PASTELES.coral },
  SESION_REVOCADA: { texto: "Sesión robada cerrada", riesgo: true, icono: ShieldAlert, color: PASTELES.coral },
  CAMBIAR_SUCURSAL: { texto: "Cambió de sucursal", icono: Building2, color: PASTELES.agua },
  CAMBIAR_PASSWORD: { texto: "Cambió su contraseña", icono: KeyRound, color: PASTELES.lila },
  CREAR: { texto: "Creó", icono: UserPlus, color: PASTELES.azul },
  EDITAR: { texto: "Editó", icono: Pencil, color: PASTELES.azul },
  ELIMINAR: { texto: "Eliminó", icono: Trash2, color: PASTELES.coral },
  RESTABLECER_PASSWORD: { texto: "Asignó contraseña", icono: KeyRound, color: PASTELES.lila },
  DESBLOQUEAR: { texto: "Desbloqueó", icono: LockOpen, color: PASTELES.verde },
  CERRAR_SESIONES: { texto: "Cerró sesiones", icono: LogOut, color: PASTELES.naranja },
};

export function accion(codigo: string, descripcion?: string | null, modulo?: string): Accion {
  // Un bloqueo se registra como ingreso fallido con la palabra "bloqueado" en la descripción
  if (codigo === "LOGIN_FALLIDO" && descripcion?.toLowerCase().includes("bloqueado")) {
    return { texto: "Quedó bloqueado", riesgo: true, icono: Lock, color: PASTELES.coral };
  }
  const base = ACCIONES[codigo] ?? {
    texto: codigo.replaceAll("_", " ").toLowerCase(),
    icono: Pencil,
    color: "bg-muted text-muted-foreground",
  };
  // Los cambios de roles van en amarillo, como en el boceto
  if (modulo === "roles" && !base.riesgo) return { ...base, icono: ShieldCheck, color: PASTELES.amarillo };
  return base;
}
