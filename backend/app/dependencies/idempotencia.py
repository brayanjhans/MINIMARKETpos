from typing import Annotated

from fastapi import Header

# El cliente genera una clave única por operación (ej. un UUID al abrir el formulario) y la reenvía si reintenta.
# La misma clave nunca ejecuta la operación dos veces.
ClaveIdempotencia = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Clave única de la operación (evita duplicados por doble clic o reintentos)",
    ),
]
