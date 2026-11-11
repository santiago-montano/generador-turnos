"""Pruebas del algoritmo genético.

El horario se verifica de forma independiente (contando con ``Counter``), sin
reutilizar la función de violaciones que el propio algoritmo optimiza.
"""

from collections import Counter
from itertools import pairwise

import pytest

from generador_turnos.genetico import generar_horario
from generador_turnos.horario import Problema, ProblemaInvalidoError


def problema(**cambios) -> Problema:
    parametros = {
        "personas": tuple(f"P{i}" for i in range(7)),
        "dias": 7,
        "turnos_por_dia": 2,
        "personas_por_turno": 3,
        "max_turnos_por_persona": 6,
    }
    parametros.update(cambios)
    return Problema(**parametros)


def turnos_de(resultado, por_turno: int) -> list[list[int]]:
    genes = resultado.cromosoma
    return [genes[i : i + por_turno] for i in range(0, len(genes), por_turno)]


@pytest.mark.parametrize("semilla", [0, 1, 2, 3, 4])
def test_encuentra_un_horario_valido_en_el_caso_sin_holgura(semilla):
    resultado = generar_horario(problema(), semilla)

    assert resultado.valido
    turnos = turnos_de(resultado, 3)
    assert len(turnos) == 14
    # Regla 1: tres personas distintas en cada turno
    assert all(len(set(turno)) == 3 for turno in turnos)
    # Regla 2: nadie supera 6 turnos (sin holgura, todos trabajan exactamente 6)
    assert set(Counter(resultado.cromosoma).values()) == {6}


def test_la_misma_semilla_produce_el_mismo_horario():
    primero = generar_horario(problema(), semilla=123)
    segundo = generar_horario(problema(), semilla=123)
    assert primero.cromosoma == segundo.cromosoma
    assert primero.generaciones == segundo.generaciones


def test_sin_semilla_informa_la_semilla_usada_para_poder_reproducirlo():
    resultado = generar_horario(problema(max_turnos_por_persona=7))
    repetido = generar_horario(problema(max_turnos_por_persona=7), resultado.semilla)
    assert repetido.cromosoma == resultado.cromosoma


def test_respeta_la_regla_de_turnos_consecutivos_cuando_se_pide():
    resultado = generar_horario(
        problema(max_turnos_por_persona=7, evitar_turnos_consecutivos=True), semilla=1
    )

    assert resultado.valido
    turnos = turnos_de(resultado, 3)
    for actual, siguiente in pairwise(turnos):
        assert not set(actual) & set(siguiente)


def test_solo_asigna_personas_que_existen():
    equipo = ("Ana", "Luis", "Marta", "Pedro")
    resultado = generar_horario(problema(personas=equipo, max_turnos_por_persona=11), semilla=5)
    assert resultado.valido
    assert set(resultado.cromosoma) <= {0, 1, 2, 3}


def test_no_intenta_resolver_un_problema_imposible():
    with pytest.raises(ProblemaInvalidoError):
        generar_horario(problema(max_turnos_por_persona=2), semilla=0)
