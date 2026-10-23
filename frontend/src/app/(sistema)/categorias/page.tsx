"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { Inicial } from "@/components/comunes/Inicial";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pildora } from "@/components/comunes/Pildora";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";
import { cn, soles } from "@/lib/utils";
import { categoriasService } from "@/services/categorias.service";
import type { Categoria, Marca } from "@/types/productos";

const COLORES = ["#f59e0b", "#3b82f6", "#facc15", "#d97706", "#ec4899", "#06b6d4", "#8b5cf6", "#ef4444", "#f97316", "#22c55e", "#64748b", "#14b8a6"];
const VISIBLES = 9;

export default function CategoriasPage() {
  return (
    <RequierePermiso permiso="categorias.ver">
      <Catalogo />
    </RequierePermiso>
  );
}

function Catalogo() {
  const { tiene } = useAuth();
  const router = useRouter();
  const [verTodas, setVerTodas] = useState(false);
  const [editando, setEditando] = useState<Categoria | "nueva" | null>(null);
  const categorias = useQuery({ queryKey: ["categorias", "todas"], queryFn: () => categoriasService.listar() });
  const ordenadas = [...(categorias.data ?? [])].sort((a, b) => Number(b.activo) - Number(a.activo) || b.productos - a.productos);
  const visibles = verTodas ? ordenadas : ordenadas.slice(0, VISIBLES);
  const verValor = tiene("productos.editar") || tiene("reportes.ganancias");

  return (
    <>
      <PageHeader
        titulo="Categorías y marcas"
        linea="Cómo se ordena el catálogo en el punto de venta y en los reportes"
        acciones={
          tiene("categorias.crear") && (
            <Button onClick={() => setEditando("nueva")}>
              <Plus strokeWidth={2.6} /> Nueva categoría
            </Button>
          )
        }
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="tarjeta p-5">
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <h2 className="text-[15px] font-extrabold">
              Categorías <span className="text-muted-foreground tabular">{categorias.data?.length ?? ""}</span>
            </h2>
            {ordenadas.length > VISIBLES && (
              <button type="button" className="text-[13px] font-bold hover:underline" onClick={() => setVerTodas((v) => !v)}>
                {verTodas ? `Ver solo las ${VISIBLES} principales` : `Ver las ${ordenadas.length}`}
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {categorias.isLoading &&
              Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-[92px] rounded-2xl" />)}
            {visibles.map((c) => (
              <div
                key={c.id}
                className={cn("group relative rounded-2xl p-4", !c.activo && "opacity-60")}
                style={{ background: `color-mix(in oklab, ${c.color ?? "#8a93a6"} 14%, var(--card))` }}
              >
                <button
                  type="button"
                  onClick={() => router.push(`/productos?categoria=${c.id}`)}
                  className="block w-full text-left focus-visible:outline-none"
                >
                  <span aria-hidden className="mb-2 block h-1.5 w-8 rounded-full" style={{ background: c.color ?? "#8a93a6" }} />
                  <span className="block font-bold">{c.nombre}</span>
                  <span className="block text-[13px] text-muted-foreground tabular">
                    {c.productos} producto{c.productos === 1 ? "" : "s"}
                    {verValor && Number(c.valor_inventario) > 0 && ` · ${soles(c.valor_inventario)}`}
                  </span>
                </button>
                {!c.activo && <Pildora className="absolute top-3 right-3">Inactiva</Pildora>}
                {tiene("categorias.editar") && (
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    className="absolute right-2 bottom-2 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                    aria-label={`Editar ${c.nombre}`}
                    onClick={() => setEditando(c)}
                  >
                    <Pencil />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </section>

        <Marcas />
      </div>

      <CategoriaDialog categoria={editando} onCerrar={() => setEditando(null)} />
    </>
  );
}

function Marcas() {
  const { tiene } = useAuth();
  const queryClient = useQueryClient();
  const [busqueda, setBusqueda] = useState("");
  const [verTodas, setVerTodas] = useState(false);
  const [editando, setEditando] = useState<Marca | "nueva" | null>(null);
  const marcas = useQuery({ queryKey: ["marcas", "todas"], queryFn: () => categoriasService.marcas() });
  const filtradas = (marcas.data ?? [])
    .filter((m) => m.nombre.toLowerCase().includes(busqueda.trim().toLowerCase()))
    .sort((a, b) => b.productos - a.productos || a.nombre.localeCompare(b.nombre));
  const visibles = verTodas || busqueda ? filtradas : filtradas.slice(0, 8);

  const guardar = useMutation({
    mutationFn: ({ nombre, activo }: { nombre: string; activo: boolean }) =>
      editando === "nueva"
        ? categoriasService.crearMarca(nombre)
        : categoriasService.actualizarMarca((editando as Marca).id, { nombre, activo }),
    onSuccess: () => {
      toast.success("Marca guardada");
      setEditando(null);
      void queryClient.invalidateQueries({ queryKey: ["marcas"] });
    },
    onError: (error) => toast.error(mensajeError(error)),
  });

  return (
    <section className="tarjeta p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-[15px] font-extrabold">
          Marcas <span className="text-muted-foreground tabular">{marcas.data?.length ?? ""}</span>
        </h2>
        {tiene("marcas.crear") && (
          <button type="button" className="text-[13px] font-bold hover:underline" onClick={() => setEditando("nueva")}>
            + Nueva marca
          </button>
        )}
      </div>
      <label className="mb-2 flex h-[38px] items-center gap-2 rounded-[10px] bg-muted px-3 text-muted-foreground">
        <Search className="size-4 flex-none" />
        <input
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar marca"
          aria-label="Buscar marca"
          className="w-full bg-transparent text-sm text-foreground outline-none"
        />
      </label>
      <ul>
        {visibles.map((m) => (
          <li key={m.id} className={cn("flex items-center gap-3 border-b border-rule py-2 last:border-0", !m.activo && "opacity-60")}>
            <Inicial id={m.id} nombre={m.nombre} className="size-8 rounded-[10px]" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold">{m.nombre}</p>
              <p className="text-xs text-muted-foreground tabular">
                {m.productos} producto{m.productos === 1 ? "" : "s"}
                {!m.activo && " · inactiva"}
              </p>
            </div>
            {tiene("marcas.editar") && (
              <Button variant="ghost" size="icon-sm" aria-label={`Editar ${m.nombre}`} onClick={() => setEditando(m)}>
                <Pencil />
              </Button>
            )}
          </li>
        ))}
        {marcas.data && visibles.length === 0 && (
          <li className="py-6 text-center text-sm text-muted-foreground">
            {busqueda ? `Ninguna marca coincide con «${busqueda}»` : "Aún no hay marcas"}
          </li>
        )}
      </ul>
      {!busqueda && filtradas.length > 8 && (
        <button type="button" className="mt-2 text-[13px] font-bold hover:underline" onClick={() => setVerTodas((v) => !v)}>
          {verTodas ? "Ver menos" : `Ver las ${filtradas.length} marcas`}
        </button>
      )}
      <MarcaDialog
        marca={editando}
        onCerrar={() => setEditando(null)}
        onGuardar={(nombre, activo) => guardar.mutate({ nombre, activo })}
        guardando={guardar.isPending}
      />
    </section>
  );
}

function MarcaDialog({
  marca,
  onCerrar,
  onGuardar,
  guardando,
}: {
  marca: Marca | "nueva" | null;
  onCerrar: () => void;
  onGuardar: (nombre: string, activo: boolean) => void;
  guardando: boolean;
}) {
  const [nombre, setNombre] = useState("");
  const [activo, setActivo] = useState(true);
  useEffect(() => {
    if (marca) {
      setNombre(marca === "nueva" ? "" : marca.nombre);
      setActivo(marca === "nueva" ? true : marca.activo);
    }
  }, [marca]);
  return (
    <Dialog open={marca !== null} onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="sm:max-w-sm">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (nombre.trim()) onGuardar(nombre.trim(), activo);
          }}
        >
          <DialogHeader>
            <DialogTitle>{marca === "nueva" ? "Nueva marca" : "Editar marca"}</DialogTitle>
            <DialogDescription>Las marcas ayudan a buscar y a ver reportes por proveedor.</DialogDescription>
          </DialogHeader>
          <div className="my-4 flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="marca-nombre">Nombre</Label>
              <Input id="marca-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={80} autoFocus />
            </div>
            {marca !== "nueva" && (
              <label className="flex items-center justify-between text-sm font-semibold">
                Activa
                <Switch checked={activo} onCheckedChange={setActivo} />
              </label>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCerrar}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!nombre.trim() || guardando}>
              Guardar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function CategoriaDialog({ categoria, onCerrar }: { categoria: Categoria | "nueva" | null; onCerrar: () => void }) {
  const { tiene } = useAuth();
  const queryClient = useQueryClient();
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [color, setColor] = useState(COLORES[0]!);
  const [activo, setActivo] = useState(true);
  const [confirmarBorrado, setConfirmarBorrado] = useState(false);

  useEffect(() => {
    if (!categoria) return;
    const c = categoria === "nueva" ? null : categoria;
    setNombre(c?.nombre ?? "");
    setDescripcion(c?.descripcion ?? "");
    setColor(c?.color ?? COLORES[0]!);
    setActivo(c?.activo ?? true);
    setConfirmarBorrado(false);
  }, [categoria]);

  const terminar = (mensaje: string) => {
    toast.success(mensaje);
    void queryClient.invalidateQueries({ queryKey: ["categorias"] });
    void queryClient.invalidateQueries({ queryKey: ["productos"] });
    onCerrar();
  };
  const guardar = useMutation({
    mutationFn: () => {
      const datos = { nombre: nombre.trim(), descripcion: descripcion.trim() || null, color };
      return categoria === "nueva"
        ? categoriasService.crear(datos)
        : categoriasService.actualizar((categoria as Categoria).id, { ...datos, activo });
    },
    onSuccess: () => terminar("Categoría guardada"),
    onError: (error) => toast.error(mensajeError(error)),
  });
  const eliminar = useMutation({
    mutationFn: () => categoriasService.eliminar((categoria as Categoria).id),
    onSuccess: () => terminar("Categoría eliminada"),
    onError: (error) => toast.error(mensajeError(error)),
  });

  return (
    <Dialog open={categoria !== null} onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (nombre.trim().length >= 2) guardar.mutate();
          }}
        >
          <DialogHeader>
            <DialogTitle>{categoria === "nueva" ? "Nueva categoría" : "Editar categoría"}</DialogTitle>
            <DialogDescription>El color identifica la categoría en las listas y en el punto de venta.</DialogDescription>
          </DialogHeader>
          <div className="my-4 flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cat-nombre">Nombre</Label>
              <Input id="cat-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={80} autoFocus />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cat-desc">Descripción</Label>
              <Input id="cat-desc" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} maxLength={250} placeholder="Opcional" />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">Color</span>
              <div role="radiogroup" aria-label="Color" className="flex flex-wrap gap-2">
                {COLORES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    role="radio"
                    aria-checked={color === c}
                    aria-label={c}
                    onClick={() => setColor(c)}
                    className={cn("size-8 rounded-full ring-offset-2 ring-offset-background", color === c && "ring-2 ring-foreground")}
                    style={{ background: c }}
                  />
                ))}
              </div>
            </div>
            {categoria !== "nueva" && (
              <label className="flex items-center justify-between text-sm font-semibold">
                Activa (aparece al crear productos)
                <Switch checked={activo} onCheckedChange={setActivo} />
              </label>
            )}
          </div>
          <DialogFooter className="gap-2 sm:justify-between">
            {categoria !== "nueva" && categoria && tiene("categorias.eliminar") ? (
              <Button
                type="button"
                variant="ghost"
                className="text-destructive"
                disabled={eliminar.isPending}
                onClick={() => (confirmarBorrado ? eliminar.mutate() : setConfirmarBorrado(true))}
              >
                {confirmarBorrado ? "¿Seguro? Eliminar" : "Eliminar"}
              </Button>
            ) : (
              <span />
            )}
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onCerrar}>
                Cancelar
              </Button>
              <Button type="submit" disabled={nombre.trim().length < 2 || guardar.isPending}>
                Guardar
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
