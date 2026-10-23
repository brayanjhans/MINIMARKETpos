# Traspaso a otra PC

Esta carpeta trae lo necesario para seguir el proyecto en otra PC: la base de datos, los scripts de instalación y
esta guía. El avance y las instrucciones para Claude están en la raíz: `CLAUDE.md` y `PROGRESO.md`.

> ⚠️ El repositorio es **público**. `minimarket.sql` solo debe tener **datos de prueba**. Cuando el sistema tenga
> ventas o clientes reales, el respaldo se guarda en `respaldos/` (no se sube) y se lleva en USB.

## Contenido
- `minimarket.sql`: respaldo completo de la BD `minimarket` (51 tablas, datos de prueba y los triggers del kardex).
  Exportado el 23/10/2026 al cierre de la Fase 4: 34 productos, Caja 1 abierta con 4 ventas de prueba.
- `instalar.ps1`: instala todo y carga la base de datos (una sola vez).
- `iniciar.ps1`: enciende el sistema (cada día).

## Guía para la PC nueva (funciona 100 % en local)

### 1. Instalar los programas (una sola vez)
| Programa | Versión | Dónde | Ojo |
|---|---|---|---|
| Git | cualquiera | https://git-scm.com | — |
| Python | **3.14** | https://www.python.org/downloads/ | marcar **«Add python.exe to PATH»** |
| Node.js | **24** (LTS) | https://nodejs.org | — |
| MySQL | **8.0** | https://dev.mysql.com/downloads/installer/ | instalar «MySQL Server», anotar la contraseña de **root**, puerto 3306 |

Los puertos **8010** (backend) y **3010** (frontend) deben estar libres.

### 2. Bajar el proyecto
```
git clone https://github.com/brayanjhans/MINIMARKETpos minimarket
cd minimarket
```

### 3. Instalar todo con un comando
```
powershell -ExecutionPolicy Bypass -File traspaso\instalar.ps1
```
Hace, en orden: revisa los programas · crea `backend\.venv` e instala lo de Python · crea `backend\.env` con una
clave secreta nueva · pide la contraseña de **root** de MySQL (no se guarda) · crea la base `minimarket` y su
usuario · importa `traspaso\minimarket.sql` · aplica las migraciones · instala lo del frontend. Si algo falla, dice
qué falta; se puede volver a ejecutar sin problema.

> Si traes el `backend\.env` de la PC anterior (USB), cópialo encima del nuevo: así los QR de los tickets ya
> impresos siguen siendo válidos. Con datos de prueba da igual.

### 4. Encender el sistema (cada día)
```
powershell -ExecutionPolicy Bypass -File traspaso\iniciar.ps1
```
Abre dos ventanas (backend y frontend). Luego entra a **http://localhost:3010** con `admin` / `Admin123*`.
Para apagar, cierra esas dos ventanas.

### 5. Seguir programando con Claude
Abrir Claude Code en la carpeta `minimarket` y escribir **«continúa»**: lee `CLAUDE.md` y `PROGRESO.md` y sigue
desde donde quedamos.

### Si prefieres hacerlo a mano
1. En MySQL como root:
   ```sql
   CREATE DATABASE minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   CREATE USER 'minimarket'@'localhost' IDENTIFIED BY 'minimarket';
   GRANT ALL ON minimarket.* TO 'minimarket'@'localhost';
   GRANT ALL ON minimarket_test.* TO 'minimarket'@'localhost';
   SET PERSIST log_bin_trust_function_creators = 1;
   ```
2. `mysql -u root -p --default-character-set=utf8mb4 minimarket < traspaso\minimarket.sql`
3. `copy backend\.env.example backend\.env` y cambiar `JWT_SECRET` por una clave nueva
   (`python -c "import secrets; print(secrets.token_urlsafe(64))"`).
4. Desde `backend\`: `python -m venv .venv` · `.venv\Scripts\pip install -r requirements.txt` ·
   `.venv\Scripts\alembic upgrade head` · `.venv\Scripts\uvicorn app.main:app --port 8010`
5. Desde `frontend\`: `npm ci` · `npm run dev`

### Problemas comunes
- **«No se pudo entrar a MySQL como root»**: el servicio MySQL80 está apagado (Servicios de Windows → MySQL80 →
  Iniciar) o la contraseña no es la correcta.
- **Error 1419 al importar** (triggers): falta `SET PERSIST log_bin_trust_function_creators = 1;` como root.
- **«No se puede cargar el archivo .ps1»**: usar el comando completo, con `-ExecutionPolicy Bypass`.
- **Puerto ocupado**: otro programa usa el 8010 o el 3010; cerrarlo.

## Trabajar en dos PCs (ir y volver)
Mientras el sistema no esté en producción, los datos son **de prueba**: cada PC tiene los suyos y no hace falta
llevarlos. Lo que viaja es el **código** (por GitHub). Si una fase agrega tablas, al actualizar se aplican las
migraciones y la base de esa PC queda al día, conservando sus datos.

| Momento | Comando | Qué hace |
|---|---|---|
| **Al terminar** en una PC | `powershell -ExecutionPolicy Bypass -File traspaso\guardar.ps1` | sube el código a GitHub |
| **Al llegar** a la otra PC | `powershell -ExecutionPolicy Bypass -File traspaso\actualizar.ps1` | baja el código, instala lo nuevo y aplica las migraciones |

O pídeselo a Claude: **«me voy a la otra PC, guarda todo»** / **«vengo de la otra PC, actualiza todo»**.

Solo si quieres los **mismos datos** en las dos PCs (o la base se dañó): `guardar.ps1 -ConBase` exporta la base al
salir y `actualizar.ps1 -ConBase` la carga al llegar (reemplaza la de esa PC).

`actualizar.ps1` se detiene si encuentra código sin subir en esa PC, para no mezclar trabajos.

Exportar a mano (lo mismo que hace `guardar.ps1`; pide la contraseña `minimarket`):
```
mysqldump -u minimarket -p --single-transaction --routines --triggers --no-tablespaces --set-gtid-purged=OFF --default-character-set=utf8mb4 --result-file=traspaso/minimarket.sql minimarket
```
