# Progreso del proyecto Minimarket POS

> Última actualización: 2026-10-22

## Estado general
| Fase | Descripción | Estado |
|---|---|---|
| 1 | Infraestructura, configuración, modelos, migraciones, seed | ✅ Completada y aprobada |
| 2 | Autenticación, usuarios, roles y permisos (backend + login y layout frontend) | ✅ Completada y aprobada |
| 3 | Productos, categorías e inventario | ✅ Completada y aprobada |
| 4 | POS y caja | 🔄 En curso |
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
- ✅ 2) pytest: 38 pruebas en `backend/tests/` (auth, usuarios, roles, auditoría, integridad de BD, configuración)
  sobre la base `minimarket_test` que se recrea en cada corrida. Se borraron los scripts verificar_fase1/2/resumenes.
- ✅ 3) Límite por IP: cuenta LOGIN_FALLIDO de la IP en la auditoría (parámetros `seguridad.max_intentos_ip`=20 y
  `seguridad.minutos_ventana_ip`=15) → 429 `limite_ip`. Migración con índice `ix_auditoria_ip_accion_fecha`.
- ✅ 4) En producción no arranca si JWT_SECRET es el de ejemplo o < 32 caracteres, si COOKIE_SECURE=false o DEBUG=true.
- ✅ 5) Errores de BD: solo los de conexión dan 503 "no se pudo conectar"; los demás 500 "error interno".
- ✅ 6) Frontend: `app/not-found.tsx` (404), `app/(sistema)/error.tsx`, `app/global-error.tsx`; si el backend no
  responde ya NO se cierra la sesión: estado `sin_conexion` con pantalla "Sin conexión con el servidor" + Reintentar,
  y un solo aviso (toast) para consultas que fallan por falta de conexión (`lib/api.ts`, `providers.tsx`).
- ✅ 7) `npx next build` OK (18 rutas). e2e 11/11. pytest 38/38.

## Fase 3 (en curso)
- ✅ Bocetos en Claude Design (mismo lienzo, sección "Fase 3"; copias en `diseno/fase3/`): Productos (lista con
  contadores, filtros por categoría, margen, stock bajo), Producto (datos, precio con ganancia calculada, IGV
  gravado/exonerado/inafecto, ICBPER, presentaciones, stock mínimo, lotes, imagen, stock por almacén, historial de
  precios), Categorías y marcas, Inventario (valor, stock bajo, por vencer, mermas del mes, lotes por vencer),
  Kardex (saldo por movimiento), Nuevo ajuste/merma (motivos, lotes, pérdida total), Inventario físico (conteo con
  escáner, diferencias y valor). Datos de ejemplo verificados (márgenes, valores y saldos cuadran).
- Revisión de robustez (2026-10-23). DECISIONES del usuario y reglas acordadas:
  * **Vender sin stock: SÍ, con permiso** `pos.vender_sin_stock` (solo Administrador por defecto, auditado).
    Solo las VENTAS pueden dejar `stock_almacen.cantidad` negativo (quitar el CHECK ≥ 0 de esa columna con
    migración); ajustes/mermas/transferencias nunca. Los lotes nunca negativos. Alerta "stock negativo por
    regularizar" en Inventario. Reemplaza al parámetro `ventas.permitir_sin_stock` (quitarlo).
  * **Fotos: SÍ, siempre lo más livianas posible** (pedido explícito del usuario): se aceptan JPG/PNG/WEBP/HEIC
    hasta 10 MB y el servidor SIEMPRE las convierte a **WEBP**: corrige orientación EXIF, máx. 800 px (calidad ~75,
    objetivo 30–60 KB) + miniatura 160 px (~5–10 KB) para listas y POS; se eliminan metadatos EXIF/GPS.
    Pillow (+ pillow-heif para HEIC). Servir con caché larga y `loading="lazy"`. Validar el contenido real
    (no confiar en la extensión) y rechazar imágenes gigantes (límite de píxeles contra "bombas de descompresión").
  * Inventario físico: guardar stock al iniciar el conteo y aplicar SOLO la diferencia sobre el stock actual.
  * Códigos de barras en UNA tabla única (producto + presentaciones) para unicidad real en BD.
  * Carga de stock inicial (manual y por Excel) con lote/vencimiento → kardex "STOCK_INICIAL".
  * Exportar Excel protegido contra inyección de fórmulas. Importar Excel con vista previa y todo-o-nada.
  * Stock: transacción + FOR UPDATE en orden fijo de producto_id + reintento ante deadlock (1213);
    estados de documentos verificados con fila bloqueada (sin doble aplicación); kardex inmutable;
    suma de lotes = stock (invariante probada); costo promedio solo con entradas; pruebas de concurrencia.
- Segunda revisión de robustez (2026-10-23). DECISIONES del usuario:
  * **Productos con lotes SÍ se pueden vender sin stock (con permiso)**: la venta sin lote queda como
    "pendiente de lote" (tabla por producto+almacén); al ingresar mercadería (compra, stock inicial, ajuste +,
    transferencia recibida) se descuenta primero lo pendiente del lote nuevo. Invariante:
    suma(lotes) − pendiente = stock_almacen. Alerta en Inventario.
  * **Lotes vencidos: BLOQUEAR la venta**; se dan de baja como merma.
  * **Ajustes y mermas: SIEMPRE con aprobación** de un usuario con permiso de aprobar (Administrador). Estados
    BORRADOR → PENDIENTE → APLICADO / RECHAZADO; el stock solo cambia al aprobar (re-validando stock en ese momento).
    Quien crea no puede aprobar su propio ajuste (salvo que sea el único Administrador: configurable).
  * **Transferencias: almacén virtual "En tránsito"** por sucursal: al enviar sale del origen y entra a tránsito;
    al recibir sale de tránsito y entra al destino; lo no recibido sale de tránsito como merma. Se ve en Inventario.
  * Técnicas (decididas por Claude): transferencias con varios lotes por producto (FEFO) y lote espejo en
    destino; inventario físico por lote y un solo conteo abierto por producto+almacén; clave de idempotencia en
    toda operación que cambia stock (doble clic / reintento); kardex inmutable con triggers MySQL (sin UPDATE/
    DELETE); verificación de integridad (stock = suma kardex = suma lotes − pendiente) como endpoint + script;
    no cambiar unidad ni `maneja_lotes` ni borrar productos con movimientos (solo desactivar); bloqueo optimista
    (columna `version`) al editar productos; Excel con límite de tamaño/filas, lectura segura y revalidación al
    confirmar; fotos con nombre aleatorio, borrar la anterior al reemplazar, carpeta incluida en respaldos.
- ✅ Bocetos Transferencia, Importar Excel y Stock inicial (commit dc108ea). Usuario APROBÓ e inició la Fase 3.
- ✅ Backend parte 1: migración `ec72af6da32e` (codigos_barras, operaciones_idempotentes, pendiente_lote, sin CHECK
  de stock ≥ 0, triggers de kardex inmutable, aprobación en ajustes/físico, lotes en físico/transferencias,
  version e imagen en productos). MySQL local: se activó `log_bin_trust_function_creators=1` (SET PERSIST, con
  root una sola vez; en Docker va en docker-compose). Servicios: `transacciones.ejecutar` (reintento deadlock +
  idempotencia), `correlativos`, `stock` (bloqueo en orden, mover, FEFO, costo promedio), `imagenes` (WEBP),
  `productos`, `categorias` (+marcas). Routers productos, categorías/marcas, media. Pruebas: 52 OK.
- ✅ Backend parte 2: `services/inventario.py` (almacenes, stock, resumen, lotes, kardex, stock inicial,
  integridad), `ajustes.py` (aprobación obligatoria, sin autoaprobación salvo único aprobador), `transferencias.py`
  (FEFO por lote, en tránsito, faltantes, anulación), `inventario_fisico.py` (por lote, solo diferencia, un conteo
  abierto por producto), `excel_productos.py` (vista previa, todo-o-nada, plantilla, exportar sin fórmulas).
  Router `/inventario/*` y `/productos/{plantilla,exportar,importar}`. Cabecera `Idempotency-Key` (la clave se
  reserva al inicio de la transacción). Pruebas: 77 OK (incluye concurrencia, idempotencia y kardex inmutable).
- ✅ Datos demo: `python -m app.demo` (34 productos, almacén "Depósito", lotes, un ajuste por aprobar). Cargados
  en la BD de trabajo; integridad correcta.
- ✅ FRONTEND Fase 3 (estilo Bodega, según bocetos): /productos (contadores, filtros, margen, stock), /productos/nuevo
  y /productos/[id] (ficha con presentaciones, IGV, lotes, foto WEBP, stock por almacén, historial de precios, aviso
  de edición concurrente), /productos/importar (subir → revisar → importar), /categorias (categorías + marcas),
  /inventario (resumen, stock, por vencer, en tránsito), /inventario/kardex, /inventario/ajustes (+nuevo, +[id] con
  aprobar/rechazar), /inventario/transferencias (+nueva, +[id] recibir con faltantes), /inventario/fisicos (+[id]
  conteo con escáner), /inventario/stock-inicial. Cliente: `api()` admite FormData, `descargar()` para Excel y
  `nuevaClave()` (Idempotency-Key creada al abrir cada formulario; funciona también por http en la red local).
  `npx tsc --noEmit` y `npx next build` OK (30 rutas). Pruebas backend 77 OK.
- ✅ Revisión visual (23/10, capturas en `.taste-skill/capturas/f3r`): 13 pantallas en escritorio, celular y
  oscuro. Corregido (commit 693cdfd): vencimientos se mostraban un día antes (fecha sin hora leída como UTC)
  y la etiqueta se encimaba sobre el total en los paneles oscuros.
- ✅ El usuario APROBÓ la Fase 3 (23/10) y pidió pasar a la Fase 4.
- ⏳ Ajustar bocetos a la segunda revisión: Ajuste (pendiente de aprobación), Inventario físico (por lote),
  Transferencia (lotes + en tránsito), Inventario (en tránsito, pendiente de lote, stock negativo). Luego aprobación.

## Fase 4 — POS y caja (en curso)
- Ya existen desde la Fase 1 los modelos: ventas, detalles_venta, pagos_venta, cajas, sesiones_caja (1 abierta por
  cajero y por caja), arqueos_denominacion, resumen_cierre_caja, movimientos_caja, devoluciones, cuentas_por_cobrar,
  abonos. Boceto del POS: `diseno/bodega/Pos.dc.html`. Parámetros: redondeo, descuento máximo, denominaciones.
- ✅ Decisiones del usuario (23/10): 1) comprobante = **ticket interno** (serie T001, sin SUNAT; boleta/factura
  electrónica más adelante con un OSE/PSE); 2) impresión **desde el navegador** (80/58 mm, Chrome en modo quiosco);
  3) **cierre ciego** (el cajero cuenta sin ver el esperado; luego ve la diferencia); 4) anular o descuento mayor al
  permitido → **clave del supervisor** en la misma caja (queda en auditoría quién autorizó).
- ✅ BACKEND Fase 4 (95 pruebas OK, ruff limpio):
  - `services/caja.py` + `/caja`: cajas de la sucursal, turno actual, abrir (bloquea la fila de la caja), ingresos/
    egresos (egreso ≤ efectivo esperado), cierre ciego con arqueo por billete/moneda y declarados por método
    (tarjeta, Yape, Plin…), historial por cajero. Venta = FOR SHARE del turno; cierre = FOR UPDATE (espera ventas en
    curso; sumas con FOR SHARE para ver lo último confirmado).
  - `services/ventas.py` + `/ventas`: catálogo del POS (todo en memoria del navegador), venta en una transacción
    (turno → productos/stock → lotes FEFO sin vencidos → cliente → serie T001 FOR UPDATE), Idempotency-Key
    OBLIGATORIA, el servidor recalcula y rechaza si cambió el precio (409 precio_cambiado) o el total
    (409 total_distinto); IGV por línea (incluido en el precio), exonerados, ICBPER, descuento global prorrateado,
    redondeo en efectivo a favor del cliente (parámetro), pago mixto, vuelto, fiado con límite (CuentaPorCobrar).
    Anulación solo con el turno abierto (si no, devolución) y revierte stock (lotes; sin lote → `reingresar_sin_lote`).
  - `services/autorizaciones.py` + `POST /ventas/autorizar`: clave del supervisor → token de 3 min para UN permiso,
    UN cajero y la sucursal; se consume una sola vez (fila en operaciones_idempotentes), bloqueo por intentos
    fallidos como el login, auditoría AUTORIZAR / AUTORIZACION_FALLIDA.
  - `/clientes/buscar` y alta rápida (módulo completo en Fase 5).
  - Corregido: `ContextoUsuario` guarda usuario_id y nombre como valores simples (un rollback expiraba el usuario y
    la respuesta de una operación repetida fallaba).
- ⏳ Frontend: POS, caja (abrir, movimientos, cierre ciego), ventas + ticket 80 mm, diálogo del supervisor.

## Pedido del usuario para la Fase 5
- Usar productos de prueba **con sus imágenes**, descargadas de internet (todo de prueba). Convertirlas a WEBP con
  el servicio de imágenes existente.

## Siguiente paso
Que el usuario apruebe (o ajuste) los bocetos de la Fase 3. Luego implementar backend (servicios con
SELECT ... FOR UPDATE para todo cambio de stock, kardex, costo promedio, importación/exportación Excel) + pruebas
pytest de inventario, y después el frontend con el estilo Bodega. Si lo aprueba:
**Fase 3 — productos, categorías, marcas e inventario** (stock por almacén, lotes, kardex, ajustes,
transferencias, inventario físico, importar/exportar Excel), con el estilo Bodega y bocetos previos en
Claude Design si son pantallas nuevas. El POS (Fase 4) se implementa con su boceto `diseno/bodega/Pos.dc.html`.
