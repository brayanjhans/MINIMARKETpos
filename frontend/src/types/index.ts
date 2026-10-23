// Tipos compartidos que reflejan los esquemas del backend (app/schemas)

export interface Pagina<T> {
  items: T[];
  total: number;
  pagina: number;
  tamanio: number;
  paginas: number;
}

export interface ErrorCampo {
  campo: string | null;
  mensaje: string;
}

export interface RespuestaError {
  detalle: string;
  codigo: string;
  errores?: ErrorCampo[];
  datos?: Record<string, unknown>;
}

export interface SucursalResumen {
  id: number;
  codigo: string;
  nombre: string;
}

export interface RolResumen {
  id: number;
  nombre: string;
}

// ---------- Autenticación ----------
export interface UsuarioSesion {
  id: number;
  nombre_completo: string;
  username: string;
  email: string | null;
  rol: RolResumen;
  permisos: string[];
  sucursales: SucursalResumen[];
  sucursal_actual: SucursalResumen;
  debe_cambiar_password: boolean;
}

export interface TokenRespuesta {
  access_token: string;
  token_type: "bearer";
  expira_en: number;
  usuario: UsuarioSesion;
}

// ---------- Usuarios ----------
export interface UsuarioListado {
  id: number;
  nombre_completo: string;
  username: string;
  email: string | null;
  rol: RolResumen;
  activo: boolean;
  bloqueado_hasta: string | null;
  ultimo_acceso: string | null;
  sucursales: SucursalResumen[];
  creado_en: string;
}

export interface UsuarioDetalle extends UsuarioListado {
  sucursal_predeterminada_id: number | null;
  debe_cambiar_password: boolean;
  intentos_fallidos: number;
}

export interface ResumenUsuarios {
  con_acceso: number;
  sin_acceso: number;
  bloqueados: number;
  ingresaron_hoy: number;
}

export interface UsuarioCrear {
  nombre_completo: string;
  username: string;
  email: string | null;
  password: string;
  rol_id: number;
  sucursal_ids: number[];
  sucursal_predeterminada_id: number | null;
  debe_cambiar_password: boolean;
}

export type UsuarioActualizar = Partial<
  Pick<UsuarioCrear, "nombre_completo" | "email" | "rol_id" | "sucursal_ids" | "sucursal_predeterminada_id">
> & { activo?: boolean };

// ---------- Roles ----------
export interface RolListado {
  id: number;
  nombre: string;
  descripcion: string | null;
  es_sistema: boolean;
  activo: boolean;
  total_usuarios: number;
  total_permisos: number;
}

export interface RolDetalle {
  id: number;
  nombre: string;
  descripcion: string | null;
  es_sistema: boolean;
  activo: boolean;
  permisos: string[];
  creado_en: string;
}

export interface PermisoItem {
  codigo: string;
  accion: string;
  descripcion: string;
}

export interface ModuloPermisos {
  modulo: string;
  etiqueta: string;
  permisos: PermisoItem[];
}

// ---------- Auditoría ----------
export interface AuditoriaItem {
  id: number;
  usuario_id: number | null;
  usuario_nombre: string | null;
  sucursal_id: number | null;
  accion: string;
  modulo: string;
  entidad: string | null;
  entidad_id: string | null;
  descripcion: string | null;
  datos: Record<string, unknown> | null;
  ip: string | null;
  creado_en: string;
}

export interface ResumenAuditoria {
  total: number;
  ingresos: number;
  fallos: number;
  cambios: number;
  revisar: { usuario_id: number; nombre: string; intentos_fallidos: number } | null;
}

export interface Mensaje {
  mensaje: string;
}
