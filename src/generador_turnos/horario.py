"""Reglas del problema de asignación de turnos.

Este módulo no sabe nada del algoritmo genético ni de la API: solo define qué
es un problema de turnos, cuándo tiene solución posible y cuántas reglas
incumple una asignación concreta.

Una asignación (cromosoma) es una lista de enteros con un gen por cada cupo:
los primeros ``personas_por_turno`` genes son el primer turno, los siguientes
el segundo, y así sucesivamente. El valor de cada gen es el índice de la
persona asignada a ese cupo.
"""

from collections import Counter
from dataclasses import dataclass
from itertools import pairwise

DIAS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")


class ProblemaInvalidoError(ValueError):
    """El problema está mal planteado o no puede tener un horario válido."""


@dataclass(frozen=True)
class Problema:
    """Parámetros de un problema de asignación de turnos."""

    personas: tuple[str, ...]
    dias: int
    turnos_por_dia: int
    personas_por_turno: int
    max_turnos_por_persona: int
    evitar_turnos_consecutivos: bool = False

    @property
    def n_personas(self) -> int:
        return len(self.personas)

    @property
    def n_turnos(self) -> int:
        return self.dias * self.turnos_por_dia

    @property
    def n_genes(self) -> int:
        return self.n_turnos * self.personas_por_turno

    @property
    def demanda(self) -> int:
        """Total de cupos que hay que cubrir en la semana."""
        return self.n_turnos * self.personas_por_turno

    @property
    def capacidad(self) -> int:
        """Total de turnos que el equipo puede trabajar sin superar el máximo."""
        return self.n_personas * self.max_turnos_por_persona

    def validar(self) -> None:
        """Lanza ``ProblemaInvalidoError`` si el problema no puede resolverse."""
        if self.n_personas == 0:
            raise ProblemaInvalidoError("Debe indicar al menos una persona.")
        if len(set(self.personas)) != self.n_personas:
            raise ProblemaInvalidoError("Hay nombres de personas repetidos.")
        if min(self.dias, self.turnos_por_dia, self.personas_por_turno) < 1:
            raise ProblemaInvalidoError("Días, turnos por día y personas por turno deben ser ≥ 1.")
        if self.max_turnos_por_persona < 1:
            raise ProblemaInvalidoError("El máximo de turnos por persona debe ser ≥ 1.")
        if self.personas_por_turno > self.n_personas:
            raise ProblemaInvalidoError(
                f"Cada turno necesita {self.personas_por_turno} personas distintas, "
                f"pero el equipo solo tiene {self.n_personas}."
            )
        if self.capacidad < self.demanda:
            raise ProblemaInvalidoError(
                f"No hay capacidad suficiente: se deben cubrir {self.demanda} cupos y el "
                f"equipo solo puede trabajar {self.capacidad} "
                f"({self.n_personas} personas × {self.max_turnos_por_persona} turnos)."
            )
        if self.evitar_turnos_consecutivos and self.n_turnos > 1:
            if self.n_personas < 2 * self.personas_por_turno:
                raise ProblemaInvalidoError(
                    "Para evitar turnos consecutivos se necesitan al menos "
                    f"{2 * self.personas_por_turno} personas (el doble de las que cubren un turno)."
                )
            max_alternando = (self.n_turnos + 1) // 2
            capacidad = self.n_personas * min(self.max_turnos_por_persona, max_alternando)
            if capacidad < self.demanda:
                raise ProblemaInvalidoError(
                    "No hay capacidad suficiente si nadie puede trabajar dos turnos seguidos: "
                    f"se deben cubrir {self.demanda} cupos y el equipo solo alcanza {capacidad}."
                )

    def nombres_turnos(self) -> list[str]:
        """Nombres legibles de los turnos: ``Lun-1``, ``Lun-2``, ``Mar-1``…"""
        nombres = []
        for d in range(self.dias):
            dia = DIAS[d] if self.dias <= len(DIAS) else f"Día{d + 1}"
            for t in range(self.turnos_por_dia):
                nombres.append(f"{dia}-{t + 1}")
        return nombres


@dataclass(frozen=True)
class Violaciones:
    """Número de veces que una asignación incumple cada regla."""

    repeticiones: int
    excesos: int
    consecutivos: int

    @property
    def total(self) -> int:
        return self.repeticiones + self.excesos + self.consecutivos


def separar_turnos(problema: Problema, cromosoma: list[int]) -> list[list[int]]:
    """Divide el cromosoma en una lista de turnos (cada uno, una lista de personas)."""
    if len(cromosoma) != problema.n_genes:
        raise ValueError(
            f"El cromosoma tiene {len(cromosoma)} genes y se esperaban {problema.n_genes}."
        )
    k = problema.personas_por_turno
    return [cromosoma[i : i + k] for i in range(0, len(cromosoma), k)]


def contar_violaciones(problema: Problema, cromosoma: list[int]) -> Violaciones:
    """Cuenta exactamente cuántas veces se incumple cada regla.

    - Repeticiones: en cada turno, cada aparición extra de una misma persona.
    - Excesos: por cada persona, cada turno por encima de su máximo.
    - Consecutivos: por cada par de turnos seguidos, cada persona que está en
      ambos (solo si el problema pide evitarlos).

    Si el total es 0, ninguna regla se incumple y el horario es válido.
    """
    turnos = separar_turnos(problema, cromosoma)

    repeticiones = sum(len(turno) - len(set(turno)) for turno in turnos)

    turnos_por_persona = Counter(cromosoma)
    excesos = sum(max(0, n - problema.max_turnos_por_persona) for n in turnos_por_persona.values())

    consecutivos = 0
    if problema.evitar_turnos_consecutivos:
        consecutivos = sum(
            len(set(actual) & set(siguiente)) for actual, siguiente in pairwise(turnos)
        )

    return Violaciones(repeticiones, excesos, consecutivos)
