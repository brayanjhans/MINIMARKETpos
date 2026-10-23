"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Inicial } from "@/components/comunes/Inicial";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pestanas } from "@/components/comunes/Pestanas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { accion } from "@/lib/auditoria";
import { cn, fechaYHora } from "@/lib/utils";
import { auditoriaService, type FiltrosAuditoria } from "@/services/auditoria.service";
import type { AuditoriaItem } from "@/types";

const TAMANIO = 25;

type Tipo = "todo" | "sesiones" | "fallos" | "usuarios" | "roles";
const FILTRO_TIPO: Record<Tipo, Pick<FiltrosAuditoria, "modulo" | "accion">> = {
  todo: {},
  sesiones: { modulo: "auth" },
  fallos: { accion: "LOGIN_FALLIDO" },
  usuarios: { modulo: "usuarios" },
  roles: { modulo: "roles" },
};

const hoyLocal = () => fechaYHora(new Date().toISOString()).fecha;

export default function AuditoriaPage() {
  return (
    <RequierePermiso permiso="auditoria.ver">
      <Auditoria />
    </RequierePermiso>
  );
}

/** Agrupa los eventos por día para la línea de tiempo ("Hoy", "Ayer", "2026-10-20"). */
function agruparPorDia(items: AuditoriaItem[]): { dia: string; items: AuditoriaItem[] }[] {
  const hoy = hoyLocal();
  const ayer = fechaYHora(new Date(Date.now() - 86_400_000).toISOString()).fecha;
  const grupos = new Map<string, AuditoriaItem[]>();
  for (const item of items) {
    const { fecha } = fechaYHora(item.creado_en);
    const dia = fecha === hoy ? "Hoy" : fecha === ayer ? "Ayer" : fecha;
    grupos.set(dia, [...(grupos.get(dia) ?? []), item]);
  }
  return [...grupos].map(([dia, lista]) => ({ dia, items: lista }));
}

function Auditoria() {
  const [tipo, setTipo] = useState<Tipo>("todo");
  const [desde, setDesde] = useState(hoyLocal);
  const [hasta, setHasta] = useState(hoyLocal);
  const [pagina, setPagina] = useState(1);

  const filtros: FiltrosAuditoria = {
    pagina,
    tamanio: TAMANIO,
    orden: "-fecha",
    desde: desde || undefined,
    hasta: hasta || undefined,
    ...FILTRO_TIPO[tipo],
  };
  const consulta = useQuery({
    queryKey: ["auditoria", filtros],
    queryFn: ({ signal }) => auditoriaService.listar(filtros, signal),
    placeholderData: keepPreviousData,
  });
  const resumen = useQuery({
    queryKey: ["auditoria", "resumen", desde, hasta],
    queryFn: () => auditoriaService.resumen(desde || undefined, hasta || undefined),
  });

  const total = consulta.data?.total ?? 0;
  const paginas = Math.max(1, Math.ceil(total / TAMANIO));
  const esHoy = desde === hoyLocal() && hasta === hoyLocal();
  const periodo = esHoy ? "hoy" : `del ${desde || "inicio"} al ${hasta || "hoy"}`;

  const cambiar = (fn: () => void) => {
    fn();
    setPagina(1);
  };

  return (
    <>
      <PageHeader titulo="Auditoría" linea="Quién hizo qué, y cuándo" />

      <div className="mb-4 flex flex-col gap-3 xl:flex-row xl:items-end">
        <Pestanas
          etiqueta="Tipo de evento"
          valor={tipo}
          onCambiar={(v) => cambiar(() => setTipo(v))}
          opciones={[
            { valor: "todo", etiqueta: "Todo" },
            { valor: "sesiones", etiqueta: "Ingresos y sesiones" },
            { valor: "fallos", etiqueta: "Fallos y bloqueos", cantidad: resumen.data?.fallos },
            { valor: "usuarios", etiqueta: "Usuarios" },
            { valor: "roles", etiqueta: "Roles y permisos" },
          ]}
        />
        <div className="flex items-end gap-2 xl:ml-auto">
          <div className="space-y-1">
            <Label htmlFor="desde" className="text-xs text-muted-foreground">
              Desde
            </Label>
            <Input id="desde" type="date" value={desde} onChange={(e) => cambiar(() => setDesde(e.target.value))} className="h-[34px] rounded-[10px] border-0 bg-card" />
          </div>
          <div className="space-y-1">
            <Label htmlFor="hasta" className="text-xs text-muted-foreground">
              Hasta
            </Label>
            <Input id="hasta" type="date" value={hasta} onChange={(e) => cambiar(() => setHasta(e.target.value))} className="h-[34px] rounded-[10px] border-0 bg-card" />
          </div>
          {!esHoy && (
            <Button variant="outline" size="sm" className="h-[34px]" onClick={() => cambiar(() => (setDesde(hoyLocal()), setHasta(hoyLocal())))}>
              Hoy
            </Button>
          )}
        </div>
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_290px]">
        {/* Línea de tiempo */}
        <section className="tarjeta overflow-hidden" aria-label="Eventos">
          {consulta.isLoading ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-11 rounded-[12px]" />
              ))}
            </div>
          ) : total === 0 ? (
            <p className="px-5 py-14 text-center text-sm text-muted-foreground">
              No hubo actividad de este tipo {periodo}. Cambia las fechas o el filtro.
            </p>
          ) : (
            agruparPorDia(consulta.data!.items).map((grupo) => (
              <div key={grupo.dia}>
                <h2 className="px-5 pt-4 pb-2 text-[15px] font-extrabold">{grupo.dia}</h2>
                <ul>
                  {grupo.items.map((r) => {
                    const a = accion(r.accion, r.descripcion, r.modulo);
                    return (
                      <li
                        key={r.id}
                        className="grid grid-cols-[44px_36px_minmax(0,1fr)] items-center gap-3.5 border-t border-rule px-5 py-3 text-sm sm:grid-cols-[52px_36px_minmax(0,1fr)_auto]"
                      >
                        <span className="font-medium text-muted-foreground tabular">{fechaYHora(r.creado_en).hora}</span>
                        <span className={cn("grid size-9 place-items-center rounded-[11px]", a.color)}>
                          <a.icono className="size-[17px]" strokeWidth={2.2} aria-hidden />
                        </span>
                        <div className="min-w-0">
                          <p className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                            {r.usuario_id && r.usuario_nombre ? (
                              <span className="inline-flex items-center gap-1.5 font-bold">
                                <Inicial id={r.usuario_id} nombre={r.usuario_nombre} className="size-[22px] rounded-[7px] text-[10px]" />
                                {r.usuario_nombre}
                              </span>
                            ) : (
                              <span className="font-bold text-muted-foreground">Usuario desconocido</span>
                            )}
                            <span className={cn(a.riesgo && "font-bold text-destructive")}>{a.texto}</span>
                          </p>
                          {r.descripcion && <p className="truncate text-[13px] text-muted-foreground">{r.descripcion}</p>}
                        </div>
                        <span className="hidden text-xs text-muted-foreground tabular sm:block">{r.ip ?? "—"}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))
          )}
          {total > TAMANIO && (
            <div className="flex items-center justify-between border-t border-rule px-5 py-3 text-sm">
              <span className="font-medium text-muted-foreground tabular">
                {(pagina - 1) * TAMANIO + 1}–{Math.min(pagina * TAMANIO, total)} de {total}
              </span>
              <div className="flex items-center gap-1.5">
                <Button variant="outline" size="icon-sm" onClick={() => setPagina(pagina - 1)} disabled={pagina <= 1} aria-label="Página anterior">
                  <ChevronLeft />
                </Button>
                <Button variant="outline" size="icon-sm" onClick={() => setPagina(pagina + 1)} disabled={pagina >= paginas} aria-label="Página siguiente">
                  <ChevronRight />
                </Button>
              </div>
            </div>
          )}
        </section>

        {/* Resumen y lo que hay que revisar */}
        <div className="flex flex-col gap-4">
          <div className="tarjeta bg-navy p-[18px] text-white dark:bg-navy-2">
            <p className="text-[13px] text-navy-ink first-letter:uppercase">Eventos {periodo}</p>
            {resumen.data ? (
              <>
                <p className="text-[34px] leading-10 font-extrabold tabular">{resumen.data.total}</p>
                <dl className="mt-3 space-y-2 text-[13px]">
                  <div className="flex justify-between">
                    <dt>Ingresos</dt>
                    <dd className="font-bold tabular">{resumen.data.ingresos}</dd>
                  </div>
                  <div className="flex justify-between text-[#ffb3aa]">
                    <dt>Fallos y bloqueos</dt>
                    <dd className="font-bold tabular">{resumen.data.fallos}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Cambios de administración</dt>
                    <dd className="font-bold tabular">{resumen.data.cambios}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <Skeleton className="mt-2 h-24 bg-navy-2" />
            )}
          </div>

          {resumen.data?.revisar && (
            <div className="tarjeta bg-aviso-fondo p-[18px]">
              <h2 className="text-[15px] font-extrabold">Para revisar</h2>
              <p className="mt-2 mb-3 text-[13px] leading-relaxed text-muted-foreground">
                {resumen.data.revisar.nombre} tuvo {resumen.data.revisar.intentos_fallidos}{" "}
                {resumen.data.revisar.intentos_fallidos === 1 ? "ingreso fallido" : "ingresos fallidos"} {periodo}.
                Puede ser un olvido o alguien probando su contraseña.
              </p>
              <Button asChild size="sm">
                <Link href="/usuarios">Ver usuarios</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
