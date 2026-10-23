import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings

TipoToken = Literal["access", "refresh", "autorizacion"]

# bcrypt solo considera los primeros 72 bytes de la contraseña
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    datos = password.encode("utf-8")
    if len(datos) > BCRYPT_MAX_BYTES:
        raise ValueError("La contraseña es demasiado larga (máximo 72 bytes).")
    return bcrypt.hashpw(datos, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    datos = password.encode("utf-8")
    if len(datos) > BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(datos, password_hash.encode("utf-8"))
    except ValueError:
        return False


def _crear_token(sub: str | int, tipo: TipoToken, expira: datetime, extra: dict[str, Any] | None) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(sub),
        "tipo": tipo,
        "jti": jti,
        "iat": datetime.now(UTC),
        "exp": expira,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITMO), jti


def crear_access_token(sub: str | int, extra: dict[str, Any] | None = None) -> str:
    expira = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTOS)
    token, _ = _crear_token(sub, "access", expira, extra)
    return token


def segundos_access_token() -> int:
    return settings.ACCESS_TOKEN_MINUTOS * 60


def crear_refresh_token(sub: str | int) -> tuple[str, str, datetime]:
    """Devuelve (token, jti, fecha_expiración). El jti se guarda hasheado en BD."""
    expira = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_DIAS)
    token, jti = _crear_token(sub, "refresh", expira, None)
    return token, jti, expira


def crear_token_autorizacion(supervisor_id: int, extra: dict[str, Any], minutos: int = 3) -> tuple[str, str]:
    """Permiso de un supervisor para UNA acción de otro usuario (anular, descuento...). Vive pocos minutos."""
    return _crear_token(supervisor_id, "autorizacion", datetime.now(UTC) + timedelta(minutes=minutos), extra)


def decodificar_token(token: str, tipo_esperado: TipoToken) -> dict[str, Any]:
    """Lanza jwt.PyJWTError si el token es inválido, expiró o no es del tipo esperado."""
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITMO],
        options={"require": ["exp", "sub", "tipo", "jti"]},
    )
    if payload.get("tipo") != tipo_esperado:
        raise jwt.InvalidTokenError("Tipo de token incorrecto")
    return payload


def hash_identificador(valor: str) -> str:
    """Hash SHA-256 para guardar identificadores de tokens sin exponerlos."""
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()
