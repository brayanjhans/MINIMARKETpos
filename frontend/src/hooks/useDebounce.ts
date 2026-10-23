"use client";

import { useEffect, useState } from "react";

/** Devuelve el valor solo cuando deja de cambiar durante `ms` milisegundos (búsquedas al escribir). */
export function useDebounce<T>(valor: T, ms = 300): T {
  const [retrasado, setRetrasado] = useState(valor);
  useEffect(() => {
    const id = setTimeout(() => setRetrasado(valor), ms);
    return () => clearTimeout(id);
  }, [valor, ms]);
  return retrasado;
}
