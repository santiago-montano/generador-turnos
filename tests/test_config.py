"""Pruebas de la configuración: el secreto se lee del entorno y se valida."""

import pytest

from generador_turnos.config import VARIABLE_CLAVE, ConfiguracionError, cargar_configuracion


def test_lee_la_clave_de_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv(VARIABLE_CLAVE, "  clave-de-prueba-123  ")
    assert cargar_configuracion().clave_acceso == "clave-de-prueba-123"


def test_falla_con_un_mensaje_claro_si_falta_la_clave(monkeypatch):
    monkeypatch.delenv(VARIABLE_CLAVE, raising=False)
    with pytest.raises(ConfiguracionError, match=r"\.env\.example"):
        cargar_configuracion()


def test_rechaza_una_clave_demasiado_corta(monkeypatch):
    monkeypatch.setenv(VARIABLE_CLAVE, "abc")
    with pytest.raises(ConfiguracionError, match="al menos 8"):
        cargar_configuracion()
