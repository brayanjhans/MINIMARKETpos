"use client";

import { LayoutDashboard, Menu, Package, Plus, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Sidebar } from "@/components/layout/Sidebar";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/dashboard", titulo: "Inicio", icono: LayoutDashboard, permiso: "dashboard.ver" },
  { href: "/productos", titulo: "Stock", icono: Package, permiso: "productos.ver" },
  { href: "/caja", titulo: "Caja", icono: Wallet, permiso: "caja.ver" },
];

/** Navegación del celular: barra inferior con el botón amarillo de vender al centro. */
export function BarraInferior() {
  const pathname = usePathname();
  const { tiene } = useAuth();
  const [menu, setMenu] = useState(false);
  const [inicio, stock, caja] = ITEMS.map((i) => ({ ...i, visible: tiene(i.permiso) }));

  const Item = ({ item }: { item: (typeof ITEMS)[number] & { visible: boolean } }) => {
    if (!item.visible) return <span className="flex-1" />;
    const activo = pathname.startsWith(item.href);
    return (
      <Link
        href={item.href}
        aria-current={activo ? "page" : undefined}
        className={cn(
          "flex flex-1 flex-col items-center gap-0.5 text-[11px] font-semibold",
          activo ? "text-foreground" : "text-muted-foreground",
        )}
      >
        <item.icono className="size-[22px]" strokeWidth={2} aria-hidden />
        {item.titulo}
      </Link>
    );
  };

  return (
    <>
      <nav
        aria-label="Navegación principal"
        className="fixed inset-x-0 bottom-0 z-40 flex h-[72px] items-center border-t border-rule bg-card px-2 pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        <Item item={inicio!} />
        <Item item={stock!} />
        {tiene("pos.vender") ? (
          <Link href="/pos" aria-label="Nueva venta" className="-mt-8 flex-none px-2">
            <span className="grid size-[58px] place-items-center rounded-[18px] bg-amarillo text-[#14213d] shadow-[0_8px_18px_rgba(255,195,0,0.45)]">
              <Plus className="size-7" strokeWidth={2.6} />
            </span>
          </Link>
        ) : (
          <span className="flex-1" />
        )}
        <Item item={caja!} />
        <button
          type="button"
          onClick={() => setMenu(true)}
          className="flex flex-1 flex-col items-center gap-0.5 text-[11px] font-semibold text-muted-foreground"
        >
          <Menu className="size-[22px]" aria-hidden />
          Más
        </button>
      </nav>
      <Sheet open={menu} onOpenChange={setMenu}>
        <SheetContent side="left" className="w-72 border-0 bg-navy p-0">
          <SheetTitle className="sr-only">Menú principal</SheetTitle>
          <Sidebar movil alNavegar={() => setMenu(false)} />
        </SheetContent>
      </Sheet>
    </>
  );
}
