# Minimarket POS – instrucciones para Claude

## Al iniciar una sesión
- Si el usuario dice "continúa", "continue", "sigue" o similar: **lee `PROGRESO.md` y muéstrale un resumen
  de dónde quedamos** (fase actual, lo último hecho, lo pendiente y el siguiente paso) antes de seguir.
- **Actualiza `PROGRESO.md`** cada vez que completes una parte importante (no solo al final de la fase),
  para que el trabajo se pueda retomar aunque la PC se apague.
- Requisitos originales completos: `PROMPT_CLAUDE_CODE.txt`. Se trabaja POR FASES y se detiene al final de
  cada una para que el usuario revise.
- Comunicación con el usuario: en español.

- Si es una **PC nueva** (no hay `backend/.venv`, `frontend/node_modules` o la BD `minimarket`): seguir
  `traspaso/LEEME.md` (instalación + importar `traspaso/minimarket.sql`) antes de continuar.

- El usuario trabaja en **dos PCs** con el mismo GitHub. Si dice que se va a la otra PC («guarda todo», «me voy»):
  ejecutar `traspaso/guardar.ps1` (exporta la BD a `traspaso/minimarket.sql`, commit y push). Si dice que viene de
  la otra PC («actualiza todo», «vengo de la otra»): hacer lo de `traspaso/actualizar.ps1` (pull, importar la BD,
  pip/npm, migraciones), avisando antes que la BD de esta PC se reemplaza. Detalle en `traspaso/LEEME.md`.

## Stack y decisiones tomadas (no cambiar sin consultar)
- Backend: FastAPI + SQLAlchemy 2 async + Pydantic v2 + Alembic. **Python 3.14** (venv en `backend/.venv`).
- **Base de datos: MySQL 8** local (servicio MySQL80). BD `minimarket`, usuario `minimarket`/`minimarket`.
  Driver `aiomysql`. NO PostgreSQL (el usuario lo pidió). No guardar la contraseña de root en el proyecto.
- Docker: archivos listos (`docker-compose.yml` con mysql:8.4) pero Docker no está instalado; se verá en Fase 7.
- Multi-sucursal: stock por almacén (`stock_almacen`), usuarios asignados a sucursales, sucursal activa en el JWT.
- Frontend: Next.js 16 (App Router) + TS 5 + Tailwind 4 + shadcn/ui + Framer Motion + TanStack Query 5 +
  Zustand 5. El frontend llama al backend vía rewrite `/api/v1` (mismo origen, cookie httpOnly de refresh).

## Repositorio Git
- Remoto: https://github.com/brayanjhans/MINIMARKETpos (rama `main`). Se sube por HTTPS con Git Credential
  Manager (ya autorizado en esta PC). Identidad local: brayanjhans / brayanjhansalmerco@gmail.com.
- Hacer commit al terminar cada parte importante y subir (`git push`) cuando el usuario lo apruebe o lo pida.
- Mensajes de commit en español; pasar el mensaje con `git commit -F archivo` (PowerShell rompe los here-strings).
- Nunca subir `.env`, `.venv`, `node_modules`, `.next` ni capturas de `.taste-skill/` (ya están en `.gitignore`).

## Puertos (IMPORTANTE)
- Este proyecto usa **backend 8010 y frontend 3010**. Los puertos 3000/8000 los usa otro proyecto del
  usuario (`C:\laragon\www\garantias_seacee`): no ocuparlos ni detener sus procesos.

## Comandos útiles (desde `backend/`)
- Migrar: `.venv\Scripts\alembic upgrade head` · Nueva migración: `.venv\Scripts\alembic revision --autogenerate -m "..."`
- Datos iniciales: `.venv\Scripts\python -m app.seed` · API: `.venv\Scripts\uvicorn app.main:app --reload --port 8010`
- Frontend (desde `frontend/`): `npm run dev` (puerto 3010) · Tipos: `npx tsc --noEmit` · Build: `npx next build`
- **Pruebas** (desde `backend/`): `.venv\Scripts\python -m pytest` — usan la base `minimarket_test`, que se
  borra y recrea en cada corrida (nunca tocan `minimarket`). Correrlas antes de cada commit.
- Prueba de punta a punta con los servidores levantados: `.venv\Scripts\python scripts\verificar_frontend.py`
- Next 16: `src/proxy.ts` reemplaza a `middleware.ts`. shadcn genera `import { cn } from "cn"`: corregir a `@/lib/utils`.
- Lint: `.venv\Scripts\ruff check app --select F,I,E,B,UP --line-length 120 --target-version py314`
- En las migraciones de MySQL, el `downgrade` debe eliminar tablas sin `op.drop_index` previos.
