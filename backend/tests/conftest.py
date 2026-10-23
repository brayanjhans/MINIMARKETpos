"""Configuración común de las pruebas.

Las pruebas usan SIEMPRE una base de datos aparte (minimarket_test): se borra y se recrea al inicio de cada
corrida, se le aplican todas las migraciones y se cargan los datos iniciales. Nunca tocan la base de trabajo.
"""

import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from urllib.parse import urlparse

# Debe definirse ANTES de importar la aplicación (la configuración se lee al importar)
URL_PRUEBAS = os.environ.get(
    "TEST_DATABASE_URL", "mysql+aiomysql://minimarket:minimarket@localhost:3306/minimarket_test?charset=utf8mb4"
)
os.environ["DATABASE_URL"] = URL_PRUEBAS
os.environ["ENTORNO"] = "pruebas"
os.environ["DB_POOL_SIZE"] = "5"

import pymysql  # noqa: E402
import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from alembic import command  # noqa: E402
from app.core.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import ejecutar_seed  # noqa: E402

API = "/api/v1"
ADMIN = ("admin", "Admin123*")
RAIZ_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _recrear_base() -> None:
    url = urlparse(URL_PRUEBAS.replace("mysql+aiomysql", "mysql"))
    nombre = url.path.lstrip("/")
    assert nombre.endswith("_test"), f"Por seguridad las pruebas solo corren en una base *_test (es {nombre!r})"
    conexion = pymysql.connect(
        host=url.hostname, port=url.port or 3306, user=url.username, password=url.password, autocommit=True
    )
    with conexion.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{nombre}`")
        cur.execute(f"CREATE DATABASE `{nombre}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    conexion.close()


async def _sembrar() -> None:
    await ejecutar_seed()
    # El seed abrió conexiones en un bucle temporal: se cierran para que las pruebas abran las suyas
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    _recrear_base()
    config = Config(os.path.join(RAIZ_BACKEND, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(RAIZ_BACKEND, "alembic"))
    command.upgrade(config, "head")
    asyncio.run(_sembrar())
    yield


@pytest.fixture(scope="session", autouse=True)
async def cerrar_motor(base_de_datos):
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def limpiar_intentos():
    """Cada prueba empieza sin ingresos fallidos ni bloqueos (el límite por IP cuenta los fallidos)."""
    async with SessionLocal() as s, s.begin():
        await s.execute(text("DELETE FROM auditoria WHERE accion = 'LOGIN_FALLIDO'"))
        await s.execute(text("UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL"))
    yield


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def cliente() -> AsyncIterator[AsyncClient]:
    """Cliente HTTP sin sesión (cada prueba tiene sus propias cookies)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def iniciar_sesion(cliente: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await cliente.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@dataclass
class Sesion:
    cliente: AsyncClient
    headers: dict[str, str]

    async def get(self, ruta: str, **kw):
        return await self.cliente.get(f"{API}{ruta}", headers=self.headers, **kw)

    async def post(self, ruta: str, **kw):
        return await self.cliente.post(f"{API}{ruta}", headers=self.headers, **kw)

    async def patch(self, ruta: str, **kw):
        return await self.cliente.patch(f"{API}{ruta}", headers=self.headers, **kw)

    async def delete(self, ruta: str, **kw):
        return await self.cliente.delete(f"{API}{ruta}", headers=self.headers, **kw)


@pytest.fixture
async def admin(cliente: AsyncClient) -> Sesion:
    return Sesion(cliente, await iniciar_sesion(cliente, *ADMIN))


@pytest.fixture
async def crear_usuario(admin: Sesion):
    """Fábrica: crea un usuario con nombre único y devuelve (datos, contraseña)."""

    async def _crear(rol: str = "Cajero", password: str = "Clave2026x", **extra) -> tuple[dict, str]:
        roles = (await admin.get("/roles")).json()
        sucursales = (await admin.get("/sucursales")).json()
        rol_id = next(r["id"] for r in roles if r["nombre"] == rol)
        datos = {
            "nombre_completo": "Persona de Prueba",
            "username": f"prueba.{uuid.uuid4().hex[:8]}",
            "password": password,
            "rol_id": rol_id,
            "sucursal_ids": [sucursales[0]["id"]],
            "debe_cambiar_password": False,
            **extra,
        }
        r = await admin.post("/usuarios", json=datos)
        assert r.status_code == 201, r.text
        return r.json(), password

    return _crear
