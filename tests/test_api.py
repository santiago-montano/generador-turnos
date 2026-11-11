"""Pruebas del servicio: salud, protección con clave y generación de horarios."""

from collections import Counter

import pytest
from fastapi.testclient import TestClient

from generador_turnos.api import app
from generador_turnos.config import VARIABLE_CLAVE, ConfiguracionError

CLAVE = "clave-solo-para-pruebas"
ENCABEZADO = {"X-Clave-Acceso": CLAVE}
SOLICITUD = {
    "personas": ["Ana", "Luis", "Marta", "Pedro", "Sofía", "Camilo", "Laura"],
    "dias": 7,
    "turnos_por_dia": 2,
    "personas_por_turno": 3,
    "max_turnos_por_persona": 6,
    "semilla": 7,
}


@pytest.fixture
def cliente(monkeypatch):
    monkeypatch.setenv(VARIABLE_CLAVE, CLAVE)
    with TestClient(app) as cliente:
        yield cliente


def test_health_responde_sin_clave(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"


def test_la_pagina_principal_muestra_el_formulario(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "Generador de turnos" in respuesta.text


@pytest.mark.parametrize("encabezado", [{}, {"X-Clave-Acceso": "clave-incorrecta"}])
def test_rechaza_solicitudes_sin_la_clave_correcta(cliente, encabezado):
    respuesta = cliente.post("/horarios", json=SOLICITUD, headers=encabezado)
    assert respuesta.status_code == 401


def test_genera_un_horario_valido_con_los_nombres_del_equipo(cliente):
    respuesta = cliente.post("/horarios", json=SOLICITUD, headers=ENCABEZADO)

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["valido"] is True
    assert datos["violaciones"] == {"repeticiones": 0, "excesos": 0, "consecutivos": 0}
    assert len(datos["turnos"]) == 14
    assert datos["turnos"][0]["nombre"] == "Lun-1"
    for turno in datos["turnos"]:
        assert len(set(turno["personas"])) == 3
        assert set(turno["personas"]) <= set(SOLICITUD["personas"])
    # El conteo que informa la API coincide con el horario devuelto
    conteo = Counter(nombre for turno in datos["turnos"] for nombre in turno["personas"])
    assert datos["turnos_por_persona"] == dict(conteo)
    assert max(conteo.values()) <= 6


def test_explica_por_que_un_problema_no_tiene_solucion(cliente):
    imposible = {**SOLICITUD, "max_turnos_por_persona": 2}
    respuesta = cliente.post("/horarios", json=imposible, headers=ENCABEZADO)
    assert respuesta.status_code == 422
    assert "capacidad" in respuesta.json()["detail"]


def test_rechaza_valores_fuera_de_los_limites(cliente):
    excesivo = {**SOLICITUD, "turnos_por_dia": 50}
    respuesta = cliente.post("/horarios", json=excesivo, headers=ENCABEZADO)
    assert respuesta.status_code == 422


def test_el_servicio_no_arranca_sin_clave_de_acceso(monkeypatch):
    monkeypatch.delenv(VARIABLE_CLAVE, raising=False)
    with pytest.raises(ConfiguracionError), TestClient(app):
        pass
