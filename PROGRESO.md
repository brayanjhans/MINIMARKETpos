# Progreso del proyecto Minimarket POS

> Última actualización: 2026-10-22

## Estado general
| Fase | Descripción | Estado |
|---|---|---|
| 1 | Infraestructura, configuración, modelos, migraciones, seed | ✅ Completada y aprobada |
| 2 | Autenticación, usuarios, roles y permisos (backend + login y layout frontend) | ✅ Completada — esperando revisión del usuario |
| 3 | Productos, categorías e inventario | ⏳ Pendiente |
| 4 | POS y caja | ⏳ Pendiente |
| 5 | Proveedores, compras y clientes | ⏳ Pendiente |
| 6 | Reportes, dashboard y configuración | ⏳ Pendiente |
| 7 | Tests, rendimiento, documentación, Docker | ⏳ Pendiente |

## Fase 1 (completada)
- MySQL 8 local (se cambió de PostgreSQL a pedido del usuario). 48 tablas, migración inicial en `backend/alembic/versions/`.
- Multi-sucursal: sucursales, almacenes, stock_almacen, transferencias, usuario_sucursales.
- 12 mejoras añadidas: presentaciones de producto, afectación IGV (gravado/exonerado/inafecto), ICBPER,
  devoluciones, marcas, historial de precios, producto_proveedor, arqueo por denominación + resumen de cierre,
  parámetros del sistema, bloqueo por intentos de login, ajustes de inventario como documento, correlativos.
- Restricciones en BD: stock no negativo, 1 caja abierta por cajero (columnas generadas + UNIQUE),
  1 almacén de venta por sucursal, no devolver más de lo vendido, etc. 15 pruebas de integridad OK.
- Seed: admin / Admin123*, 3 roles (61 permisos), sucursal "Principal", almacén, Caja 1, series T001/B001/F001.

## Fase 2 (en curso)
### Backend ✅ terminado y probado (41/41 pruebas: `backend/scripts/verificar_fase2.py`)
- 17 rutas: `/api/v1/auth/*` (login, refresh, logout, me, cambiar-sucursal, cambiar-password),
  `/usuarios` (CRUD, restablecer-password, desbloquear, cerrar-sesiones), `/roles` (+ `/roles/permisos`),
  `/auditoria`, `/sucursales`.
- Seguridad: refresh token en cookie httpOnly `mm_refresh` (SameSite strict), rotación con periodo de gracia
  de 30 s y detección de robo; bloqueo tras 5 intentos (parámetro); tokens anteriores a un cambio de
  contraseña quedan inválidos; no se puede desactivar a uno mismo ni dejar el sistema sin administrador.
- Segunda migración `sesiones refresh token`.
- Corregidos 2 bugs de MySQL: redondeo de microsegundos en DATETIME (ahora `FechaHora` los descarta) y
  `eager_defaults` en Base (leer creado_en tras INSERT en async).
- Scripts de verificación en `backend/scripts/` (ejecutar con `PYTHONPATH=.` desde `backend/`).

### Frontend ✅ terminado (tsc OK, `next build` OK, 11/11 pruebas e2e: `backend/scripts/verificar_frontend.py`)
- Next 16.4 + React 19 + TS 5.9 + Tailwind 4 + shadcn/ui (Radix) + TanStack Query 5 / Table 8 + Zustand 5 +
  Framer Motion + zod 4 + react-hook-form.
- `next.config.ts`: rewrite `/api/v1` → backend (8010), cabeceras de seguridad, output standalone.
- `src/proxy.ts` (Next 16 reemplaza middleware.ts, se eliminó el archivo vacío) redirige según la cookie.
- `lib/api.ts`: cliente fetch con renovación automática (una sola a la vez) y errores en español.
- Access token solo en memoria (Zustand); preferencias de UI persistidas (sidebar colapsado).
- Pantallas: login (panel de marca, ver contraseña, aviso Bloq Mayús), layout con sidebar colapsable
  (filtrado por permisos, tooltips) + menú móvil, topbar (sucursal, caja placeholder, tema, usuario),
  cambio de contraseña obligatorio en primer ingreso, dashboard de bienvenida, usuarios (tabla con
  búsqueda/filtros/orden/paginación, crear/editar, restablecer, desbloquear, cerrar sesiones,
  activar/desactivar), roles (matriz de permisos por módulo), auditoría (filtros por módulo y fechas).
  Los demás módulos muestran "Disponible en la Fase N".
- Puertos cambiados a 3010/8010 (3000/8000 los usa otro proyecto del usuario: garantias_seacee).

### Rediseño del frontend (en curso)
- Al usuario **no le gustó** el diseño inicial y pidió usar skills de diseño. Se investigaron y se instalaron en
  `.claude/skills/` (revisadas, licencia MIT, sin tests): `ui-ux-pro-max`, `frontend-design` (Anthropic),
  `web-design-guidelines` (Vercel) y `taste-skill` (modo app: `references/app-screens.md`, `scripts/draw.mjs --app`,
  `scripts/inspect.mjs` toma capturas con Chrome headless).
- taste-skill propuso 2 estilos para "commerce": `achromatic-ledger` (Geist, sin color en la interfaz, todo en tinta)
  y `framed-sheet` (IBM Plex Sans, marco tintado en L + hoja blanca). Hoja guardada en `.taste-skill/direction.json`.
- El usuario eligió **Libro contable** (achromatic-ledger). Le disgustaba: aspecto genérico, colores, distribución.
- ✅ Rediseño hecho: tokens en `globals.css` (fondo piedra #f4f3f1, tinta, acción casi negra, azul #1d5fbf solo
  para datos), Geist + Geist Mono (cifras), sin sombras en reposo, menú plano con píldora gris, barra superior
  sin línea (sucursal · caja | tema · usuario), Inicio con datos reales (franja + actividad de hoy), usuarios con
  pestañas y filas de 2 líneas en celular, roles en patrón de ajustes por módulo, auditoría con acciones en
  palabras, login con ticket térmico dibujado (`components/auth/TicketMuestra.tsx`).
- Notas y crítica: `.taste-skill/notas.md`. Capturas antes/después: `.taste-skill/antes`, `.taste-skill/despues`.
- Script de capturas con sesión: `node frontend/scripts/capturas.mjs <carpeta> [--rutas ...] [--anchos ...] [--oscuro]`.
- **Reglas de diseño para las próximas fases**: seguir `.claude/skills/taste-skill/references/app-screens.md`
  (color solo en datos/estado, KPIs como texto, tablas sin bandas, cifras a la derecha, una acción principal negra,
  nada de tarjetas con íconos en cuadros de color ni MAYÚSCULAS espaciadas). Revisar con capturas.

- ❌ El usuario rechazó también el estilo "Libro contable": "ya no tiene nada de diseño" (demasiado sobrio).
  Quiere más diseño visual (color, gráficos, personalidad) — NO volver al minimalismo gris.
- Se publicó un lienzo con 3 propuestas visuales del Inicio para que elija:
  https://claude.ai/artifact/RiVSdLZGN1pfK3kQtWzZpr — A "Bodega" (azul noche + amarillo, Plus Jakarta Sans),
  B "Fresco" (claro, azul #2563eb + coral, Manrope, sombras suaves), C "Noche" (oscuro, turquesa con brillo, Sora).
  Fuentes locales en el scratchpad (se pierden); si hace falta, rehacer a partir de esta descripción.

- ✅ El usuario eligió **A · Bodega** y pidió bocetos de todas las pantallas en Claude Design. Hechos en el mismo
  lienzo (fila "Estilo Bodega"): Ingreso, Punto de venta, Inicio en celular, Usuarios, Roles y permisos, Auditoría.
  Copias de los archivos de diseño en `diseno/bodega/*.dc.html` (fuente de verdad para implementar).
- Tokens del estilo Bodega: azul noche #14213d (menú y acentos oscuros), amarillo #ffc300 (acción principal e ítem
  activo), fondo #f3f4f8, tarjetas blancas radio 18, Plus Jakarta Sans 400–800, chips de color pastel por
  categoría/rol (amarillo #fff3cc/#8a6700, azul #e4ecff/#2f5bd3, coral #ffe4e1/#c2412f, verde-agua #e0f7f4/#0f7d70,
  lila #f3e8ff/#6b3fa0, naranja #ffe9d6/#b55a00), rojo alerta #d6453a, verde ok #1f9d55.

- ✅ El usuario APROBÓ los bocetos Bodega ("está bien").
- ✅ Backend para datos reales de los bocetos: `GET /api/v1/usuarios/resumen` (con_acceso, sin_acceso, bloqueados,
  ingresaron_hoy) y `GET /api/v1/auditoria/resumen?desde&hasta` (total, ingresos, fallos, cambios, revisar).
  Probados con `backend/scripts/verificar_resumenes.py`; fase 2 sigue 41/41. Ojo MySQL: no usar `FILTER (WHERE…)`.
- ✅ 2026-10-23: **estilo Bodega implementado en el frontend real**: tokens + Plus Jakarta Sans + botón
  (default amarillo, variante `navy`), Sidebar azul noche, Topbar (caja · sucursal | tema · usuario), barra
  inferior en celular con botón amarillo de vender, Login, Inicio (datos reales: ventas S/ 0.00 hasta Fase 4),
  Usuarios (contadores de `/usuarios/resumen`, chips por rol), Roles (tarjetas con barra, interruptores
  amarillos, "N cambios sin guardar"), Auditoría (línea de tiempo + resumen + "Para revisar").
  Verificado: tsc OK, e2e 11/11, capturas claro/oscuro/celular en `.taste-skill/bodega/`.
  Nota técnica: `.tarjeta` va en `@layer components` para que `bg-navy` la pueda sobrescribir.
  Orden sugerido: 1) `globals.css` tokens Bodega + Plus Jakarta Sans en `layout.tsx` (quitar Geist/mono, `.cifra`
  = tabular-nums); 2) Sidebar azul noche con ítem activo amarillo + grupos; Topbar (caja, usuario); barra inferior
  en celular con botón amarillo; 3) Login según `diseno/bodega/Login.dc.html` (borrar `TicketMuestra`);
  4) Inicio (KPIs: ventas S/ 0.00 honestos hasta Fase 4, usuarios reales, actividad de hoy); 5) Usuarios (tarjetas
  con `/usuarios/resumen`, chips por rol, tabla con avatar de color y estado con punto); 6) Roles (tarjetas con barra,
  interruptores amarillos, "N cambios sin guardar"); 7) Auditoría (línea de tiempo + resumen + "Para revisar");
  8) capturas con `node frontend/scripts/capturas.mjs .taste-skill/bodega` y `verificar_frontend.py`.

### Cierre de Fase 2: robustez (en curso, 2026-10-23)
- ✅ 1) Git: repositorio en https://github.com/brayanjhans/MINIMARKETpos (primer commit db3d235).
- ⏳ 2) Pruebas pytest reales (pasar los scripts de `backend/scripts/` a `backend/tests/`).
- ⏳ 3) Límite de intentos de login por IP.
- ⏳ 4) No arrancar en producción con JWT_SECRET por defecto.
- ⏳ 5) Mensajes de error de BD más precisos (ProgrammingError ≠ "error de comunicación").
- ⏳ 6) Frontend: página 404, pantalla de error y aviso cuando el backend está apagado.
- ⏳ 7) Volver a correr `npx next build`.

## Siguiente paso
Completar los puntos 2–7 de arriba. Luego, que el usuario revise el estilo Bodega en http://localhost:3010 (cierra la Fase 2). Si lo aprueba:
**Fase 3 — productos, categorías, marcas e inventario** (stock por almacén, lotes, kardex, ajustes,
transferencias, inventario físico, importar/exportar Excel), con el estilo Bodega y bocetos previos en
Claude Design si son pantallas nuevas. El POS (Fase 4) se implementa con su boceto `diseno/bodega/Pos.dc.html`.
