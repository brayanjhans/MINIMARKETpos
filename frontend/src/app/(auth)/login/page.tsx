"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, Barcode, CreditCard, Eye, EyeOff, Loader2, Package } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Marca } from "@/components/comunes/Marca";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { mensajeError } from "@/lib/api";

const esquema = z.object({
  username: z.string().trim().min(1, "Escribe tu usuario"),
  password: z.string().min(1, "Escribe tu contraseña"),
});
type Datos = z.infer<typeof esquema>;

const VENTAJAS = [
  { icono: Barcode, titulo: "Lector de códigos y atajos", texto: "F2 buscar, F4 cobrar. Todo con el teclado." },
  { icono: Package, titulo: "Stock en tiempo real", texto: "Por sucursal, con lotes y fechas de vencimiento." },
  { icono: CreditCard, titulo: "Efectivo, Yape, Plin y tarjeta", texto: "Con cálculo del vuelto y cierre de caja." },
];

export default function LoginPage() {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[600px_1fr]">
      <PanelMarca />
      <div className="flex flex-col items-center justify-center bg-background px-5 py-10">
        <Marca className="mb-8 lg:hidden" />
        <Suspense>
          <FormularioIngreso />
        </Suspense>
      </div>
    </div>
  );
}

function PanelMarca() {
  return (
    <section className="relative hidden flex-col overflow-hidden bg-navy px-14 py-12 text-white lg:flex">
      {/* Círculos de marca (decoración) */}
      <div aria-hidden className="absolute -top-32 -right-32 size-96 rounded-full bg-amarillo opacity-[0.12]" />
      <div aria-hidden className="absolute right-16 -bottom-40 size-72 rounded-full border-[44px] border-amarillo opacity-[0.08]" />

      <Marca claro className="relative" />
      <h2 className="relative mt-auto text-[46px] leading-[1.08] font-extrabold tracking-[-0.035em]">
        Vende rápido.
        <br />
        <span className="text-amarillo">Controla todo.</span>
      </h2>
      <p className="relative mt-4 mb-9 max-w-md text-base leading-relaxed text-[#c3cbe0]">
        La caja, el inventario y la administración de tu minimarket en un solo lugar.
      </p>
      <ul className="relative space-y-[18px]">
        {VENTAJAS.map(({ icono: Icono, titulo, texto }) => (
          <li key={titulo} className="flex items-start gap-3.5">
            <span className="grid size-10 flex-none place-items-center rounded-[12px] bg-navy-2">
              <Icono className="size-5 text-amarillo" aria-hidden />
            </span>
            <span>
              <span className="block font-bold">{titulo}</span>
              <span className="block text-sm text-navy-ink">{texto}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function FormularioIngreso() {
  const router = useRouter();
  const parametros = useSearchParams();
  const { login } = useAuth();
  const [verPassword, setVerPassword] = useState(false);
  const [mayusculas, setMayusculas] = useState(false);
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Datos>({ resolver: zodResolver(esquema) });

  const enviar = async ({ username, password }: Datos) => {
    try {
      await login(username, password);
      const siguiente = parametros.get("siguiente");
      // Solo rutas internas (evita redirigir a otros sitios)
      router.replace(siguiente?.startsWith("/") && !siguiente.startsWith("//") ? siguiente : "/dashboard");
    } catch (error) {
      setError("root", { message: mensajeError(error) });
    }
  };

  const detectarMayusculas = (e: React.KeyboardEvent) => setMayusculas(e.getModifierState("CapsLock"));

  return (
    <form
      onSubmit={handleSubmit(enviar)}
      noValidate
      className="flex w-full max-w-[400px] flex-col gap-[18px] rounded-[24px] bg-card p-7 sm:p-10"
    >
      <div>
        <h1 className="text-[28px] leading-9 font-extrabold tracking-[-0.02em]">Ingresar</h1>
        <p className="mt-1.5 text-[15px] text-muted-foreground">Usa tu usuario y contraseña de la tienda.</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="username" className="font-semibold">
          Usuario
        </Label>
        <Input
          id="username"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          autoFocus
          className="h-12 rounded-[12px] border-[1.5px] text-[15px]"
          aria-invalid={!!errors.username}
          {...register("username")}
        />
        {errors.username && <p className="text-xs font-medium text-destructive">{errors.username.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password" className="font-semibold">
          Contraseña
        </Label>
        <div className="relative">
          <Input
            id="password"
            type={verPassword ? "text" : "password"}
            autoComplete="current-password"
            className="h-12 rounded-[12px] border-[1.5px] pr-12 text-[15px]"
            aria-invalid={!!errors.password}
            onKeyUp={detectarMayusculas}
            onKeyDown={detectarMayusculas}
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setVerPassword((v) => !v)}
            className="absolute inset-y-0 right-0 grid w-12 place-items-center rounded-r-[12px] text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            aria-label={verPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
          >
            {verPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
          </button>
        </div>
        {errors.password && <p className="text-xs font-medium text-destructive">{errors.password.message}</p>}
      </div>

      {mayusculas && (
        <p className="flex items-center gap-2 rounded-[10px] bg-aviso-fondo px-3 py-2.5 text-[13px] font-semibold text-amarillo-tinta">
          <AlertTriangle className="size-4" /> Las mayúsculas están activadas
        </p>
      )}

      {errors.root && (
        <p role="alert" className="rounded-[10px] bg-pill-negative-bg px-3 py-2.5 text-sm font-semibold text-pill-negative-ink">
          {errors.root.message}
        </p>
      )}

      <Button type="submit" className="h-[50px] rounded-[12px] text-base font-extrabold" disabled={isSubmitting}>
        {isSubmitting && <Loader2 className="animate-spin" />}
        {isSubmitting ? "Ingresando…" : "Ingresar"}
      </Button>
      <p className="text-center text-[13px] text-muted-foreground">
        ¿Olvidaste tu contraseña? Pide una temporal al administrador.
      </p>
    </form>
  );
}
