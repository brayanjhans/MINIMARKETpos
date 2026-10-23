from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Convención de nombres para que Alembic genere nombres de índices/restricciones estables
CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)
    # Tras INSERT/UPDATE se leen los valores generados por la BD (creado_en, actualizado_en...).
    # Sin esto, acceder a ellos dispararía una carga perezosa, que en modo async no está permitida.
    __mapper_args__ = {"eager_defaults": True}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    # MySQL cierra conexiones inactivas (wait_timeout); se reciclan antes de que ocurra
    pool_recycle=1800,
    # Igual que PostgreSQL: cada SELECT ve datos confirmados; el stock se protege con FOR UPDATE
    isolation_level="READ COMMITTED",
    # Todas las fechas se manejan en UTC dentro de la base de datos
    connect_args={"init_command": "SET time_zone = '+00:00'"},
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Sesión por petición. Si ocurre un error se hace rollback de todo."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
