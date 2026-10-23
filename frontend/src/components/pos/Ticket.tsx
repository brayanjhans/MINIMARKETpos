"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";

import { cantidad } from "@/lib/inventario";
import { METODOS } from "@/lib/ventas";
import { cn, fechaHora } from "@/lib/utils";
import type { VentaDetalle } from "@/types/ventas";

const s = (v: string | number) => Number(v).toFixed(2);

function Fila({ izq, der, fuerte }: { izq: string; der: string; fuerte?: boolean }) {
  return (
    <div className={cn("flex justify-between gap-2", fuerte && "text-[13px] font-extrabold")}>
      <span>{izq}</span>
      <span className="tabular">{der}</span>
    </div>
  );
}

/** Ticket de 80 mm (también sirve en 58 mm: el ancho se adapta al papel). */
export function Ticket({ venta, className }: { venta: VentaDetalle; className?: string }) {
  const e = venta.empresa;
  const anulada = venta.estado === "ANULADA";
  return (
    <div className={cn("relative w-[72mm] bg-white p-[3mm] font-sans text-[11px] leading-snug text-black", className)}>
      {anulada && (
        <p className="mb-2 border-2 border-black py-1 text-center text-[14px] font-extrabold tracking-widest">ANULADA</p>
      )}
      <div className="text-center">
        <p className="text-[14px] font-extrabold">{e.nombre_comercial || e.razon_social}</p>
        {e.nombre_comercial && <p>{e.razon_social}</p>}
        <p>RUC {e.ruc}</p>
        {(e.direccion_sucursal || e.direccion) && <p>{e.direccion_sucursal || e.direccion}</p>}
        {e.telefono && <p>Tel. {e.telefono}</p>}
      </div>
      <div className="my-2 border-t border-dashed border-black" />
      <p className="text-center font-extrabold">TICKET DE VENTA {venta.comprobante}</p>
      <p>Fecha: {fechaHora(venta.fecha)}</p>
      <p>
        {venta.caja} · Cajero: {venta.usuario}
      </p>
      {venta.cliente && (
        <p>
          Cliente: {venta.cliente}
          {venta.cliente_documento && ` (${venta.cliente_documento})`}
        </p>
      )}
      <div className="my-2 border-t border-dashed border-black" />
      {venta.detalles.map((d) => (
        <div key={d.id} className="mb-1">
          <p className="font-semibold">{d.descripcion}</p>
          <Fila
            izq={`${cantidad(d.cantidad)} x ${s(d.precio_unitario)}${Number(d.descuento) > 0 ? ` (−${s(d.descuento)})` : ""}`}
            der={s(d.total)}
          />
        </div>
      ))}
      <div className="my-2 border-t border-dashed border-black" />
      {Number(venta.op_gravadas) > 0 && <Fila izq="Op. gravada" der={s(venta.op_gravadas)} />}
      {Number(venta.op_exoneradas) > 0 && <Fila izq="Op. exonerada" der={s(venta.op_exoneradas)} />}
      {Number(venta.op_inafectas) > 0 && <Fila izq="Op. inafecta" der={s(venta.op_inafectas)} />}
      <Fila izq={`IGV ${Number(venta.igv_porcentaje)}%`} der={s(venta.igv)} />
      {Number(venta.icbper) > 0 && <Fila izq="ICBPER" der={s(venta.icbper)} />}
      {Number(venta.descuento) > 0 && <Fila izq="Descuento" der={`−${s(venta.descuento)}`} />}
      {Number(venta.redondeo) !== 0 && <Fila izq="Redondeo" der={s(venta.redondeo)} />}
      <Fila izq="TOTAL S/" der={s(venta.a_cobrar)} fuerte />
      <div className="my-2 border-t border-dashed border-black" />
      {venta.pagos.map((p, i) => (
        <Fila
          key={i}
          izq={`${METODOS[p.metodo].texto}${p.referencia ? ` ${p.referencia}` : ""}`}
          der={s(p.monto_recibido ?? p.monto)}
        />
      ))}
      {Number(venta.vuelto) > 0 && <Fila izq="Vuelto" der={s(venta.vuelto)} fuerte />}
      <div className="my-2 border-t border-dashed border-black" />
      <p className="text-center">Documento interno de venta. Canjéelo por boleta o factura si lo necesita.</p>
      {e.mensaje_ticket && <p className="mt-1 text-center font-semibold">{e.mensaje_ticket}</p>}
      {anulada && venta.motivo_anulacion && <p className="mt-2">Anulada: {venta.motivo_anulacion}</p>}
    </div>
  );
}

/**
 * Imprime el ticket con el diálogo del navegador (Chrome en modo quiosco con --kiosk-printing imprime directo en
 * la térmica predeterminada). Solo el ticket es visible al imprimir (estilos @media print en globals.css).
 */
export function ImprimirTicket({ venta, onListo }: { venta: VentaDetalle | null; onListo: () => void }) {
  useEffect(() => {
    if (!venta) return;
    const terminar = () => onListo();
    window.addEventListener("afterprint", terminar, { once: true });
    // Se espera a que el ticket esté pintado antes de abrir la impresión
    const id = requestAnimationFrame(() => requestAnimationFrame(() => window.print()));
    return () => {
      cancelAnimationFrame(id);
      window.removeEventListener("afterprint", terminar);
    };
  }, [venta, onListo]);

  if (!venta || typeof document === "undefined") return null;
  return createPortal(
    <div className="ticket-impresion" aria-hidden>
      <Ticket venta={venta} />
    </div>,
    document.body,
  );
}
