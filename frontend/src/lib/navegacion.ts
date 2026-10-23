import {
  BarChart3,
  ClipboardList,
  LayoutDashboard,
  type LucideIcon,
  Package,
  ReceiptText,
  ScrollText,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Tags,
  Truck,
  UserCog,
  Users,
  Wallet,
  Warehouse,
} from "lucide-react";

export interface ItemNavegacion {
  titulo: string;
  href: string;
  icono: LucideIcon;
  /** Permiso necesario para ver la opción en el menú */
  permiso: string;
  atajo?: string;
}

export interface GrupoNavegacion {
  titulo: string;
  items: ItemNavegacion[];
}

export const NAVEGACION: GrupoNavegacion[] = [
  {
    titulo: "Tienda",
    items: [
      { titulo: "Inicio", href: "/dashboard", icono: LayoutDashboard, permiso: "dashboard.ver" },
      { titulo: "Punto de venta", href: "/pos", icono: ShoppingCart, permiso: "pos.vender" },
      { titulo: "Caja", href: "/caja", icono: Wallet, permiso: "caja.ver" },
      { titulo: "Tickets", href: "/ventas", icono: ReceiptText, permiso: "pos.vender" },
    ],
  },
  {
    titulo: "Inventario",
    items: [
      { titulo: "Productos", href: "/productos", icono: Package, permiso: "productos.ver" },
      { titulo: "Categorías", href: "/categorias", icono: Tags, permiso: "categorias.ver" },
      { titulo: "Inventario", href: "/inventario", icono: Warehouse, permiso: "inventario.ver" },
    ],
  },
  {
    titulo: "Abastecimiento",
    items: [
      { titulo: "Proveedores", href: "/proveedores", icono: Truck, permiso: "proveedores.ver" },
      { titulo: "Compras", href: "/compras", icono: ClipboardList, permiso: "compras.ver" },
      { titulo: "Clientes", href: "/clientes", icono: Users, permiso: "clientes.ver" },
    ],
  },
  {
    titulo: "Análisis",
    items: [{ titulo: "Reportes", href: "/reportes", icono: BarChart3, permiso: "reportes.ver" }],
  },
  {
    titulo: "Administración",
    items: [
      { titulo: "Usuarios", href: "/usuarios", icono: UserCog, permiso: "usuarios.ver" },
      { titulo: "Roles y permisos", href: "/roles", icono: ShieldCheck, permiso: "roles.ver" },
      { titulo: "Auditoría", href: "/auditoria", icono: ScrollText, permiso: "auditoria.ver" },
      { titulo: "Configuración", href: "/configuracion", icono: Settings, permiso: "configuracion.ver" },
    ],
  },
];

export const TODAS_LAS_RUTAS = NAVEGACION.flatMap((g) => g.items);

export function itemDeRuta(pathname: string): ItemNavegacion | undefined {
  return TODAS_LAS_RUTAS.find((i) => pathname === i.href || pathname.startsWith(`${i.href}/`));
}
