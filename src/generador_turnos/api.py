"""Servicio web: recibe un problema de turnos y devuelve un horario."""

import secrets
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from generador_turnos import __version__
from generador_turnos.config import Configuracion, cargar_configuracion
from generador_turnos.genetico import generar_horario
from generador_turnos.horario import Problema, ProblemaInvalidoError, separar_turnos


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
    """Carga la configuración al iniciar: sin clave de acceso el servicio no arranca."""
    app.state.configuracion = cargar_configuracion()
    yield


app = FastAPI(
    title="Generador de turnos",
    description="Genera un horario semanal de turnos con un algoritmo genético.",
    version=__version__,
    lifespan=ciclo_de_vida,
)


class SolicitudHorario(BaseModel):
    """Datos que envía el usuario. Los límites protegen al servicio de cargas excesivas."""

    personas: list[Annotated[str, Field(min_length=1, max_length=40)]] = Field(
        min_length=1, max_length=30, examples=[["Ana", "Luis", "Marta", "Pedro", "Sofía"]]
    )
    dias: int = Field(default=7, ge=1, le=7)
    turnos_por_dia: int = Field(default=2, ge=1, le=3)
    personas_por_turno: int = Field(default=2, ge=1, le=10)
    max_turnos_por_persona: int = Field(default=6, ge=1, le=21)
    evitar_turnos_consecutivos: bool = False
    semilla: int | None = Field(default=None, ge=0, description="Fija el resultado si se indica.")


class Turno(BaseModel):
    nombre: str
    personas: list[str]


class DetalleViolaciones(BaseModel):
    repeticiones: int
    excesos: int
    consecutivos: int


class RespuestaHorario(BaseModel):
    valido: bool
    violaciones: DetalleViolaciones
    turnos: list[Turno]
    turnos_por_persona: dict[str, int]
    generaciones: int
    reinicios: int
    semilla: int


def verificar_clave(
    request: Request, x_clave_acceso: Annotated[str | None, Header()] = None
) -> None:
    """Rechaza la solicitud si no trae la clave de acceso correcta."""
    configuracion: Configuracion = request.app.state.configuracion
    recibida = x_clave_acceso or ""
    # compare_digest evita filtrar información por el tiempo de comparación
    if not secrets.compare_digest(recibida.encode(), configuracion.clave_acceso.encode()):
        raise HTTPException(status_code=401, detail="Clave de acceso ausente o incorrecta.")


@app.get("/health")
def health() -> dict[str, str]:
    """Confirma que el servicio está listo. No requiere clave."""
    return {"estado": "ok", "version": __version__}


@app.post("/horarios", dependencies=[Depends(verificar_clave)])
def crear_horario(solicitud: SolicitudHorario) -> RespuestaHorario:
    """Genera un horario. Requiere el encabezado ``X-Clave-Acceso``."""
    problema = Problema(
        personas=tuple(nombre.strip() for nombre in solicitud.personas),
        dias=solicitud.dias,
        turnos_por_dia=solicitud.turnos_por_dia,
        personas_por_turno=solicitud.personas_por_turno,
        max_turnos_por_persona=solicitud.max_turnos_por_persona,
        evitar_turnos_consecutivos=solicitud.evitar_turnos_consecutivos,
    )
    try:
        resultado = generar_horario(problema, solicitud.semilla)
    except ProblemaInvalidoError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    turnos = separar_turnos(problema, resultado.cromosoma)
    conteo = Counter(resultado.cromosoma)
    return RespuestaHorario(
        valido=resultado.valido,
        violaciones=DetalleViolaciones(
            repeticiones=resultado.violaciones.repeticiones,
            excesos=resultado.violaciones.excesos,
            consecutivos=resultado.violaciones.consecutivos,
        ),
        turnos=[
            Turno(nombre=nombre, personas=sorted(problema.personas[i] for i in turno))
            for nombre, turno in zip(problema.nombres_turnos(), turnos, strict=True)
        ],
        turnos_por_persona={nombre: conteo.get(i, 0) for i, nombre in enumerate(problema.personas)},
        generaciones=resultado.generaciones,
        reinicios=resultado.reinicios,
        semilla=resultado.semilla,
    )
