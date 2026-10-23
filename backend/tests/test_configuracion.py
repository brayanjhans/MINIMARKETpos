"""Configuración segura y clasificación de errores de base de datos."""

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import Settings
from app.core.excepciones import _es_error_de_conexion

CLAVE_FUERTE = "x" * 48


def test_produccion_no_arranca_con_la_clave_de_ejemplo():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(ENTORNO="produccion", COOKIE_SECURE=True, _env_file=None)


def test_produccion_exige_cookie_segura_y_sin_debug():
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(ENTORNO="produccion", JWT_SECRET=CLAVE_FUERTE, COOKIE_SECURE=False, _env_file=None)
    with pytest.raises(ValidationError, match="DEBUG"):
        Settings(ENTORNO="produccion", JWT_SECRET=CLAVE_FUERTE, COOKIE_SECURE=True, DEBUG=True, _env_file=None)


def test_produccion_con_configuracion_correcta():
    s = Settings(ENTORNO="produccion", JWT_SECRET=CLAVE_FUERTE, COOKIE_SECURE=True, _env_file=None)
    assert s.es_produccion


def test_desarrollo_permite_valores_de_ejemplo():
    assert Settings(ENTORNO="desarrollo", _env_file=None).JWT_SECRET


class _ErrorMySQL(Exception):
    pass


def test_clasifica_errores_de_conexion_y_de_programacion():
    caida = OperationalError("SELECT 1", {}, _ErrorMySQL(2003, "Can't connect to MySQL server"))
    sintaxis = ProgrammingError("SELECT", {}, _ErrorMySQL(1064, "You have an error in your SQL syntax"))
    assert _es_error_de_conexion(caida)
    assert not _es_error_de_conexion(sintaxis)
