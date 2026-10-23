from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

JWT_SECRET_EJEMPLO = "cambiar-esta-clave-en-produccion"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Aplicación
    APP_NOMBRE: str = "Minimarket POS"
    ENTORNO: Literal["desarrollo", "pruebas", "produccion"] = "desarrollo"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ZONA_HORARIA: str = "America/Lima"

    # Base de datos
    DATABASE_URL: str = "mysql+aiomysql://minimarket:minimarket@localhost:3306/minimarket?charset=utf8mb4"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Seguridad / JWT
    JWT_SECRET: str = JWT_SECRET_EJEMPLO
    JWT_ALGORITMO: str = "HS256"
    ACCESS_TOKEN_MINUTOS: int = 30
    REFRESH_TOKEN_DIAS: int = 7
    # Segundos en que un refresh token recién rotado aún se acepta (peticiones simultáneas / varias pestañas)
    REFRESH_GRACIA_SEGUNDOS: int = 30
    COOKIE_REFRESH_NOMBRE: str = "mm_refresh"
    COOKIE_SECURE: bool = False  # True en producción con HTTPS

    # CORS: lista separada por comas
    CORS_ORIGENES: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Usuario administrador inicial (seed)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin123*"
    ADMIN_EMAIL: str = "admin@minimarket.local"
    ADMIN_NOMBRE: str = "Administrador del Sistema"

    # Valores por defecto del negocio
    IGV_PORCENTAJE: float = 18.0

    # Archivos subidos (fotos de productos). Debe incluirse en los respaldos.
    MEDIA_DIR: str = "media"

    @field_validator("CORS_ORIGENES", mode="before")
    @classmethod
    def _separar_origenes(cls, valor: str | list[str]) -> list[str]:
        if isinstance(valor, str):
            return [o.strip() for o in valor.split(",") if o.strip()]
        return valor

    @model_validator(mode="after")
    def _exigir_configuracion_segura(self) -> Settings:
        """En producción el sistema no arranca con valores de ejemplo: cualquiera podría falsificar sesiones."""
        if self.ENTORNO != "produccion":
            return self
        problemas = []
        if self.JWT_SECRET == JWT_SECRET_EJEMPLO or len(self.JWT_SECRET) < 32:
            problemas.append(
                "JWT_SECRET es el de ejemplo o tiene menos de 32 caracteres "
                '(genere uno con: python -c "import secrets; print(secrets.token_urlsafe(64))")'
            )
        if not self.COOKIE_SECURE:
            problemas.append("COOKIE_SECURE debe ser true (la cookie de sesión solo debe viajar por HTTPS)")
        if self.DEBUG:
            problemas.append("DEBUG debe ser false")
        if problemas:
            raise ValueError("Configuración insegura para producción:\n- " + "\n- ".join(problemas))
        return self

    @property
    def es_produccion(self) -> bool:
        return self.ENTORNO == "produccion"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
