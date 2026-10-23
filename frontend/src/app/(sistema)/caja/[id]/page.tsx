"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2, Lock } from "lucide-react";
import Link from "next/link";
import { use } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { PildoraDiferencia } from "@/components/caja/PildoraDiferencia";
import { Indicador } from "@/components/comunes/Indicador";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";
import { METODOS } from "@/lib/ventas";
import { cn, fechaHora, fechaYHora, soles } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";
import { ventasService } from "@/services/ventas.service";

export default function SesionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <RequierePermiso permiso="caja.ver">
      <Detalle id={Number(id)} />
    </RequierePermiso>
  );
}

function Detalle({ id }: { id: number }) {
  const { tiene, usuario } = useAuth();
  const sesion = useQuery({ queryKey: ["caja", "sesion", id], queryFn: () => cajaService.sesion(id) });
  const ventas = useQuery({
    queryKey: ["ventas", "turno", id],
    queryFn: () => ventasService.listar({ sesion_caja_id: id, tamanio: 100 }),
    enabled: tiene("pos.vender"),
  });

  if (sesion.isLoading) return <Loader2 className="size-6 animate-spin text-muted-foreground" />;
  if (!sesion.data) return <p className="text-sm text-muted-foreground">{mensajeError(sesion.error)}</p>;
  const s = sesion.data;
  const abierta = s.estado === "ABIERTA";
  const puedeCerrar = abierta && tiene("caja.cerrar") && (s.usuario_id === usuario?.id || tiene("caja.ver_todas"));

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[13px] text-muted-foreground">
            <Link href="/caja" className="hover:underline">
              Caja
            </Link>{" "}
            ›
          </p>
          <h1 className="flex flex-wrap items-center gap-3 text-[26px] leading-8 font-extrabold tracking-[-0.02em]">
            {s.caja} · {fechaYHora(s.fecha_apertura).fecha}
            <PildoraDiferencia diferencia={abierta ? null : s.diferencia} />
          </h1>
          <p className="text-sm text-muted-foreground">
            {s.usuario} · {fechaHora(s.fecha_apertura)} – {s.fecha_cierre ? fechaHora(s.fecha_cierre) : "sigue abierta"}
          </p>
        </div>
        {puedeCerrar && (
          <Button asChild>
            <Link href={`/caja/${s.id}/cerrar`}>
              <Lock /> Cerrar caja
            </Link>
          </Button>
        )}
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Indicador oscuro etiqueta="Vendido" valor={s.total_vendido !== null ? soles(s.total_vendido) : "Al cerrar"} detalle={`${s.ventas} ventas`} />
        <Indicador etiqueta="Efectivo esperado" valor={s.efectivo_esperado !== null ? soles(s.efectivo_esperado) : "Al cerrar"} detalle={`inicial ${soles(s.monto_inicial)}`} />
        <Indicador etiqueta="Contado" valor={s.monto_contado !== null ? soles(s.monto_contado) : "—"} detalle={s.observaciones_cierre ?? "en el arqueo"} />
        <Indicador
          etiqueta="Diferencia"
          valor={s.diferencia !== null ? soles(s.diferencia) : "—"}
          alerta={Number(s.diferencia ?? 0) < 0}
          detalle={s.anuladas ? `${s.anuladas} venta(s) anulada(s)` : "sin anulaciones"}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <section className="tarjeta overflow-hidden">
          <h2 className="px-5 pt-4 pb-2 font-extrabold">Por forma de pago</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-cabecera-tabla text-left text-xs font-bold text-muted-foreground">
                <th className="h-9 px-5">Forma</th>
                <th className="px-2 text-right">Operaciones</th>
                <th className="px-2 text-right">Sistema</th>
                <th className="px-2 text-right">Declarado</th>
                <th className="px-5 text-right">Diferencia</th>
              </tr>
            </thead>
            <tbody>
              {s.metodos.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-6 text-center text-muted-foreground">
                    Sin ventas en este turno.
                  </td>
                </tr>
              )}
              {s.metodos.map((m) => (
                <tr key={m.metodo} className="border-t border-rule">
                  <td className={cn("px-5 py-2.5 font-bold", METODOS[m.metodo].color)}>{METODOS[m.metodo].texto}</td>
                  <td className="px-2 text-right tabular">{m.operaciones}</td>
                  <td className="px-2 text-right tabular">{m.monto_sistema !== null ? soles(m.monto_sistema) : "—"}</td>
                  <td className="px-2 text-right tabular">{m.monto_declarado !== null ? soles(m.monto_declarado) : "—"}</td>
                  <td className={cn("px-5 text-right font-bold tabular", Number(m.diferencia ?? 0) < 0 && "text-destructive")}>
                    {m.diferencia !== null ? soles(m.diferencia) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="tarjeta overflow-hidden">
          <h2 className="px-5 pt-4 pb-2 font-extrabold">Arqueo</h2>
          {s.arqueo.length === 0 ? (
            <p className="px-5 pb-5 text-sm text-muted-foreground">{abierta ? "Se cuenta al cerrar la caja." : "No se contó efectivo."}</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {s.arqueo.map((a) => (
                  <tr key={a.denominacion} className="border-t border-rule">
                    <td className="px-5 py-2 font-bold tabular">{soles(a.denominacion)}</td>
                    <td className="px-2 text-muted-foreground">{a.tipo === "BILLETE" ? "billetes" : "monedas"}</td>
                    <td className="px-2 text-right tabular">× {a.cantidad}</td>
                    <td className="px-5 text-right font-bold tabular">{soles(a.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {s.movimientos.length > 0 && (
          <section className="tarjeta overflow-hidden">
            <h2 className="px-5 pt-4 pb-2 font-extrabold">Ingresos y egresos</h2>
            <ul>
              {s.movimientos.map((m) => (
                <li key={m.id} className="flex items-center justify-between gap-3 border-t border-rule px-5 py-2.5 text-sm">
                  <span className="min-w-0 truncate">
                    <b>{m.concepto}</b> <span className="text-muted-foreground">· {m.usuario} · {fechaYHora(m.creado_en).hora}</span>
                  </span>
                  <b className={cn("tabular", m.tipo === "EGRESO" && "text-destructive")}>
                    {m.tipo === "EGRESO" ? "−" : "+"}
                    {soles(m.monto)}
                  </b>
                </li>
              ))}
            </ul>
          </section>
        )}

        {ventas.data && (
          <section className="tarjeta overflow-hidden">
            <h2 className="px-5 pt-4 pb-2 font-extrabold">Ventas del turno ({ventas.data.total})</h2>
            <ul className="scrollbar-fino max-h-96 overflow-y-auto">
              {ventas.data.items.map((v) => (
                <li key={v.id} className="border-t border-rule">
                  <Link href={`/ventas/${v.id}`} className="flex items-center justify-between gap-3 px-5 py-2.5 text-sm hover:bg-muted">
                    <span className={cn("font-bold tabular", v.estado === "ANULADA" && "text-muted-foreground line-through")}>
                      {v.comprobante}
                    </span>
                    <span className="text-muted-foreground">
                      {fechaYHora(v.fecha).hora} · {v.metodos.map((m) => METODOS[m].corto).join(" + ")}
                    </span>
                    <b className="tabular">{soles(v.a_cobrar)}</b>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </>
  );
}
