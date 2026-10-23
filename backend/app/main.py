import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.excepciones import registrar_manejadores
from app.routers import auditoria, auth, categorias, inventario, media, productos, roles, sucursales, usuarios
from app.utils.respuestas import RespuestaError

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NOMBRE,
    version="1.0.0",
    description="API del sistema interno de minimarket: POS, inventario y administración.",
    lifespan=lifespan,
    docs_url=None if settings.es_produccion else "/docs",
    redoc_url=None,
    responses={
        400: {"model": RespuestaError},
        422: {"model": RespuestaError},
        500: {"model": RespuestaError},
    },
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGENES,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores(app)


@app.get("/health", tags=["Sistema"], summary="Estado del servicio y de la base de datos")
async def health() -> dict[str, str]:
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"estado": "ok", "base_de_datos": "ok"}


for modulo in (auth, usuarios, roles, auditoria, sucursales, productos, categorias, inventario, media):
    app.include_router(modulo.router, prefix=settings.API_PREFIX)
