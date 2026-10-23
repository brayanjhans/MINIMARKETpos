from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.excepciones import NoAutenticado
from app.dependencies import DB, Contexto
from app.dependencies.auth import ip_cliente
from app.schemas.auth import (
    CambiarPasswordEntrada,
    CambiarSucursalEntrada,
    LoginEntrada,
    TokenRespuesta,
    UsuarioSesion,
)
from app.services import auth as servicio
from app.utils.respuestas import Mensaje

router = APIRouter(prefix="/auth", tags=["Autenticación"])

CookieRefresh = Annotated[str | None, Cookie(alias=settings.COOKIE_REFRESH_NOMBRE, include_in_schema=False)]


def _guardar_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.COOKIE_REFRESH_NOMBRE,
        token,
        max_age=settings.REFRESH_TOKEN_DIAS * 86400,
        httponly=True,  # inaccesible desde JavaScript (protege contra XSS)
        secure=settings.COOKIE_SECURE,
        samesite="strict",  # no se envía desde otros sitios (protege contra CSRF)
        path="/",
    )


def _borrar_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.COOKIE_REFRESH_NOMBRE, path="/", httponly=True, secure=settings.COOKIE_SECURE, samesite="strict"
    )


@router.post("/login", summary="Iniciar sesión")
async def login(datos: LoginEntrada, request: Request, response: Response, session: DB) -> TokenRespuesta:
    resultado = await servicio.login(session, datos, ip_cliente(request), request.headers.get("user-agent"))
    _guardar_cookie(response, resultado.refresh_token)  # type: ignore[arg-type]
    return resultado.respuesta


@router.post("/refresh", summary="Renovar el access token usando la cookie de sesión")
async def refresh(
    request: Request, response: Response, session: DB, refresh_token: CookieRefresh = None
) -> TokenRespuesta:
    try:
        resultado = await servicio.refrescar(
            session, refresh_token, ip_cliente(request), request.headers.get("user-agent")
        )
    except NoAutenticado as exc:
        # Se responde aquí (y no con el manejador global) para poder borrar la cookie inválida
        error = JSONResponse(status_code=exc.status_code, content={"detalle": exc.mensaje, "codigo": exc.codigo})
        _borrar_cookie(error)
        return error  # type: ignore[return-value]
    if resultado.refresh_token:
        _guardar_cookie(response, resultado.refresh_token)
    return resultado.respuesta


@router.post("/logout", summary="Cerrar sesión")
async def logout(request: Request, response: Response, session: DB, refresh_token: CookieRefresh = None) -> Mensaje:
    await servicio.logout(session, refresh_token, ip_cliente(request))
    _borrar_cookie(response)
    return Mensaje(mensaje="Sesión cerrada")


@router.get("/me", summary="Datos del usuario autenticado")
async def me(ctx: Contexto) -> UsuarioSesion:
    return servicio.construir_sesion(ctx.usuario, ctx.sucursal_id)


@router.post("/cambiar-sucursal", summary="Trabajar en otra sucursal")
async def cambiar_sucursal(
    datos: CambiarSucursalEntrada, ctx: Contexto, session: DB, refresh_token: CookieRefresh = None
) -> TokenRespuesta:
    return await servicio.cambiar_sucursal(session, ctx, refresh_token, datos.sucursal_id)


@router.post("/cambiar-password", summary="Cambiar la contraseña propia", status_code=status.HTTP_200_OK)
async def cambiar_password(
    datos: CambiarPasswordEntrada, ctx: Contexto, session: DB, refresh_token: CookieRefresh = None
) -> TokenRespuesta:
    return await servicio.cambiar_password(session, ctx, datos, refresh_token)
