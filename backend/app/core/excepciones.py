"""Excepciones de negocio y manejadores centralizados de errores (mensajes en español)."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("minimarket")


class ErrorNegocio(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    codigo: str = "error_negocio"

    def __init__(self, mensaje: str, *, codigo: str | None = None, datos: dict[str, Any] | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo
        self.datos = datos


class NoEncontrado(ErrorNegocio):
    status_code = status.HTTP_404_NOT_FOUND
    codigo = "no_encontrado"


class Conflicto(ErrorNegocio):
    status_code = status.HTTP_409_CONFLICT
    codigo = "conflicto"


class NoAutenticado(ErrorNegocio):
    status_code = status.HTTP_401_UNAUTHORIZED
    codigo = "no_autenticado"


class PermisoDenegado(ErrorNegocio):
    status_code = status.HTTP_403_FORBIDDEN
    codigo = "permiso_denegado"


class DemasiadosIntentos(ErrorNegocio):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    codigo = "demasiados_intentos"


class ValidacionNegocio(ErrorNegocio):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    codigo = "validacion"


# Traducción de los tipos de error de Pydantic v2
_MENSAJES_VALIDACION: dict[str, str] = {
    "missing": "Este campo es obligatorio",
    "string_too_short": "Debe tener al menos {min_length} caracteres",
    "string_too_long": "Debe tener como máximo {max_length} caracteres",
    "string_type": "Debe ser un texto",
    "string_pattern_mismatch": "El formato no es válido",
    "int_type": "Debe ser un número entero",
    "int_parsing": "Debe ser un número entero",
    "float_type": "Debe ser un número",
    "float_parsing": "Debe ser un número",
    "decimal_type": "Debe ser un número decimal",
    "decimal_parsing": "Debe ser un número decimal",
    "decimal_max_digits": "Tiene demasiados dígitos",
    "decimal_max_places": "Tiene demasiados decimales (máximo {decimal_places})",
    "bool_type": "Debe ser verdadero o falso",
    "bool_parsing": "Debe ser verdadero o falso",
    "greater_than": "Debe ser mayor que {gt}",
    "greater_than_equal": "Debe ser mayor o igual que {ge}",
    "less_than": "Debe ser menor que {lt}",
    "less_than_equal": "Debe ser menor o igual que {le}",
    "enum": "Valor no permitido. Opciones: {expected}",
    "literal_error": "Valor no permitido. Opciones: {expected}",
    "date_parsing": "Fecha no válida (formato AAAA-MM-DD)",
    "date_from_datetime_parsing": "Fecha no válida (formato AAAA-MM-DD)",
    "datetime_parsing": "Fecha y hora no válidas",
    "datetime_from_date_parsing": "Fecha y hora no válidas",
    "value_error": "{error}",
    "list_type": "Debe ser una lista",
    "too_short": "Debe tener al menos {min_length} elemento(s)",
    "too_long": "Debe tener como máximo {max_length} elemento(s)",
    "json_invalid": "El cuerpo de la petición no es un JSON válido",
    "model_attributes_type": "Formato de datos no válido",
    "dict_type": "Debe ser un objeto",
}


def _traducir_error(error: dict[str, Any]) -> dict[str, Any]:
    tipo = error.get("type", "")
    ctx = error.get("ctx") or {}
    plantilla = _MENSAJES_VALIDACION.get(tipo)
    mensaje = error.get("msg", "Valor no válido")
    if plantilla:
        try:
            mensaje = plantilla.format(**{k: str(v) for k, v in ctx.items()})
        except (KeyError, IndexError):
            pass
    if tipo == "value_error" and mensaje.startswith("Value error, "):
        mensaje = mensaje.removeprefix("Value error, ")
    # Se quita el prefijo "body"/"query" para mostrar solo el nombre del campo
    loc = [str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path", "header")]
    return {"campo": ".".join(loc) or None, "mensaje": mensaje}


def _respuesta(status_code: int, detalle: str, codigo: str, **extra: Any) -> JSONResponse:
    contenido = {"detalle": detalle, "codigo": codigo, **{k: v for k, v in extra.items() if v is not None}}
    return JSONResponse(status_code=status_code, content=jsonable_encoder(contenido))


_MENSAJES_HTTP = {
    401: "No autenticado",
    403: "No tiene permiso para realizar esta acción",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    429: "Demasiadas solicitudes, intente nuevamente en unos segundos",
}
_DETALLES_INGLES = {"Not Found", "Unauthorized", "Forbidden", "Method Not Allowed", "Too Many Requests"}


# Códigos de error de MySQL -> (status HTTP, mensaje, código)
_ERRORES_MYSQL: dict[int, tuple[int, str, str]] = {
    1062: (409, "Ya existe un registro con esos datos (valor duplicado)", "duplicado"),
    1451: (409, "El registro está siendo usado por otros datos y no se puede eliminar o modificar", "en_uso"),
    1452: (409, "El registro relacionado no existe", "referencia_invalida"),
    1048: (422, "Falta un dato obligatorio", "dato_obligatorio"),
    3819: (409, "Los datos no cumplen las reglas del sistema (por ejemplo, stock o montos negativos)", "regla_datos"),
    1264: (422, "Un valor numérico está fuera del rango permitido", "fuera_de_rango"),
    1406: (422, "Un texto excede la longitud permitida", "texto_muy_largo"),
    1213: (409, "La operación entró en conflicto con otra simultánea. Intente nuevamente.", "concurrencia"),
    1205: (409, "La operación tardó demasiado esperando a otra. Intente nuevamente.", "concurrencia"),
    # SIGNAL de los triggers (ej. el kardex es inmutable)
    1644: (409, "La operación no está permitida: el historial de movimientos no se puede modificar", "inmutable"),
}


# Códigos de MySQL que significan que no hay conexión (servidor caído, conexión perdida o rechazada)
_ERRORES_CONEXION_MYSQL = {1040, 1045, 1053, 2002, 2003, 2005, 2006, 2013, 2055}


def _es_error_de_conexion(exc: DBAPIError) -> bool:
    if exc.connection_invalidated or isinstance(exc.orig, ConnectionError | OSError):
        return True
    args = getattr(exc.orig, "args", ())
    return bool(args) and isinstance(args[0], int) and args[0] in _ERRORES_CONEXION_MYSQL


def _clasificar_error_bd(exc: DBAPIError) -> tuple[int, str, str] | None:
    args = getattr(exc.orig, "args", ())
    if args and isinstance(args[0], int) and args[0] in _ERRORES_MYSQL:
        return _ERRORES_MYSQL[args[0]]
    if isinstance(exc, IntegrityError):
        return 409, "No se pudo guardar la información por un conflicto de datos", "integridad"
    return None


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def _error_negocio(_: Request, exc: ErrorNegocio) -> JSONResponse:
        return _respuesta(exc.status_code, exc.mensaje, exc.codigo, datos=exc.datos)

    @app.exception_handler(RequestValidationError)
    async def _error_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        errores = [_traducir_error(e) for e in exc.errors()]
        return _respuesta(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Los datos enviados no son válidos",
            "validacion",
            errores=errores,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _error_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Los mensajes por defecto de Starlette (en inglés) se reemplazan por su versión en español
        detalle = _MENSAJES_HTTP.get(exc.status_code, str(exc.detail))
        if isinstance(exc.detail, str) and exc.detail not in _DETALLES_INGLES:
            detalle = exc.detail
        respuesta = _respuesta(exc.status_code, detalle, "http_error")
        if exc.headers:
            respuesta.headers.update(exc.headers)
        return respuesta

    @app.exception_handler(DBAPIError)
    async def _error_bd(_: Request, exc: DBAPIError) -> JSONResponse:
        # MySQL reporta algunas violaciones de datos (ej. CHECK) como OperationalError,
        # por eso se clasifica por código de error y no solo por la clase de excepción.
        clasificado = _clasificar_error_bd(exc)
        if clasificado:
            logger.warning("Error de integridad: %s", exc.orig)
            status_code, mensaje, codigo = clasificado
            return _respuesta(status_code, mensaje, codigo)
        if _es_error_de_conexion(exc):
            logger.error("Sin conexión con la base de datos: %s", exc.orig)
            return _respuesta(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "No se pudo conectar con la base de datos. Intente nuevamente en unos segundos.",
                "base_de_datos_no_disponible",
            )
        # Error de programación o de datos inesperado: es un fallo del sistema, no de la red
        logger.exception("Error de base de datos", exc_info=exc)
        return _respuesta(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Ocurrió un error interno al procesar la operación. Si se repite, contacte al administrador.",
            "error_base_de_datos",
        )

    @app.exception_handler(Exception)
    async def _error_inesperado(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado", exc_info=exc)
        return _respuesta(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Ocurrió un error inesperado. Si el problema persiste, contacte al administrador.",
            "error_interno",
        )
