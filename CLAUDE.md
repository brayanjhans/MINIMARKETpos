# Minimarket POS – instrucciones para Claude

## Al iniciar una sesión
- Si el usuario dice "continúa", "continue", "sigue" o similar: **lee `PROGRESO.md` y muéstrale un resumen
  de dónde quedamos** (fase actual, lo último hecho, lo pendiente y el siguiente paso) antes de seguir.
- **Actualiza `PROGRESO.md`** cada vez que completes una parte importante (no solo al final de la fase),
  para que el trabajo se pueda retomar aunque la PC se apague.
- Requisitos originales completos: `PROMPT_CLAUDE_CODE.txt`. Se trabaja POR FASES y se detiene al final de
  cada una para que el usuario revise.
- Comunicación con el usuario: en español.

## Stack y decisiones tomadas (no cambiar sin consultar)
- Backend: FastAPI + SQLAlchemy 2 async + Pydantic v2 + Alembic. **Python 3.14** (venv en `backend/.venv`).
- **Base de datos: MySQL 8** local (servicio MySQL80). BD `minimarket`, usuario `minimarket`/`minimarket`.
  Driver `aiomysql`. NO PostgreSQL (el usuario lo pidió). No guardar la contraseña de root en el proyecto.
- Docker: archivos listos (`docker-compose.yml` con mysql:8.4) pero Docker no está instalado; se verá en Fase 7.
- Multi-sucursal: stock por almacén (`stock_almacen`), usuarios asignados a sucursales, sucursal activa en el JWT.
- Frontend: Next.js 16 (App Router) + TS 5 + Tailwind 4 + shadcn/ui + Framer Motion + TanStack Query 5 +
  Zustand 5. El frontend llama al backend vía rewrite `/api/v1` (mismo origen, cookie httpOnly de refresh).

## Puertos (IMPORTANTE)
- Este proyecto usa **backend 8010 y frontend 3010**. Los puertos 3000/8000 los usa otro proyecto del
  usuario (`C:\laragon\www\garantias_seacee`): no ocuparlos ni detener sus procesos.

## Comandos útiles (desde `backend/`)
- Migrar: `.venv\Scripts\alembic upgrade head` · Nueva migración: `.venv\Scripts\alembic revision --autogenerate -m "..."`
- Datos iniciales: `.venv\Scripts\python -m app.seed` · API: `.venv\Scripts\uvicorn app.main:app --reload --port 8010`
- Frontend (desde `frontend/`): `npm run dev` (puerto 3010) · Tipos: `npx tsc --noEmit` · Build: `npx next build`
- Verificaciones (desde `backend/`, con `$env:PYTHONPATH="."`): `scripts\verificar_fase1.py`, `verificar_fase2.py`,
  `verificar_frontend.py` (este último con ambos servidores levantados)
- Next 16: `src/proxy.ts` reemplaza a `middleware.ts`. shadcn genera `import { cn } from "cn"`: corregir a `@/lib/utils`.
- Lint: `.venv\Scripts\ruff check app --select F,I,E,B,UP --line-length 120 --target-version py314`
- En las migraciones de MySQL, el `downgrade` debe eliminar tablas sin `op.drop_index` previos.
