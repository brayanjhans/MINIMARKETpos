import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { nuevaClave } from "@/lib/api";
import type { Afectacion, Cliente } from "@/types/ventas";

export interface ItemCarrito {
  clave: string;
  producto_id: number;
  nombre: string;
  presentacion_id: number | null;
  presentacion: string | null;
  factor: string;
  precio: string;
  afectacion: Afectacion;
  afecto_icbper: boolean;
  permite_decimales: boolean;
  cantidad: string;
  descuento: string;
}

export interface VentaEnEspera {
  id: string;
  creada: string;
  items: ItemCarrito[];
  descuento: string;
  cliente: Cliente | null;
}

interface CarritoState {
  items: ItemCarrito[];
  descuento: string;
  cliente: Cliente | null;
  /** Clave de la venta en curso: si el cobro se reintenta (red, doble Enter), el servidor no la duplica */
  claveVenta: string;
  ultimo: string | null;
  enEspera: VentaEnEspera[];
  agregar: (item: Omit<ItemCarrito, "clave" | "cantidad" | "descuento">, cantidad?: string) => void;
  cambiar: (clave: string, cambios: Partial<Pick<ItemCarrito, "cantidad" | "descuento" | "precio">>) => void;
  quitar: (clave: string) => void;
  setDescuento: (descuento: string) => void;
  setCliente: (cliente: Cliente | null) => void;
  /** Tras cobrar: carrito vacío y clave nueva para la próxima venta */
  terminar: () => void;
  vaciar: () => void;
  ponerEnEspera: () => boolean;
  recuperar: (id: string) => void;
  descartarEspera: (id: string) => void;
}

const sumar = (a: string, b: string) => String(Math.round((Number(a) + Number(b)) * 1000) / 1000);
const limpio = { items: [], descuento: "", cliente: null, ultimo: null };

export const useCarritoStore = create<CarritoState>()(
  persist(
    (set, get) => ({
      ...limpio,
      claveVenta: nuevaClave(),
      enEspera: [],
      agregar: (item, cantidad = "1") =>
        set((s) => {
          const existente = s.items.find(
            (i) => i.producto_id === item.producto_id && i.presentacion_id === item.presentacion_id,
          );
          if (existente) {
            return {
              items: s.items.map((i) => (i === existente ? { ...i, cantidad: sumar(i.cantidad, cantidad) } : i)),
              ultimo: existente.clave,
            };
          }
          const nuevo = { ...item, clave: nuevaClave(), cantidad, descuento: "" };
          return { items: [...s.items, nuevo], ultimo: nuevo.clave };
        }),
      cambiar: (clave, cambios) => set((s) => ({ items: s.items.map((i) => (i.clave === clave ? { ...i, ...cambios } : i)) })),
      quitar: (clave) => set((s) => ({ items: s.items.filter((i) => i.clave !== clave) })),
      setDescuento: (descuento) => set({ descuento }),
      setCliente: (cliente) => set({ cliente }),
      terminar: () => set({ ...limpio, claveVenta: nuevaClave() }),
      vaciar: () => set({ ...limpio, claveVenta: nuevaClave() }),
      ponerEnEspera: () => {
        const { items, descuento, cliente, enEspera } = get();
        if (!items.length) return false;
        set({
          ...limpio,
          claveVenta: nuevaClave(),
          enEspera: [...enEspera, { id: nuevaClave(), creada: new Date().toISOString(), items, descuento, cliente }].slice(-10),
        });
        return true;
      },
      recuperar: (id) => {
        const { enEspera, items } = get();
        const venta = enEspera.find((v) => v.id === id);
        if (!venta || items.length) return;
        set({
          items: venta.items,
          descuento: venta.descuento,
          cliente: venta.cliente,
          ultimo: null,
          claveVenta: nuevaClave(),
          enEspera: enEspera.filter((v) => v.id !== id),
        });
      },
      descartarEspera: (id) => set((s) => ({ enEspera: s.enEspera.filter((v) => v.id !== id) })),
    }),
    {
      // Si se cierra el navegador o se va la luz, la venta en curso y las que están en espera se recuperan
      name: "mm-carrito",
      storage: createJSONStorage(() => localStorage),
      partialize: ({ items, descuento, cliente, claveVenta, enEspera }) => ({ items, descuento, cliente, claveVenta, enEspera }),
    },
  ),
);
