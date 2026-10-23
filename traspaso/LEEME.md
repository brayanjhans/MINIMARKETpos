# Traspaso a otra PC

Esta carpeta trae lo necesario para seguir el proyecto en otra PC: la base de datos y los pasos de instalación.
El avance y las instrucciones para Claude están en la raíz: `CLAUDE.md` y `PROGRESO.md`.

> ⚠️ El repositorio es **público**. `minimarket.sql` solo debe tener **datos de prueba**. Cuando el sistema tenga
> ventas o clientes reales, el respaldo se guarda en `respaldos/` (no se sube) y se lleva en USB.

## Contenido
- `minimarket.sql`: respaldo completo de la BD `minimarket` (tablas, datos de prueba y triggers del kardex).
  Exportado el 23/10/2026, al cierre de la Fase 4 (Caja 1 abierta con 4 ventas de prueba).

## Pasos en la PC nueva
1. Instalar Git, Python 3.14, Node.js 24 y MySQL 8.0.
2. `git clone https://github.com/brayanjhans/MINIMARKETpos`
3. En MySQL, como root:
   ```sql
   CREATE DATABASE minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   CREATE USER 'minimarket'@'localhost' IDENTIFIED BY 'minimarket';
   GRANT ALL ON minimarket.* TO 'minimarket'@'localhost';
   SET PERSIST log_bin_trust_function_creators = 1;
   ```
4. Importar: `mysql -u root -p minimarket < traspaso/minimarket.sql`
5. `backend/.env`: copiarlo de la PC anterior (USB). Si no se puede, copiar `backend/.env.example` a `.env` y poner
   una `JWT_SECRET` nueva (`python -c "import secrets; print(secrets.token_urlsafe(64))"`). Con una clave nueva, los
   QR de los tickets ya impresos dejan de verificarse (salen como «alterados»): con datos de prueba no importa.
6. Backend (desde `backend/`): `python -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`,
   `.venv\Scripts\alembic upgrade head` (debe decir que ya está al día) y
   `.venv\Scripts\uvicorn app.main:app --port 8010`.
7. Frontend (desde `frontend/`): `npm install` y `npm run dev` → http://localhost:3010 (usuario `admin`).
8. Abrir Claude Code en la carpeta del proyecto y escribir **«continúa»**.

## Al volver a cambiar de PC
Exportar de nuevo y reemplazar `minimarket.sql` (desde `backend/`, con la contraseña del usuario `minimarket`):
```
mysqldump -u minimarket -p --single-transaction --routines --triggers --no-tablespaces --set-gtid-purged=OFF --default-character-set=utf8mb4 --result-file=../traspaso/minimarket.sql minimarket
```
