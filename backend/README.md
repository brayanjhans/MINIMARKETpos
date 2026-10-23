# Backend – Minimarket POS (FastAPI)

> Documentación completa en la Fase 7. Resumen para desarrollo local (MySQL 8):

Base de datos (una sola vez, como root):

```sql
CREATE DATABASE minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'minimarket'@'localhost' IDENTIFIED BY 'minimarket';
GRANT ALL PRIVILEGES ON minimarket.* TO 'minimarket'@'localhost';
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env          # ajustar DATABASE_URL si es necesario

.\.venv\Scripts\alembic upgrade head   # crear/actualizar tablas
.\.venv\Scripts\python -m app.seed     # roles, permisos, admin, categorías
.\.venv\Scripts\uvicorn app.main:app --reload --port 8010
```

- API: http://localhost:8010 · Documentación interactiva: http://localhost:8010/docs
- Se usa el puerto 8010 (no 8000) para no chocar con otros proyectos de la PC.
- Verificaciones: `$env:PYTHONPATH="."; .\.venv\Scripts\python scripts\verificar_fase2.py`
- Usuario inicial: `admin` / `Admin123*` (configurable en `.env`)
- Nueva migración tras cambiar modelos: `alembic revision --autogenerate -m "descripcion"`
