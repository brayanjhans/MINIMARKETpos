import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface UIState {
  sidebarColapsado: boolean;
  alternarSidebar: () => void;
}

/** Preferencias de interfaz que se recuerdan entre visitas. */
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarColapsado: false,
      alternarSidebar: () => set((s) => ({ sidebarColapsado: !s.sidebarColapsado })),
    }),
    { name: "mm-ui", storage: createJSONStorage(() => localStorage) },
  ),
);
