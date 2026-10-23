"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Coins, Plus, ReceiptText, Users } from "lucide-react";
import Link from "next/link";

import { Inicial } from "@/components/comunes/Inicial";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import { accion } from "@/lib/auditoria";
import { cn, fechaYHora, soles } from "@/lib/utils";
import { auditoriaService } from "@/services/auditoria.service";
import { usuariosService } from "@/services/usuarios.service";

const METODOS = [
  { nombre: "Efectivo", clase: "bg-muted" },
  { nombre: "Yape", clase: "bg-p-lila text-p-lila-t" },
  { nombre: "Tarjeta", clase: "bg-p-azul text-p-azul-t" },
  { nombre: "Plin", clase: "bg-p-agua text-p-agua-t" },
];

function saludo(): string {
  const hora = Number(
    new Intl.DateTimeFormat("es-PE", { hour: "numeric", hour12: false, timeZone: "America/Lima" }).format(new Date()),
  );
  return hora < 12 ? "Buen día" : hora < 19 ? "Buenas tardes" : "Buenas noches";
}

export default function InicioPage() {
  const { usuario, tiene } = useAuth();
  const hoy = fechaYHora(new Date().toISOString()).fecha;
  const fechaLarga = new Intl.DateTimeFormat("es-PE", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "America/Lima",
  }).format(new Date());

  const verAuditoria = tiene("auditoria.ver");
  const actividad = useQuery({
    queryKey: ["auditoria", "hoy", hoy],
    queryFn: () => auditoriaService.listar({ desde: hoy, hasta: hoy, tamanio: 5, orden: "-fecha" }),
    enabled: verAuditoria,
  });
  const resumenUsuarios = useQuery({
    queryKey: ["usuarios", "resumen"],
    queryFn: usuariosService.resumen,
    enabled: tiene("usuarios.ver"),
  });

  if (!usuario) return null;
  const nombre = usuario.nombre_completo.split(" ")[0];

  return (
    <div className="space-y-[18px]">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-[26px] leading-8 font-extrabold tracking-[-0.02em]">
            {saludo()}, {nombre}
          </h1>
          <p className="text-sm text-muted-foreground first-letter:uppercase">
            {fechaLarga} · Sucursal {usuario.sucursal_actual.nombre}
          </p>
        </div>
        {tiene("pos.vender") && (
          <Button asChild className="sm:ml-auto">
            <Link href="/pos">
              <Plus strokeWidth={2.6} /> Nueva venta · F2
            </Link>
          </Button>
        )}
      </header>

      {/* Indicadores */}
      <section className="grid grid-cols-2 gap-3 md:gap-4 xl:grid-cols-4">
        <div className="tarjeta col-span-2 bg-navy p-5 text-white md:col-span-1 dark:bg-navy-2">
          <p className="text-[13px] font-medium text-navy-ink">Ventas de hoy</p>
          <p className="mt-2.5 text-[30px] leading-9 font-extrabold tracking-[-0.02em] tabular">{soles(0)}</p>
          <p className="mt-1 text-xs text-navy-ink">Se suman solas con cada venta del punto de venta</p>
        </div>
        <Indicador icono={ReceiptText} color="bg-p-amarillo text-p-amarillo-t" etiqueta="Tickets" valor="0" />
        <Indicador icono={Coins} color="bg-p-azul text-p-azul-t" etiqueta="Ticket promedio" valor="—" />
        <Indicador
          className="col-span-2 md:col-span-1"
          icono={Users}
          color="bg-p-agua text-p-agua-t"
          etiqueta="Personas con acceso"
          valor={resumenUsuarios.isLoading ? null : resumenUsuarios.data ? String(resumenUsuarios.data.con_acceso) : "—"}
        />
      </section>

      <section className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        {/* Ventas por hora */}
        <div className="tarjeta flex flex-col p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold">Ventas por hora</h2>
            <span className="text-[13px] font-medium text-muted-foreground">Hoy</span>
          </div>
          <div className="my-5 grid h-[170px] place-items-center rounded-[14px] border-2 border-dashed border-rule text-center">
            <div className="px-6">
              <BarChart3 className="mx-auto size-8 text-muted-foreground/60" aria-hidden />
              <p className="mt-2 text-sm font-semibold">Todavía no hay ventas hoy</p>
              <p className="text-[13px] text-muted-foreground">El gráfico se llena con cada venta registrada en la caja.</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {METODOS.map((m) => (
              <div key={m.nombre} className={cn("rounded-[12px] px-3 py-2.5", m.clase)}>
                <p className="text-[13px] font-medium opacity-80">{m.nombre}</p>
                <p className="font-bold tabular">{soles(0)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Columna derecha */}
        <div className="flex flex-col gap-4">
          {verAuditoria && (
            <div className="tarjeta p-5">
              <div className="mb-1.5 flex items-center justify-between">
                <h2 className="text-base font-bold">Actividad de hoy</h2>
                <Link href="/auditoria" className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
                  Ver todo
                </Link>
              </div>
              {actividad.isLoading ? (
                <div className="space-y-2 pt-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 rounded-[10px]" />
                  ))}
                </div>
              ) : actividad.data?.items.length ? (
                <ul>
                  {actividad.data.items.map((r) => {
                    const a = accion(r.accion);
                    return (
                      <li key={r.id} className="flex items-center gap-3 border-t border-rule py-2.5 text-sm">
                        {r.usuario_id && r.usuario_nombre ? (
                          <Inicial id={r.usuario_id} nombre={r.usuario_nombre} />
                        ) : (
                          <span className="size-9 flex-none" />
                        )}
                        <span className="min-w-0 flex-1">
                          <span className="block truncate font-semibold">{r.usuario_nombre ?? "Desconocido"}</span>
                          <span className={cn("block text-xs", a.riesgo ? "font-semibold text-destructive" : "text-muted-foreground")}>
                            {a.texto}
                          </span>
                        </span>
                        <span className="text-xs font-medium text-muted-foreground tabular">
                          {fechaYHora(r.creado_en).hora}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="border-t border-rule pt-3 text-sm text-muted-foreground">Nadie ha ingresado todavía hoy.</p>
              )}
            </div>
          )}

          <div className="tarjeta bg-aviso-fondo p-5">
            <h2 className="text-base font-bold">Atención hoy</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Aquí aparecerán los productos con stock bajo y los que están por vencer, en cuanto se registre el
              inventario.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function Indicador({
  icono: Icono,
  color,
  etiqueta,
  valor,
  className,
}: {
  icono: typeof ReceiptText;
  color: string;
  etiqueta: string;
  valor: string | null;
  className?: string;
}) {
  return (
    <div className={cn("tarjeta flex items-center gap-3 p-4 md:gap-3.5 md:p-5", className)}>
      <span className={cn("grid size-10 flex-none place-items-center rounded-[12px] md:size-11", color)}>
        <Icono className="size-5 md:size-[22px]" aria-hidden />
      </span>
      <div className="min-w-0">
        <p className="text-[13px] leading-4 font-medium text-muted-foreground">{etiqueta}</p>
        {valor === null ? (
          <Skeleton className="mt-1 h-7 w-12" />
        ) : (
          <p className="text-[26px] leading-8 font-extrabold tabular">{valor}</p>
        )}
      </div>
    </div>
  );
}
