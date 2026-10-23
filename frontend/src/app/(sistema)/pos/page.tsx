"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Clock, Loader2, Pause, Printer, ReceiptText, Store } from "lucide-react";
import Link from "next/link";
import { useCallback, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { AbrirCaja } from "@/components/caja/AbrirCaja";
import { BotonMenu } from "@/components/layout/BotonMenu";
import { AutorizacionDialog, type PedidoAutorizacion } from "@/components/pos/AutorizacionDialog";
import { BuscadorProductos, type BuscadorHandle, type Opcion } from "@/components/pos/BuscadorProductos";
import { Carrito } from "@/components/pos/Carrito";
import { ClienteDialog } from "@/components/pos/ClienteDialog";
import { ModalCobro } from "@/components/pos/ModalCobro";
import { ImprimirTicket } from "@/components/pos/Ticket";
import { VentaTerminada } from "@/components/pos/VentaTerminada";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useAtajos } from "@/hooks/useAtajos";
import { useAuth } from "@/hooks/useAuth";
import { useScanner } from "@/hooks/useScanner";
import { ApiError, mensajeError } from "@/lib/api";
import { cantidadValida } from "@/lib/inventario";
import { calcular, desdeCentimos } from "@/lib/ventas";
import { fechaYHora, iniciales, recencia, soles } from "@/lib/utils";
import { cajaService } from "@/services/caja.service";
import { ventasService } from "@/services/ventas.service";
import { useCarritoStore } from "@/store/carritoStore";
import type { PagoEntrada, VentaDetalle } from "@/types/ventas";

export default function PosPage() {
  return (
    <RequierePermiso permiso="pos.vender">
      <Pos />
    </RequierePermiso>
  );
}

function Pos() {
  const { usuario } = useAuth();
  const estado = useQuery({ queryKey: ["caja", "actual"], queryFn: cajaService.actual, refetchOnWindowFocus: true });
  const sesion = estado.data?.sesion;

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className="flex h-[60px] flex-none items-center gap-3 bg-navy px-3 text-white md:gap-4 md:px-5 dark:bg-navy-2">
        <BotonMenu className="text-navy-ink hover:bg-navy-2 hover:text-white" />
        <Link href="/dashboard" aria-label="Salir del punto de venta" className="grid size-9 place-items-center rounded-[10px] bg-amarillo text-navy">
          <Store className="size-5" />
        </Link>
        <span className="hidden text-base font-extrabold sm:block">Punto de venta</span>
        {sesion && (
          <span className="rounded-full bg-navy-2 px-3 py-1 text-[13px] text-navy-ink dark:bg-navy">
            <b className="text-amarillo">●</b> {sesion.caja} · abierta {fechaYHora(sesion.fecha_apertura).hora}
          </span>
        )}
        <div className="ml-auto hidden items-center gap-3 text-[13px] text-navy-ink xl:flex">
          {[
            ["F2", "Buscar"],
            ["F4", "Cobrar"],
            ["F6", "Cliente"],
            ["F8", "En espera"],
            ["F9", "Reimprimir"],
          ].map(([k, t]) => (
            <span key={k} className="flex items-center gap-1.5">
              <kbd className="grid h-[22px] min-w-[26px] place-items-center rounded-md bg-navy-2 px-1.5 text-[11px] font-extrabold text-amarillo dark:bg-navy">
                {k}
              </kbd>
              {t}
            </span>
          ))}
        </div>
        <Link
          href="/ventas"
          className="ml-auto flex items-center gap-1.5 rounded-[10px] px-2 py-1.5 text-[13px] font-semibold text-navy-ink hover:bg-navy-2 xl:ml-0"
        >
          <ReceiptText className="size-4" /> <span className="hidden sm:inline">Tickets</span>
        </Link>
        <Link
          href="/dashboard"
          className="flex items-center gap-1.5 rounded-[10px] px-2 py-1.5 text-[13px] font-semibold text-navy-ink hover:bg-navy-2 xl:ml-0"
        >
          <ArrowLeft className="size-4" /> Salir
        </Link>
        <span className="grid size-9 place-items-center rounded-[10px] bg-amarillo text-[13px] font-extrabold text-navy">
          {iniciales(usuario?.nombre_completo ?? "")}
        </span>
      </header>

      {estado.isLoading ? (
        <div className="grid flex-1 place-items-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      ) : estado.data?.sucursal_distinta ? (
        <div className="grid flex-1 place-items-center p-4">
          <p className="tarjeta max-w-md p-6 text-center text-sm">
            Tu caja abierta ({sesion?.caja}) es de otra sucursal. Ciérrala en <Link href="/caja" className="font-bold underline">Caja</Link> o
            cambia de sucursal.
          </p>
        </div>
      ) : !sesion ? (
        <div className="grid flex-1 place-items-center overflow-y-auto p-4">
          <AbrirCaja className="w-full max-w-lg" />
        </div>
      ) : (
        <Venta />
      )}
    </div>
  );
}

const AUTORIZABLE = (e: unknown): e is ApiError =>
  e instanceof ApiError && e.status === 403 && e.datos?.autorizable === true && typeof e.datos.permiso === "string";

function Venta() {
  const queryClient = useQueryClient();
  const { tiene } = useAuth();
  const buscador = useRef<BuscadorHandle>(null);
  const carrito = useCarritoStore();
  const catalogo = useQuery({
    queryKey: ["pos", "catalogo"],
    queryFn: ventasService.catalogo,
    staleTime: 60_000,
    refetchInterval: 5 * 60_000,
  });
  const config = catalogo.data?.configuracion;
  const productos = useMemo(() => catalogo.data?.productos ?? [], [catalogo.data]);

  const [cobrando, setCobrando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorCobro, setErrorCobro] = useState<string | null>(null);
  const [pedido, setPedido] = useState<PedidoAutorizacion | null>(null);
  const [clienteAbierto, setClienteAbierto] = useState(false);
  const [esperaAbierta, setEsperaAbierta] = useState(false);
  const [imprimir, setImprimir] = useState<VentaDetalle | null>(null);
  const [ultima, setUltima] = useState<VentaDetalle | null>(null);
  // Venta recién cobrada: se elige imprimir el ticket o pasar a la siguiente
  const [terminada, setTerminada] = useState<VentaDetalle | null>(null);
  // Pagos y autorizaciones del intento de cobro en curso (si falta una autorización, se reintenta con ella)
  const intento = useRef<{ pagos: PagoEntrada[]; total: string; autorizaciones: string[] } | null>(null);

  const totales = useMemo(
    () =>
      calcular(
        carrito.items.map((i) => ({
          cantidad: cantidadValida(i.cantidad, i.permite_decimales && !i.presentacion_id) ? i.cantidad.replace(",", ".") : "0",
          precio: i.precio,
          descuento: "0",
          afectacion: i.afectacion,
          bolsas: i.afecto_icbper ? String(Number(i.cantidad.replace(",", ".") || 0) * Number(i.factor)) : "0",
        })),
        /^\d{1,6}([.,]\d{1,2})?$/.test(carrito.descuento.trim()) ? carrito.descuento.trim().replace(",", ".") : "0",
        config?.igv_porcentaje ?? "18",
        config?.icbper_monto ?? "0.50",
        config?.precios_incluyen_igv ?? true,
      ),
    [carrito.items, carrito.descuento, config],
  );
  const invalida = carrito.items.find((i) => !cantidadValida(i.cantidad, i.permite_decimales && !i.presentacion_id) || Number(i.cantidad.replace(",", ".")) <= 0);
  const errorCarrito =
    totales.error ??
    (invalida ? `Revisa la cantidad de ${invalida.nombre}` : null) ??
    (carrito.descuento.trim() && !/^\d{1,6}([.,]\d{1,2})?$/.test(carrito.descuento.trim()) ? "Descuento no válido" : null);

  const agregar = useCallback(
    ({ producto: p, presentacion: pr }: Opcion, cantidad: string) => {
      if (Number(pr?.precio ?? p.precio) <= 0) return toast.error(`${p.nombre} no tiene precio de venta`);
      const unidades = Number(cantidad) * Number(pr?.factor ?? 1);
      if (Number(p.stock) < unidades && !tiene("pos.vender_sin_stock")) {
        toast.warning(`${p.nombre}: hay ${Number(p.stock)} en stock. Al cobrar se pedirá autorización.`);
      }
      carrito.agregar(
        {
          producto_id: p.id,
          nombre: p.nombre,
          presentacion_id: pr?.id ?? null,
          presentacion: pr?.nombre ?? null,
          factor: pr?.factor ?? "1",
          precio: pr?.precio ?? p.precio,
          afectacion: p.tipo_afectacion_igv,
          afecto_icbper: p.afecto_icbper,
          permite_decimales: p.permite_decimales,
        },
        cantidad,
      );
    },
    [carrito, tiene],
  );

  const porCodigo = useCallback(
    (codigo: string) => {
      const c = codigo.toUpperCase();
      for (const p of productos) {
        if (p.codigos.some((x) => x.toUpperCase() === c) || p.codigo_interno?.toUpperCase() === c)
          return agregar({ producto: p, presentacion: null }, "1");
        const pr = p.presentaciones.find((x) => x.codigos.some((y) => y.toUpperCase() === c));
        if (pr) return agregar({ producto: p, presentacion: pr }, "1");
      }
      toast.error(`No hay ningún producto con el código ${codigo}`);
    },
    [productos, agregar],
  );

  const enviar = async () => {
    const datos = intento.current;
    if (!datos) return;
    setEnviando(true);
    setErrorCobro(null);
    try {
      const venta = await ventasService.registrar(
        {
          items: carrito.items.map((i) => ({
            producto_id: i.producto_id,
            presentacion_id: i.presentacion_id,
            cantidad: i.cantidad.replace(",", "."),
            precio_unitario: i.precio,
            descuento: "0",
          })),
          descuento: carrito.descuento.trim() ? carrito.descuento.trim().replace(",", ".") : "0",
          pagos: datos.pagos,
          cliente_id: carrito.cliente?.id ?? null,
          total: datos.total,
          autorizaciones: datos.autorizaciones,
        },
        carrito.claveVenta,
      );
      intento.current = null;
      carrito.terminar();
      setCobrando(false);
      setUltima(venta);
      setTerminada(venta);
      void queryClient.invalidateQueries({ queryKey: ["pos", "catalogo"] });
      void queryClient.invalidateQueries({ queryKey: ["caja"] });
    } catch (error) {
      if (AUTORIZABLE(error)) {
        setPedido({ permiso: error.datos!.permiso as string, motivo: error.message });
      } else if (error instanceof ApiError && error.codigo === "precio_cambiado") {
        const { producto_id, presentacion_id, precio } = error.datos as { producto_id: number; presentacion_id: number | null; precio: string };
        for (const i of carrito.items)
          if (i.producto_id === producto_id && i.presentacion_id === presentacion_id) carrito.cambiar(i.clave, { precio });
        setErrorCobro(`${error.message}. Ya se actualizó en la venta: confirma de nuevo.`);
        void catalogo.refetch();
      } else {
        if (error instanceof ApiError && error.codigo === "total_distinto") void catalogo.refetch();
        if (error instanceof ApiError && error.codigo.startsWith("caja_")) void queryClient.invalidateQueries({ queryKey: ["caja"] });
        setErrorCobro(mensajeError(error));
      }
    } finally {
      setEnviando(false);
    }
  };

  const abrirCobro = () => {
    if (!carrito.items.length || errorCarrito || cobrando) return;
    intento.current = null;
    setErrorCobro(null);
    setCobrando(true);
  };

  const ponerEnEspera = () => {
    if (carrito.ponerEnEspera()) toast.info("Venta en espera (F8 para retomarla)");
    else setEsperaAbierta(true);
  };

  const dialogoAbierto = cobrando || clienteAbierto || esperaAbierta || !!pedido || !!terminada;
  useAtajos(
    {
      F2: () => buscador.current?.enfocar(),
      F4: abrirCobro,
      F6: () => setClienteAbierto(true),
      F8: ponerEnEspera,
      F9: () => ultima && setImprimir(ultima),
    },
    !dialogoAbierto,
  );
  useScanner(porCodigo, !dialogoAbierto);
  const impreso = useCallback(() => setImprimir(null), []);

  if (catalogo.isLoading || !config) {
    return (
      <div className="grid flex-1 place-items-center text-sm text-muted-foreground">
        {catalogo.isError ? mensajeError(catalogo.error) : <Loader2 className="size-6 animate-spin" />}
      </div>
    );
  }

  return (
    <div className="scrollbar-fino flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4 md:p-[18px] lg:flex-row lg:overflow-hidden">
      <section className="flex min-h-[62vh] min-w-0 flex-1 flex-col gap-3 lg:min-h-0">
        <BuscadorProductos ref={buscador} productos={productos} onAgregar={agregar} onNoEncontrado={(c) => toast.error(`No hay ningún producto con el código ${c}`)} />
        <div className="flex flex-none flex-wrap items-center gap-2 text-[13px]">
          {ultima && (
            <Button variant="outline" size="sm" onClick={() => setImprimir(ultima)}>
              <Printer /> {ultima.comprobante}
              {Number(ultima.vuelto) > 0 && <span className="text-muted-foreground"> · vuelto {soles(ultima.vuelto)}</span>}
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={ponerEnEspera}>
            <Pause /> {carrito.items.length ? "Poner en espera" : "En espera"}
            {carrito.enEspera.length > 0 && <b className="tabular">{carrito.enEspera.length}</b>}
          </Button>
        </div>
      </section>

      <div className="flex w-full flex-none flex-col lg:min-h-0 lg:w-[420px]">
        <Carrito
          items={carrito.items}
          totales={{ ...totales, error: errorCarrito }}
          igv={config.igv_porcentaje}
          cliente={carrito.cliente}
          descuento={carrito.descuento}
          ultimo={carrito.ultimo}
          onCantidad={(clave, cantidad) => carrito.cambiar(clave, { cantidad })}
          onQuitar={carrito.quitar}
          onDescuento={carrito.setDescuento}
          onCliente={() => setClienteAbierto(true)}
          onCobrar={abrirCobro}
          onVaciar={() => {
            carrito.vaciar();
            buscador.current?.enfocar();
          }}
        />
      </div>

      <ModalCobro
        abierto={cobrando}
        total={totales.total}
        redondeo={config.redondeo_efectivo}
        cliente={carrito.cliente}
        enviando={enviando}
        error={errorCobro}
        onElegirCliente={() => setClienteAbierto(true)}
        onCerrar={() => {
          setCobrando(false);
          buscador.current?.enfocar();
        }}
        onCobrar={(pagos, total) => {
          intento.current = { pagos, total, autorizaciones: [] };
          void enviar();
        }}
      />
      <AutorizacionDialog
        pedido={pedido}
        onCerrar={() => {
          setPedido(null);
          setErrorCobro("Falta la autorización del supervisor");
        }}
        onAutorizado={(token, supervisor) => {
          setPedido(null);
          toast.success(`Autorizó ${supervisor}`);
          if (intento.current) intento.current.autorizaciones.push(token);
          void enviar();
        }}
      />
      <ClienteDialog
        abierto={clienteAbierto}
        actual={carrito.cliente}
        onCerrar={() => setClienteAbierto(false)}
        onElegir={(c) => {
          carrito.setCliente(c);
          setClienteAbierto(false);
        }}
      />
      <Dialog open={esperaAbierta} onOpenChange={setEsperaAbierta}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Ventas en espera</DialogTitle>
            <DialogDescription>Se guardan en este equipo aunque se cierre el navegador.</DialogDescription>
          </DialogHeader>
          {carrito.enEspera.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No hay ventas en espera.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {carrito.enEspera.map((v) => {
                const t = calcular(
                  v.items.map((i) => ({ cantidad: i.cantidad, precio: i.precio, descuento: "0", afectacion: i.afectacion, bolsas: "0" })),
                  "0",
                  config.igv_porcentaje,
                  config.icbper_monto,
                );
                return (
                  <li key={v.id} className="flex items-center gap-3 rounded-xl bg-muted p-3">
                    <Clock className="size-4 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold">
                        {v.items.length} productos · {soles(desdeCentimos(t.total))}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {v.cliente?.nombre ?? "Varios"} · {recencia(v.creada)}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      disabled={carrito.items.length > 0}
                      onClick={() => {
                        carrito.recuperar(v.id);
                        setEsperaAbierta(false);
                      }}
                    >
                      Retomar
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => carrito.descartarEspera(v.id)}>
                      Descartar
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}
          {carrito.items.length > 0 && carrito.enEspera.length > 0 && (
            <p className="text-xs text-muted-foreground">Termina o pon en espera la venta actual para retomar otra.</p>
          )}
        </DialogContent>
      </Dialog>
      <VentaTerminada
        venta={terminada}
        onImprimir={() => {
          setImprimir(terminada);
          setTerminada(null);
          buscador.current?.enfocar();
        }}
        onSiguiente={() => {
          setTerminada(null);
          buscador.current?.enfocar();
        }}
      />
      <ImprimirTicket venta={imprimir} onListo={impreso} />
    </div>
  );
}
