import { useAuthStore } from "@/store/authStore";
import type { ErrorCampo, RespuestaError, TokenRespuesta } from "@/types";

const BASE = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly codigo: string;
  readonly errores: ErrorCampo[];
  readonly datos?: Record<string, unknown>;

  constructor(status: number, cuerpo: Partial<RespuestaError>) {
    super(cuerpo.detalle ?? "Ocurrió un error inesperado");
    this.status = status;
    this.codigo = cuerpo.codigo ?? "error";
    this.errores = cuerpo.errores ?? [];
    this.datos = cuerpo.datos;
  }
}

/** Mensaje legible de cualquier error (incluye el detalle de los campos inválidos). */
export function mensajeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.errores.length) {
      return error.errores.map((e) => (e.campo ? `${e.campo}: ${e.mensaje}` : e.mensaje)).join(" · ");
    }
    return error.message;
  }
  if (error instanceof TypeError) return "No se pudo conectar con el servidor. Verifique su conexión.";
  return error instanceof Error ? error.message : "Ocurrió un error inesperado";
}

async function leerCuerpo(respuesta: Response): Promise<unknown> {
  const texto = await respuesta.text();
  if (!texto) return null;
  try {
    return JSON.parse(texto);
  } catch {
    return { detalle: texto };
  }
}

// Una sola renovación a la vez: si varias peticiones reciben 401 al mismo tiempo, comparten la misma promesa
let renovacionEnCurso: Promise<boolean> | null = null;

export function renovarSesion(): Promise<boolean> {
  renovacionEnCurso ??= (async () => {
    try {
      const respuesta = await fetch(`${BASE}/auth/refresh`, { method: "POST", credentials: "same-origin" });
      if (!respuesta.ok) {
        useAuthStore.getState().limpiar();
        return false;
      }
      useAuthStore.getState().setSesion((await respuesta.json()) as TokenRespuesta);
      return true;
    } catch {
      return false;
    } finally {
      // Se libera en el siguiente ciclo para que las peticiones en espera reutilicen el resultado
      setTimeout(() => (renovacionEnCurso = null), 0);
    }
  })();
  return renovacionEnCurso;
}

type Parametros = Record<string, string | number | boolean | null | undefined>;

interface Opciones {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  params?: Parametros;
  signal?: AbortSignal;
  /** false para endpoints públicos (login) */
  autenticado?: boolean;
}

function construirUrl(ruta: string, params?: Parametros): string {
  const query = new URLSearchParams();
  for (const [clave, valor] of Object.entries(params ?? {})) {
    if (valor !== undefined && valor !== null && valor !== "") query.set(clave, String(valor));
  }
  const qs = query.toString();
  return `${BASE}${ruta}${qs ? `?${qs}` : ""}`;
}

export async function api<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const { method = "GET", body, params, signal, autenticado = true } = opciones;

  const ejecutar = () => {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const token = useAuthStore.getState().accessToken;
    if (autenticado && token) headers.Authorization = `Bearer ${token}`;
    return fetch(construirUrl(ruta, params), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
      signal,
    });
  };

  let respuesta = await ejecutar();

  // Access token vencido: se renueva con la cookie de sesión y se reintenta una vez
  if (respuesta.status === 401 && autenticado) {
    const renovado = await renovarSesion();
    if (renovado) respuesta = await ejecutar();
  }

  const cuerpo = await leerCuerpo(respuesta);
  if (!respuesta.ok) {
    if (respuesta.status === 401 && autenticado) useAuthStore.getState().limpiar();
    throw new ApiError(respuesta.status, (cuerpo ?? {}) as Partial<RespuestaError>);
  }
  return cuerpo as T;
}
