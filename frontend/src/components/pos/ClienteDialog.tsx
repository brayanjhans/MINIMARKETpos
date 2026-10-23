"use client";

import { useQuery } from "@tanstack/react-query";
import { Loader2, Search, UserPlus, UserRound, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { mensajeError } from "@/lib/api";
import { cn, soles } from "@/lib/utils";
import { clientesService } from "@/services/clientes.service";
import type { Cliente, TipoDocumento } from "@/types/ventas";

interface Props {
  abierto: boolean;
  actual: Cliente | null;
  onElegir: (cliente: Cliente | null) => void;
  onCerrar: () => void;
}

const DOCUMENTOS: { valor: TipoDocumento; texto: string }[] = [
  { valor: "DNI", texto: "DNI" },
  { valor: "RUC", texto: "RUC" },
  { valor: "CARNET_EXTRANJERIA", texto: "Carné de extranjería" },
  { valor: "PASAPORTE", texto: "Pasaporte" },
  { valor: "SIN_DOCUMENTO", texto: "Sin documento" },
];

export function ClienteDialog({ abierto, actual, onElegir, onCerrar }: Props) {
  const { tiene } = useAuth();
  const [texto, setTexto] = useState("");
  const [nuevo, setNuevo] = useState(false);
  const busqueda = useDebounce(texto.trim(), 200);
  const lista = useQuery({
    queryKey: ["clientes", "buscar", busqueda],
    queryFn: ({ signal }) => clientesService.buscar(busqueda, signal),
    enabled: abierto && !nuevo,
    staleTime: 10_000,
  });

  const elegir = (c: Cliente | null) => {
    onElegir(c);
    setTexto("");
    setNuevo(false);
  };

  return (
    <Dialog open={abierto} onOpenChange={(a) => !a && (setNuevo(false), onCerrar())}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{nuevo ? "Nuevo cliente" : "Cliente de la venta"}</DialogTitle>
          <DialogDescription>
            {nuevo ? "Lo justo para identificarlo; el resto se completa en Clientes." : "Busca por DNI, RUC o nombre."}
          </DialogDescription>
        </DialogHeader>
        {nuevo ? (
          <NuevoCliente inicial={texto} onCreado={elegir} onVolver={() => setNuevo(false)} />
        ) : (
          <div className="flex flex-col gap-3">
            <div className="relative">
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="DNI, RUC o nombre"
                className="h-11 pl-9"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter" && lista.data?.length) {
                    e.preventDefault();
                    elegir(lista.data[0]!);
                  }
                }}
              />
            </div>
            <ul className="scrollbar-fino max-h-72 overflow-y-auto">
              <li>
                <button
                  type="button"
                  onClick={() => elegir(null)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-muted",
                    !actual && "bg-aviso-fondo",
                  )}
                >
                  <UserRound className="size-4 text-muted-foreground" />
                  <span className="font-bold">Varios</span>
                  <span className="text-[13px] text-muted-foreground">cliente sin identificar</span>
                </button>
              </li>
              {lista.isLoading && (
                <li className="flex justify-center py-4">
                  <Loader2 className="size-5 animate-spin text-muted-foreground" />
                </li>
              )}
              {lista.data?.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => elegir(c)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-muted",
                      actual?.id === c.id && "bg-aviso-fondo",
                    )}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-bold">{c.nombre}</span>
                      <span className="block text-xs text-muted-foreground tabular">
                        {c.numero_documento ? `${c.tipo_documento} ${c.numero_documento}` : "Sin documento"}
                        {c.permite_credito && ` · fía hasta ${Number(c.limite_credito) > 0 ? soles(c.limite_credito) : "sin tope"}`}
                      </span>
                    </span>
                    {Number(c.deuda) > 0 && (
                      <span className="text-xs font-bold text-destructive tabular">debe {soles(c.deuda)}</span>
                    )}
                  </button>
                </li>
              ))}
              {lista.data?.length === 0 && busqueda && (
                <li className="px-3 py-4 text-center text-sm text-muted-foreground">No hay clientes con «{busqueda}»</li>
              )}
            </ul>
            {tiene("clientes.crear") && (
              <Button variant="outline" onClick={() => setNuevo(true)}>
                <UserPlus /> Nuevo cliente
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function NuevoCliente({
  inicial,
  onCreado,
  onVolver,
}: {
  inicial: string;
  onCreado: (c: Cliente) => void;
  onVolver: () => void;
}) {
  const { tiene } = useAuth();
  const esNumero = /^\d+$/.test(inicial.trim());
  const [tipo, setTipo] = useState<TipoDocumento>(inicial.trim().length === 11 ? "RUC" : "DNI");
  const [numero, setNumero] = useState(esNumero ? inicial.trim() : "");
  const [nombre, setNombre] = useState(esNumero ? "" : inicial.trim());
  const [telefono, setTelefono] = useState("");
  const [fia, setFia] = useState(false);
  const [limite, setLimite] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const crear = async (e: React.FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      onCreado(
        await clientesService.crear({
          tipo_documento: tipo,
          numero_documento: tipo === "SIN_DOCUMENTO" ? null : numero.trim(),
          nombre: nombre.trim(),
          telefono: telefono.trim() || null,
          permite_credito: fia,
          limite_credito: fia && limite.trim() ? limite.trim().replace(",", ".") : "0",
        }),
      );
    } catch (err) {
      setError(mensajeError(err));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={crear} className="flex flex-col gap-3">
      <div className="grid grid-cols-[150px_1fr] gap-2">
        <div className="flex flex-col gap-1.5">
          <Label>Documento</Label>
          <Select value={tipo} onValueChange={(v) => setTipo(v as TipoDocumento)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DOCUMENTOS.map((d) => (
                <SelectItem key={d.valor} value={d.valor}>
                  {d.texto}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cli-numero">Número</Label>
          <Input
            id="cli-numero"
            value={numero}
            onChange={(e) => setNumero(e.target.value)}
            disabled={tipo === "SIN_DOCUMENTO"}
            inputMode={tipo === "DNI" || tipo === "RUC" ? "numeric" : "text"}
            maxLength={15}
            className="tabular"
            autoFocus={!numero}
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="cli-nombre">Nombre o razón social</Label>
        <Input id="cli-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={200} autoFocus={!!numero} />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="cli-tel">Teléfono (opcional)</Label>
        <Input id="cli-tel" value={telefono} onChange={(e) => setTelefono(e.target.value)} maxLength={20} inputMode="tel" />
      </div>
      {tiene("clientes.editar") && (
        <div className="flex items-end gap-3 rounded-xl bg-muted p-3">
          <label className="flex flex-1 items-center gap-2 text-sm font-semibold">
            <input type="checkbox" checked={fia} onChange={(e) => setFia(e.target.checked)} className="size-4 accent-navy" />
            Se le puede fiar
          </label>
          {fia && (
            <div className="flex flex-col gap-1">
              <Label htmlFor="cli-limite" className="text-xs">
                Límite (vacío = sin tope)
              </Label>
              <Input id="cli-limite" value={limite} onChange={(e) => setLimite(e.target.value)} inputMode="decimal" className="h-9 w-28 tabular" placeholder="0.00" />
            </div>
          )}
        </div>
      )}
      {error && <p className="rounded-xl bg-pill-negative-bg px-3 py-2 text-sm font-semibold text-pill-negative-ink">{error}</p>}
      <div className="flex justify-between gap-2">
        <Button type="button" variant="ghost" onClick={onVolver}>
          <X /> Volver
        </Button>
        <Button type="submit" disabled={enviando || nombre.trim().length < 2}>
          {enviando && <Loader2 className="animate-spin" />} Crear y elegir
        </Button>
      </div>
    </form>
  );
}
