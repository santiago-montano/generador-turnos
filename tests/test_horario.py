"""Pruebas de las reglas del problema: validación y conteo de violaciones."""

import pytest

from generador_turnos.horario import (
    Problema,
    ProblemaInvalidoError,
    contar_violaciones,
    separar_turnos,
)


def problema_base(**cambios) -> Problema:
    """Caso de la Actividad 2: 7 personas, 14 turnos, 3 por turno, máximo 6."""
    parametros = {
        "personas": tuple(f"P{i}" for i in range(7)),
        "dias": 7,
        "turnos_por_dia": 2,
        "personas_por_turno": 3,
        "max_turnos_por_persona": 6,
    }
    parametros.update(cambios)
    return Problema(**parametros)


def test_el_caso_base_no_tiene_holgura():
    problema = problema_base()
    assert problema.n_turnos == 14
    assert problema.n_genes == 42
    assert problema.demanda == problema.capacidad == 42


def test_cuenta_cada_repeticion_dentro_de_un_turno():
    problema = problema_base(dias=1, turnos_por_dia=3)
    # [4 0 2] sin repetición, [1 4 6] sin repetición, [3 3 5] una repetición
    violaciones = contar_violaciones(problema, [4, 0, 2, 1, 4, 6, 3, 3, 5])
    assert violaciones.repeticiones == 1
    assert violaciones.excesos == 0
    assert violaciones.total == 1


def test_un_turno_con_la_misma_persona_tres_veces_cuenta_dos_repeticiones():
    problema = problema_base(dias=1, turnos_por_dia=1)
    assert contar_violaciones(problema, [3, 3, 3]).repeticiones == 2


def test_cuenta_los_excesos_sobre_el_maximo_por_persona():
    problema = problema_base()
    # La persona 0 ocupa los 42 cupos: 14 turnos × 2 repeticiones y 42 − 6 excesos
    violaciones = contar_violaciones(problema, [0] * 42)
    assert violaciones.repeticiones == 28
    assert violaciones.excesos == 36


def test_un_horario_construido_a_mano_no_tiene_violaciones():
    problema = problema_base()
    # Rotación: el turno t lo cubren las personas t, t+1 y t+2 (módulo 7)
    cromosoma = [(t + j) % 7 for t in range(14) for j in range(3)]
    assert contar_violaciones(problema, cromosoma).total == 0


def test_los_turnos_consecutivos_solo_se_cuentan_si_se_piden():
    cromosoma = [(t + j) % 7 for t in range(14) for j in range(3)]
    sin_regla = contar_violaciones(problema_base(), cromosoma)
    con_regla = contar_violaciones(problema_base(evitar_turnos_consecutivos=True), cromosoma)
    assert sin_regla.consecutivos == 0
    # En la rotación, cada turno comparte 2 personas con el siguiente: 13 pares × 2
    assert con_regla.consecutivos == 26


def test_separar_turnos_rechaza_un_cromosoma_de_tamano_incorrecto():
    with pytest.raises(ValueError, match="42"):
        separar_turnos(problema_base(), [0, 1, 2])


@pytest.mark.parametrize(
    ("cambios", "fragmento"),
    [
        ({"max_turnos_por_persona": 5}, "capacidad"),
        ({"personas_por_turno": 8}, "personas distintas"),
        ({"personas": ("Ana", "Ana", "Luis")}, "repetidos"),
        ({"personas": ()}, "al menos una persona"),
        ({"dias": 0}, "≥ 1"),
        (
            {
                "evitar_turnos_consecutivos": True,
                "personas": ("A", "B", "C", "D", "E"),
                "max_turnos_por_persona": 9,
            },
            "doble",
        ),
    ],
)
def test_validar_rechaza_problemas_sin_solucion(cambios, fragmento):
    with pytest.raises(ProblemaInvalidoError, match=fragmento):
        problema_base(**cambios).validar()


def test_validar_acepta_el_caso_base():
    problema_base().validar()


def test_los_nombres_de_los_turnos_siguen_los_dias_de_la_semana():
    nombres = problema_base().nombres_turnos()
    assert nombres[:3] == ["Lun-1", "Lun-2", "Mar-1"]
    assert nombres[-1] == "Dom-2"
    assert len(nombres) == 14
