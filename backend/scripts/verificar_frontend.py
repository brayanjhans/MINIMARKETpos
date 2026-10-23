"""Prueba el flujo de autenticación pasando por el frontend (rewrite /api/v1 y proxy.ts de Next).

Uso (con backend y frontend levantados):  python scripts/verificar_frontend.py [url_frontend]
"""

import sys
import time

import httpx

FRONT = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3010"
res: list[bool] = []


def check(nombre: str, ok: bool, extra: object = "") -> None:
    res.append(ok)
    print(("  OK    " if ok else "  FALLA ") + nombre + (f"  -> {extra}" if extra and not ok else ""))


def esperar() -> None:
    for _ in range(90):
        try:
            if httpx.get(f"{FRONT}/login", timeout=10).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise SystemExit("El frontend no respondió")


esperar()
with httpx.Client(base_url=FRONT, follow_redirects=False, timeout=60) as c:
    r = c.get("/usuarios")
    check("sin sesión, /usuarios redirige a /login?siguiente=", r.status_code in (307, 308)
          and "/login?siguiente=%2Fusuarios" in r.headers.get("location", ""), r.headers)
    r = c.get("/login")
    check("página de login carga (200)", r.status_code == 200 and "Ingresar" in r.text)

    r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin123*"})
    check("login vía rewrite /api/v1 (mismo origen)", r.status_code == 200, r.text[:200])
    set_cookie = r.headers.get("set-cookie", "")
    check("cookie de sesión httpOnly + SameSite=strict", "mm_refresh=" in set_cookie
          and "httponly" in set_cookie.lower() and "samesite=strict" in set_cookie.lower(), set_cookie)
    token = r.json()["access_token"]

    r = c.get("/login")
    check("con sesión, /login redirige a /dashboard", r.status_code in (307, 308)
          and r.headers.get("location", "").endswith("/dashboard"), r.headers)
    r = c.get("/dashboard")
    check("con sesión, /dashboard carga", r.status_code == 200)

    r = c.post("/api/v1/auth/refresh")
    check("refresh con la cookie (simula recargar la página)",
          r.status_code == 200 and bool(r.json().get("access_token")))
    r = c.get("/api/v1/usuarios", params={"tamanio": 5}, headers={"Authorization": f"Bearer {token}"})
    check("listar usuarios vía proxy", r.status_code == 200 and r.json()["total"] >= 1, r.text[:200])
    r = c.get("/api/v1/roles/permisos", headers={"Authorization": f"Bearer {token}"})
    check("catálogo de permisos vía proxy", r.status_code == 200 and len(r.json()) == 16)

    r = c.post("/api/v1/auth/logout")
    check("logout borra la cookie", r.status_code == 200 and 'mm_refresh=""' in r.headers.get("set-cookie", ""),
          r.headers.get("set-cookie"))
    r = c.get("/dashboard")
    check("tras logout, /dashboard vuelve a pedir login", r.status_code in (307, 308))

print(f"\n{sum(res)}/{len(res)} pruebas OK")
