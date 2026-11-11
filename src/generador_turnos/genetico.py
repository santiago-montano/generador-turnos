"""Algoritmo genético que busca un horario sin violaciones.

Usa los mismos operadores que se estudiaron en la Unidad 2: selección por
torneo, cruce uniforme, mutación aleatoria de un gen y elitismo. Está escrito
en Python puro para que el servicio no dependa de librerías numéricas.
"""

import random
from dataclasses import dataclass

from generador_turnos.horario import Problema, Violaciones, contar_violaciones

TAMANO_POBLACION = 50
TAMANO_TORNEO = 3
ELITISMO = 2
MAX_GENERACIONES = 400
MAX_REINICIOS = 12


@dataclass(frozen=True)
class Resultado:
    """Mejor horario encontrado por el algoritmo."""

    cromosoma: list[int]
    violaciones: Violaciones
    generaciones: int
    reinicios: int
    semilla: int

    @property
    def valido(self) -> bool:
        return self.violaciones.total == 0


def _torneo(poblacion: list[list[int]], costos: list[int], rng: random.Random) -> list[int]:
    """Elige el mejor entre ``TAMANO_TORNEO`` individuos tomados al azar."""
    candidatos = rng.sample(range(len(poblacion)), TAMANO_TORNEO)
    return poblacion[min(candidatos, key=lambda i: costos[i])]


def _cruce_uniforme(padre: list[int], madre: list[int], rng: random.Random) -> list[int]:
    """Cada gen del hijo viene de uno u otro progenitor con igual probabilidad."""
    return [a if rng.random() < 0.5 else b for a, b in zip(padre, madre, strict=True)]


def _mutar(hijo: list[int], n_personas: int, rng: random.Random) -> None:
    """Reemplaza un gen al azar por otra persona (mutación de un solo gen)."""
    hijo[rng.randrange(len(hijo))] = rng.randrange(n_personas)


def _evolucionar(problema: Problema, rng: random.Random) -> tuple[list[int], Violaciones, int]:
    """Ejecuta una corrida del algoritmo y devuelve el mejor individuo."""

    def costo(cromosoma: list[int]) -> int:
        return contar_violaciones(problema, cromosoma).total

    poblacion = [
        [rng.randrange(problema.n_personas) for _ in range(problema.n_genes)]
        for _ in range(TAMANO_POBLACION)
    ]
    costos = [costo(c) for c in poblacion]

    generacion = 0
    while min(costos) > 0 and generacion < MAX_GENERACIONES:
        generacion += 1
        orden = sorted(range(TAMANO_POBLACION), key=lambda i: costos[i])
        nueva = [poblacion[i][:] for i in orden[:ELITISMO]]
        while len(nueva) < TAMANO_POBLACION:
            hijo = _cruce_uniforme(
                _torneo(poblacion, costos, rng), _torneo(poblacion, costos, rng), rng
            )
            _mutar(hijo, problema.n_personas, rng)
            nueva.append(hijo)
        poblacion = nueva
        costos = [costo(c) for c in poblacion]

    mejor = min(range(TAMANO_POBLACION), key=lambda i: costos[i])
    return poblacion[mejor], contar_violaciones(problema, poblacion[mejor]), generacion


def generar_horario(problema: Problema, semilla: int | None = None) -> Resultado:
    """Busca un horario válido para ``problema``.

    Si una corrida se estanca sin llegar a cero violaciones, se reinicia con
    una población nueva (hasta ``MAX_REINICIOS`` veces). Devuelve siempre el
    mejor horario encontrado; ``Resultado.valido`` indica si cumple todas las
    reglas. Con la misma semilla el resultado es idéntico.
    """
    problema.validar()
    if semilla is None:
        semilla = random.SystemRandom().randrange(2**31)
    rng = random.Random(semilla)

    mejor: tuple[list[int], Violaciones, int] | None = None
    generaciones_totales = 0
    reinicios = 0
    for intento in range(MAX_REINICIOS + 1):
        cromosoma, violaciones, generaciones = _evolucionar(problema, rng)
        generaciones_totales += generaciones
        reinicios = intento
        if mejor is None or violaciones.total < mejor[1].total:
            mejor = (cromosoma, violaciones, generaciones)
        if violaciones.total == 0:
            break

    assert mejor is not None  # el bucle se ejecuta al menos una vez
    return Resultado(mejor[0], mejor[1], generaciones_totales, reinicios, semilla)
