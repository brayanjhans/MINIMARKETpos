import { useEffect, useRef } from "react";

const MAX_PAUSA_MS = 40; // un lector USB "escribe" cada carácter en pocos milisegundos
const MIN_LARGO = 6;

/**
 * Detecta códigos del lector USB cuando el foco NO está en un campo de texto (ej. tras hacer clic en un botón):
 * teclas muy seguidas que terminan en Enter. Si el foco está en un campo, el propio campo recibe el código.
 */
export function useScanner(onCodigo: (codigo: string) => void, activo = true) {
  const ref = useRef(onCodigo);
  useEffect(() => {
    ref.current = onCodigo;
  });

  useEffect(() => {
    if (!activo) return;
    let buffer = "";
    let ultima = 0;
    const alPresionar = (e: KeyboardEvent) => {
      const destino = e.target as HTMLElement | null;
      if (destino && (destino.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(destino.tagName))) return;
      const ahora = performance.now();
      if (ahora - ultima > MAX_PAUSA_MS) buffer = "";
      ultima = ahora;
      if (e.key === "Enter") {
        if (buffer.length >= MIN_LARGO) {
          e.preventDefault();
          ref.current(buffer);
        }
        buffer = "";
      } else if (e.key.length === 1) {
        buffer += e.key;
      }
    };
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [activo]);
}
