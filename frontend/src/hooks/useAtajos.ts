import { useEffect, useRef } from "react";

type Atajos = Record<string, (e: KeyboardEvent) => void>;

/**
 * Atajos de teclado de la pantalla: { F2: buscar, F4: cobrar, "ctrl+Enter": ... }.
 * Las teclas de función funcionan aunque el foco esté en un campo de texto (el POS siempre tiene el buscador
 * enfocado); se desactivan mientras hay un diálogo abierto (`activo` = false).
 */
export function useAtajos(atajos: Atajos, activo = true) {
  const ref = useRef(atajos);
  useEffect(() => {
    ref.current = atajos;
  });

  useEffect(() => {
    if (!activo) return;
    const alPresionar = (e: KeyboardEvent) => {
      const tecla = `${e.ctrlKey ? "ctrl+" : ""}${e.altKey ? "alt+" : ""}${e.key}`;
      const accion = ref.current[tecla];
      if (!accion) return;
      e.preventDefault();
      accion(e);
    };
    window.addEventListener("keydown", alPresionar);
    return () => window.removeEventListener("keydown", alPresionar);
  }, [activo]);
}
