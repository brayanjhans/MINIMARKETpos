# Notas de diseño — Minimarket POS (taste-skill, modo app)

Estilo: achromatic-ledger (seed 20987497), elegido por el usuario. Tema claro por defecto; oscuro con los
tokens por defecto de app-screens §9.5. Shell: open plane + barra superior delgada SIN regla (el brief original
exige "barra superior con usuario y caja activa": el brief manda sobre la hoja).

## Inventario de datos
- Usuarios (1-30 por negocio): nombre, @usuario, correo, rol, sucursales, estado, último acceso.
- Roles (3 del sistema + propios): 61 permisos en 16 módulos.
- Auditoría: decenas a miles de eventos/día (login, fallos, cambios).
- Sucursales (1-5), cada una con su almacén de venta y sus cajas. Moneda: soles, S/ 1,234.50.
- Personas: administrador (revisa y configura, en PC), cajeros (8 h en la PC de caja), almacenero (tablet).
- Trabajos: crear usuario / restablecer clave (más frecuente), ajustar permisos, revisar quién hizo qué.

## Rasgo propio (face)
Fondo piedra #f4f3f1 (estante y papel de tienda) en lugar de #f8f8f8, tarjetas blancas; cifras en Geist Mono
(como las columnas de un libro contable y el ticket térmico; decisión del estilo, se declara al inspector).

## Elemento distintivo
El ticket térmico (el impreso del mundo del minimarket): en el login, dibujado en código con la serie T001,
ítems que suman, IGV correcto y su código de barras. Marca: un código de barras de 5 barras (no un cuadro con letra).
Cada persona con su inicial sobre un tinte pálido estable (60°+ de separación).

## Pregunta de cada pantalla
- Inicio: "¿En qué sucursal y caja estoy, y qué pasó hoy en el sistema?" → franja sucursal/caja/sesión + actividad.
- Usuarios: "¿Quién tiene acceso y en qué estado está?" → tabla; acción principal: Nuevo usuario.
- Roles: "¿Qué puede hacer cada rol?" → lista de roles + permisos por módulo (patrón de ajustes en dos columnas).
- Auditoría: "¿Quién hizo qué y cuándo?" → lista con filtros; los fallos en el color negativo.

## Crítica (2 rondas, capturas en .taste-skill/despues)
1. Pregunta respondida por lo más grande: sí (franja de turno arriba; tabla en listas).
2. Bordes compartidos: corregido el doble borde izquierdo (barra en x=274 vs título en 248) → todo en 248.
   Tarjetas del Inicio: terminaban 6 px distintas → igualadas (587/587).
3. Color solo en estado y en la acción principal (negro); el azul del dato queda para gráficos (Fase 6) y para
   marcar cambios sin guardar en roles. Cara visible: fondo piedra + cifras mono + ticket en el login.
4. Cifras: el ticket cuadra (22.80 = 19.32 + 3.48; vuelto 27.20). Conteos calculados de la API.
5. Ceros y vacíos: "Nunca" para usuarios sin ingreso, "—" para datos ausentes, frases que dicen qué hacer.
7. Celular: menú plegado en barra de 56 px; usuarios en filas de dos líneas; Inicio en 2×2.
Inspector oficial (solo /login es pública): 0 FAIL; 2 WARN defendibles (mitad derecha = ilustración centrada).
Lint --app: 0 FAIL; 5 WARN por Geist Mono (decisión del estilo para las cifras).

## Antes (capturas en .taste-skill/antes)
Tarjetas con ícono en cuadro tintado, etiquetas MAYÚSCULAS espaciadas, verde en cromo, título duplicado,
media pantalla vacía bajo la tabla, matriz de roles como grilla de tarjetas, indicador de Next tapando el menú.
