import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.main import app
from app.models import Rol, Sucursal, Usuario

API = "/api/v1"
res: list[tuple[str, bool]] = []


def check(nombre: str, ok: bool, extra: object = "") -> None:
    res.append((nombre, ok))
    print(("  OK    " if ok else "  FALLA ") + nombre + (f"  -> {extra}" if extra and not ok else ""))


def cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def limpiar_previo() -> None:
    async with SessionLocal() as s, s.begin():
        await s.execute(text("DELETE FROM usuario_sucursales WHERE usuario_id IN "
                             "(SELECT id FROM usuarios WHERE username='acajera')"))
        await s.execute(text("DELETE FROM refresh_tokens"))
        await s.execute(text("DELETE FROM usuarios WHERE username='acajera'"))
        await s.execute(text("DELETE FROM roles WHERE nombre='Supervisor'"))
        await s.execute(text("DELETE FROM usuario_sucursales WHERE sucursal_id IN "
                             "(SELECT id FROM sucursales WHERE codigo='0099')"))
        await s.execute(text("DELETE FROM sucursales WHERE codigo='0099'"))
        await s.execute(text("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL"))


async def main() -> None:
    await limpiar_previo()
    async with SessionLocal() as s:
        id_cajero_rol = await s.scalar(select(Rol.id).where(Rol.nombre == "Cajero"))
        id_principal = await s.scalar(select(Sucursal.id).where(Sucursal.codigo == "0000"))

    async with cliente() as admin_c:
        print("— Login y sesión")
        r = await admin_c.post(f"{API}/auth/login", json={"username": "admin", "password": "mala"})
        check("contraseña incorrecta -> 401 mensaje genérico",
              r.status_code == 401 and r.json()["detalle"] == "Usuario o contraseña incorrectos", r.text)
        r = await admin_c.post(f"{API}/auth/login", json={"username": "noexiste", "password": "x"})
        check("usuario inexistente -> mismo mensaje (no revela usuarios)",
              r.json()["detalle"] == "Usuario o contraseña incorrectos")
        r = await admin_c.post(f"{API}/auth/login", json={"username": " ADMIN ", "password": "Admin123*"})
        check("login admin OK (ignora mayúsculas/espacios)", r.status_code == 200, r.text)
        token_admin = r.json()["access_token"]
        sesion = r.json()["usuario"]
        check("cookie httpOnly de refresh guardada", settings.COOKIE_REFRESH_NOMBRE in admin_c.cookies)
        check("sesión incluye 61 permisos y sucursal actual",
              len(sesion["permisos"]) == 61 and sesion["sucursal_actual"]["nombre"] == "Principal")
        check("refresh_token NO viaja en el JSON", "refresh_token" not in r.json())

        r = await admin_c.get(f"{API}/auth/me")
        check("sin token -> 401", r.status_code == 401 and r.json()["codigo"] == "sin_token")
        r = await admin_c.get(f"{API}/auth/me", headers=auth("abc.def.ghi"))
        check("token falso -> 401", r.status_code == 401)
        r = await admin_c.get(f"{API}/auth/me", headers=auth(token_admin))
        check("/auth/me con token OK", r.status_code == 200 and r.json()["username"] == "admin")

        print("— Usuarios")
        nuevo = {"nombre_completo": "Ana Cajera", "username": "acajera", "password": "1234",
                 "rol_id": id_cajero_rol, "sucursal_ids": [id_principal]}
        r = await admin_c.post(f"{API}/usuarios", json=nuevo, headers=auth(token_admin))
        check("contraseña débil -> 422 en español", r.status_code == 422 and "8 caracteres" in r.text, r.text)
        nuevo["password"] = "Cajera2026"
        nuevo["username"] = "ana cajera"
        r = await admin_c.post(f"{API}/usuarios", json=nuevo, headers=auth(token_admin))
        check("username con espacios -> 422 (formato)", r.status_code == 422, r.text)
        nuevo["username"] = "ACajera"
        r = await admin_c.post(f"{API}/usuarios", json=nuevo, headers=auth(token_admin))
        check("crear cajero -> 201 (username normalizado a minúsculas)",
              r.status_code == 201 and r.json()["username"] == "acajera", r.text)
        id_cajera = r.json()["id"]
        r = await admin_c.post(f"{API}/usuarios", json=nuevo, headers=auth(token_admin))
        check("username duplicado -> 409", r.status_code == 409 and "ya existe" in r.json()["detalle"], r.text)
        r = await admin_c.post(f"{API}/usuarios", json={**nuevo, "username": "otro", "extra": 1},
                               headers=auth(token_admin))
        check("campo desconocido -> 422", r.status_code == 422)

        r = await admin_c.get(f"{API}/usuarios?busqueda=ana&orden=-creado&tamanio=5", headers=auth(token_admin))
        check("listado con búsqueda/orden/paginación",
              r.status_code == 200 and r.json()["total"] == 1 and r.json()["tamanio"] == 5, r.text)
        r = await admin_c.get(f"{API}/usuarios?tamanio=500", headers=auth(token_admin))
        check("tamaño de página > 100 -> 422", r.status_code == 422)

        r = await admin_c.patch(f"{API}/usuarios/{sesion['id']}", json={"activo": False}, headers=auth(token_admin))
        check("no puede desactivarse a sí mismo", r.status_code == 422, r.text)
        r = await admin_c.patch(f"{API}/usuarios/{sesion['id']}", json={"rol_id": id_cajero_rol},
                                headers=auth(token_admin))
        check("único admin no puede perder su rol", r.status_code == 422 and "único administrador" in r.text, r.text)

    print("— Cajero: permisos, cambio de contraseña, bloqueo")
    async with cliente() as caj:
        r = await caj.post(f"{API}/auth/login", json={"username": "acajera", "password": "Cajera2026"})
        token_caj = r.json()["access_token"]
        check("cajero debe cambiar contraseña", r.json()["usuario"]["debe_cambiar_password"] is True)
        r = await caj.get(f"{API}/usuarios", headers=auth(token_caj))
        check("cajero sin permiso usuarios.ver -> 403", r.status_code == 403, r.text)
        await asyncio.sleep(1.1)
        r = await caj.post(f"{API}/auth/cambiar-password",
                           json={"password_actual": "Cajera2026", "password_nueva": "NuevaClave99"},
                           headers=auth(token_caj))
        check("cambiar contraseña OK", r.status_code == 200 and not r.json()["usuario"]["debe_cambiar_password"],
              r.text)
        token_caj2 = r.json()["access_token"]
        r = await caj.get(f"{API}/auth/me", headers=auth(token_caj))
        check("token anterior al cambio de contraseña queda inválido", r.status_code == 401)
        r = await caj.get(f"{API}/auth/me", headers=auth(token_caj2))
        check("token nuevo funciona", r.status_code == 200)

        for _ in range(5):
            r = await caj.post(f"{API}/auth/login", json={"username": "acajera", "password": "equivocada1"})
        r = await caj.post(f"{API}/auth/login", json={"username": "acajera", "password": "NuevaClave99"})
        check("5 intentos fallidos -> bloqueado aunque luego acierte",
              r.status_code == 401 and r.json()["codigo"] == "usuario_bloqueado", r.text)

    async with cliente() as admin_c:
        r = await admin_c.post(f"{API}/auth/login", json={"username": "admin", "password": "Admin123*"})
        token_admin = r.json()["access_token"]
        r = await admin_c.post(f"{API}/usuarios/{id_cajera}/desbloquear", headers=auth(token_admin))
        check("admin desbloquea al cajero", r.status_code == 200 and r.json()["bloqueado_hasta"] is None)

        print("— Refresh rotativo")
        cookie_1 = admin_c.cookies[settings.COOKIE_REFRESH_NOMBRE]
        r = await admin_c.post(f"{API}/auth/refresh")
        cookie_2 = admin_c.cookies[settings.COOKIE_REFRESH_NOMBRE]
        check("refresh devuelve nuevo access token y rota la cookie", r.status_code == 200 and cookie_1 != cookie_2)
        async with cliente() as otra_pestana:
            otra_pestana.cookies.set(settings.COOKIE_REFRESH_NOMBRE, cookie_1)
            r = await otra_pestana.post(f"{API}/auth/refresh")
            check("token recién rotado aceptado en periodo de gracia (2 pestañas)", r.status_code == 200, r.text)
            settings.REFRESH_GRACIA_SEGUNDOS = 0
            otra_pestana.cookies.clear()
            otra_pestana.cookies.set(settings.COOKIE_REFRESH_NOMBRE, cookie_1)
            r = await otra_pestana.post(f"{API}/auth/refresh")
            check("reutilizar token viejo fuera de gracia -> 401 (robo)",
                  r.status_code == 401 and r.json()["codigo"] == "sesion_revocada", r.text)
            settings.REFRESH_GRACIA_SEGUNDOS = 30
        r = await admin_c.post(f"{API}/auth/refresh")
        check("tras detectar robo se cierran TODAS las sesiones", r.status_code == 401)

        print("— Sucursales, roles, logout y auditoría")
        r = await admin_c.post(f"{API}/auth/login", json={"username": "admin", "password": "Admin123*"})
        token_admin = r.json()["access_token"]
        async with SessionLocal() as s, s.begin():
            sur = Sucursal(codigo="0099", nombre="Sucursal Prueba")
            s.add(sur)
            await s.flush()
            id_sur = sur.id
        r = await admin_c.post(f"{API}/auth/cambiar-sucursal", json={"sucursal_id": id_sur}, headers=auth(token_admin))
        check("cambiar a sucursal no asignada -> 403", r.status_code == 403, r.text)
        async with SessionLocal() as s, s.begin():
            await s.execute(text(f"INSERT INTO usuario_sucursales VALUES ({sesion['id']}, {id_sur})"))
        r = await admin_c.post(f"{API}/auth/cambiar-sucursal", json={"sucursal_id": id_sur}, headers=auth(token_admin))
        check("cambiar a sucursal asignada OK", r.status_code == 200
              and r.json()["usuario"]["sucursal_actual"]["nombre"] == "Sucursal Prueba", r.text)
        r = await admin_c.post(f"{API}/auth/refresh")
        check("el refresh conserva la sucursal elegida",
              r.json()["usuario"]["sucursal_actual"]["nombre"] == "Sucursal Prueba", r.text)
        token_admin = r.json()["access_token"]

        r = await admin_c.post(f"{API}/roles", json={"nombre": "Supervisor", "permisos": ["xx.yy"]},
                               headers=auth(token_admin))
        check("rol con permiso inexistente -> 422", r.status_code == 422, r.text)
        r = await admin_c.post(f"{API}/roles", json={"nombre": "Supervisor", "permisos": ["pos.vender", "caja.ver"]},
                               headers=auth(token_admin))
        check("crear rol Supervisor", r.status_code == 201, r.text)
        id_sup = r.json()["id"]
        r = await admin_c.get(f"{API}/roles", headers=auth(token_admin))
        admin_rol = next(x for x in r.json() if x["nombre"] == "Administrador")
        check("listar roles con conteos", admin_rol["total_permisos"] == 61 and admin_rol["total_usuarios"] == 1)
        r = await admin_c.patch(f"{API}/roles/{admin_rol['id']}", json={"permisos": []}, headers=auth(token_admin))
        check("no se pueden quitar permisos al Administrador", r.status_code == 422)
        r = await admin_c.delete(f"{API}/roles/{id_cajero_rol}", headers=auth(token_admin))
        check("no se puede eliminar rol del sistema", r.status_code == 422)
        r = await admin_c.delete(f"{API}/roles/{id_sup}", headers=auth(token_admin))
        check("eliminar rol sin usuarios OK", r.status_code == 200)
        r = await admin_c.get(f"{API}/roles/permisos", headers=auth(token_admin))
        check("catálogo de permisos por módulo", r.status_code == 200 and len(r.json()) == 16)

        r = await admin_c.get(f"{API}/auditoria?tamanio=100", headers=auth(token_admin))
        acciones = {x["accion"] for x in r.json()["items"]}
        check("auditoría registró login, fallos, bloqueo, cambios",
              {"LOGIN", "LOGIN_FALLIDO", "CREAR", "CAMBIAR_PASSWORD", "DESBLOQUEAR", "SESION_REVOCADA",
               "CAMBIAR_SUCURSAL", "ELIMINAR"} <= acciones, acciones)

        r = await admin_c.post(f"{API}/auth/logout")
        check("logout OK y cookie borrada",
              r.status_code == 200 and settings.COOKIE_REFRESH_NOMBRE not in admin_c.cookies)

    # Limpieza
    async with SessionLocal() as s, s.begin():
        await s.execute(delete(Usuario).where(Usuario.username == "acajera"))
        await s.execute(text(f"DELETE FROM usuario_sucursales WHERE sucursal_id={id_sur}"))
        await s.execute(text("DELETE FROM refresh_tokens"))
        await s.execute(text(f"DELETE FROM sucursales WHERE id={id_sur}"))
        await s.execute(text("DELETE FROM auditoria"))
        await s.execute(text("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL"))
    await engine.dispose()
    fallas = [n for n, ok in res if not ok]
    print(f"\n{len(res) - len(fallas)}/{len(res)} pruebas OK" + (f" — FALLAS: {fallas}" if fallas else ""))


asyncio.run(main())
