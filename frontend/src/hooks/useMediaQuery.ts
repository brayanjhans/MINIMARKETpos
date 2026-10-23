import { useSyncExternalStore } from "react";

/** true si la consulta CSS se cumple (ej. "(min-width: 1024px)"); se actualiza al cambiar el tamaño. */
export function useMediaQuery(consulta: string, enServidor = true): boolean {
  return useSyncExternalStore(
    (avisar) => {
      const mq = window.matchMedia(consulta);
      mq.addEventListener("change", avisar);
      return () => mq.removeEventListener("change", avisar);
    },
    () => window.matchMedia(consulta).matches,
    () => enServidor,
  );
}
