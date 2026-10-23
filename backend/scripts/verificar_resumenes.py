"""Verifica los endpoints de resumen (usuarios y auditoría). Uso: PYTHONPATH=. python scripts/verificar_resumenes.py"""

import asyncio
from datetime import date

from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123*"})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        await c.post("/api/v1/auth/login", json={"username": "admin", "password": "incorrecta"})
        r = await c.get("/api/v1/usuarios/resumen", headers=h)
        print("usuarios/resumen:", r.status_code, r.json())
        assert r.status_code == 200 and r.json()["con_acceso"] >= 1 and r.json()["ingresaron_hoy"] >= 1
        hoy = date.today().isoformat()
        r = await c.get("/api/v1/auditoria/resumen", params={"desde": hoy, "hasta": hoy}, headers=h)
        print("auditoria/resumen:", r.status_code, r.json())
        d = r.json()
        assert r.status_code == 200 and d["fallos"] >= 1 and d["revisar"]["nombre"]
        assert d["total"] >= d["ingresos"] + d["fallos"] + d["cambios"]
    await engine.dispose()
    print("OK")


asyncio.run(main())
