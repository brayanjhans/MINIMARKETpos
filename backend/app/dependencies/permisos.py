from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends

from app.dependencies.auth import ContextoUsuario, get_contexto


def requiere_permiso(*permisos: str) -> Callable[..., Awaitable[ContextoUsuario]]:
    """Dependencia que exige TODOS los permisos indicados.

    Uso:  ctx: Annotated[ContextoUsuario, Depends(requiere_permiso("usuarios.crear"))]
    """

    async def _verificar(ctx: Annotated[ContextoUsuario, Depends(get_contexto)]) -> ContextoUsuario:
        for permiso in permisos:
            ctx.exigir(permiso)
        return ctx

    return _verificar


def ConPermiso(*permisos: str) -> type[ContextoUsuario]:  # noqa: N802 (se usa como tipo en las firmas)
    """Atajo para anotar parámetros:  ctx: ConPermiso("usuarios.ver")"""
    return Annotated[ContextoUsuario, Depends(requiere_permiso(*permisos))]  # type: ignore[return-value]
