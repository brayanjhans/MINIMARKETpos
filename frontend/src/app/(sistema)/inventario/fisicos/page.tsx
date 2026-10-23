"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { RequierePermiso } from "@/components/auth/RequierePermiso";
import { DataTable, type MetaColumna } from "@/components/comunes/DataTable";
import { PageHeader } from "@/components/comunes/PageHeader";
import { Pildora } from "@/components/comunes/Pildora";
import { NavInventario } from "@/components/inventario/NavInventario";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError, nuevaClave } from "@/lib/api";
import { ESTADOS_FISICO } from "@/lib/inventario";
import { recencia, soles } from "@/lib/utils";
import { categoriasService } from "@/services/categorias.service";
import { inventarioService } from "@/services/inventario.service";
import type { FisicoListado } from "@/types/inventario";

const TAMANIO = 20;
const TODO = "todo";

export default function FisicosPage() {
  return (
    <RequierePermiso permiso="inventario.ver">
      <Fisicos />
    </RequierePermiso>
  );
}

function Fisicos() {
  const { tiene } = useAuth();
  const [pagina, setPagina] = useState(1);
  const [nuevo, setNuevo] = useState(false);
  const lista = useQuery({
    queryKey: ["inventario", "fisicos", pagina],
    queryFn: () => inventarioService.fisicos({ pagina, tamanio: TAMANIO }),
    placeholderData: keepPreviousData,
  });

  const columnas = useMemo<ColumnDef<FisicoListado, unknown>[]>(
    () => [
      {
        id: "numero",
        header: "Conteo",
        cell: ({ row: { original: f } }) => (
          <Link href={`/inventario/fisicos/${f.id}`} className="group block">
            <p className="font-bold group-hover:underline">{f.descripcion || "Conteo"}</p>
            <p className="text-xs text-muted-foreground tabular">
              {f.numero} · {f.usuario} · {recencia(f.creado_en)}
            </p>
          </Link>
        ),
      },
      {
        id: "estado",
        header: "Estado",
        cell: ({ row }) => <Pildora tono={ESTADOS_FISICO[row.original.estado].tono}>{ESTADOS_FISICO[row.original.estado].texto}</Pildora>,
      },
      {
        id: "avance",
        header: "Contados",
        meta: { className: "hidden sm:table-cell" } satisfies MetaColumna,
        cell: ({ row: { original: f } }) => (
          <div className="w-36">
            <p className="text-xs font-semibold tabular">
              {f.contadas} de {f.total_lineas}
            </p>
            <div className="mt-1 h-1.5 rounded-full bg-muted">
              <div className="h-1.5 rounded-full bg-primary" style={{ width: `${(f.contadas / Math.max(f.total_lineas, 1)) * 100}%` }} />
            </div>
          </div>
        ),
      },
      {
        id: "diferencia",
        header: "Diferencia",
        meta: { numero: true } satisfies MetaColumna,
        cell: ({ row: { original: f } }) => {
          if (f.valor_faltante === null) return `${f.con_diferencia} línea(s)`;
          const neto = Number(f.valor_sobrante) - Number(f.valor_faltante);
          return <b className={neto < 0 ? "text-destructive" : neto > 0 ? "text-positive" : ""}>{neto === 0 ? "—" : soles(neto)}</b>;
        },
      },
    ],
    [],
  );

  return (
    <>
      <PageHeader
        titulo="Inventario físico"
        linea="Contar lo que hay en el almacén y corregir solo las diferencias"
        acciones={
          tiene("inventario.inventario_fisico") && (
            <Button onClick={() => setNuevo(true)}>
              <Plus strokeWidth={2.6} /> Nuevo conteo
            </Button>
          )
        }
      />
      <NavInventario />
      <DataTable
        columnas={columnas}
        datos={lista.data?.items}
        cargando={lista.isLoading}
        total={lista.data?.total ?? 0}
        pagina={pagina}
        tamanio={TAMANIO}
        onPagina={setPagina}
        vacio="Aún no hay conteos. Empieza por una categoría pequeña, por ejemplo Bebidas."
      />
      <NuevoConteo abierto={nuevo} onCerrar={() => setNuevo(false)} />
    </>
  );
}

function NuevoConteo({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [clave] = useState(nuevaClave);
  const [categoria, setCategoria] = useState(TODO);
  const [descripcion, setDescripcion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const categorias = useQuery({ queryKey: ["categorias"], queryFn: () => categoriasService.listar(true), enabled: abierto });

  const crear = useMutation({
    mutationFn: () => {
      const elegida = categorias.data?.find((c) => String(c.id) === categoria);
      return inventarioService.crearFisico(
        {
          categoria_id: elegida?.id ?? null,
          descripcion: descripcion.trim() || (elegida ? `Conteo de ${elegida.nombre}` : "Conteo general"),
        },
        clave,
      );
    },
    onSuccess: (f) => {
      void queryClient.invalidateQueries({ queryKey: ["inventario"] });
      router.push(`/inventario/fisicos/${f.id}`);
    },
    onError: (e) => setError(mensajeError(e)),
  });

  return (
    <Dialog open={abierto} onOpenChange={(a) => !a && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuevo conteo</DialogTitle>
          <DialogDescription>
            Se guarda el stock de este momento. Puedes seguir vendiendo: al final solo se corrige la diferencia contada.
          </DialogDescription>
        </DialogHeader>
        <div className="my-2 flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Qué se cuenta</Label>
            <Select value={categoria} onValueChange={setCategoria}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODO}>Todo el almacén</SelectItem>
                {(categorias.data ?? []).map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.nombre} ({c.productos})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="desc-conteo">Nombre del conteo</Label>
            <Input id="desc-conteo" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} maxLength={200} placeholder="Opcional, ej. Conteo de fin de mes" />
          </div>
          {error && <p className="rounded-xl bg-pill-negative-bg px-3 py-2 text-sm font-semibold text-pill-negative-ink">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>
            Cancelar
          </Button>
          <Button disabled={crear.isPending} onClick={() => crear.mutate()}>
            Empezar a contar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
