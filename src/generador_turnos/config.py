"""Configuración del servicio, leída de variables de entorno.

El código no contiene ningún secreto: la clave de acceso llega desde el
entorno (un archivo ``.env`` en desarrollo, ``--env-file`` en Docker).
"""

import os
from dataclasses import dataclass

VARIABLE_CLAVE = "TURNOS_CLAVE_ACCESO"
LONGITUD_MINIMA_CLAVE = 8


class ConfiguracionError(RuntimeError):
    """Falta una variable de entorno obligatoria o tiene un valor inseguro."""


@dataclass(frozen=True)
class Configuracion:
    clave_acceso: str


def cargar_configuracion() -> Configuracion:
    """Lee la configuración del entorno y falla con un mensaje claro si falta.

    Se prefiere no iniciar el servicio antes que publicarlo sin protección.
    """
    clave = os.environ.get(VARIABLE_CLAVE, "").strip()
    if not clave:
        raise ConfiguracionError(
            f"Falta la variable de entorno {VARIABLE_CLAVE}. "
            "Copie .env.example como .env, defina una clave y vuelva a iniciar el servicio."
        )
    if len(clave) < LONGITUD_MINIMA_CLAVE:
        raise ConfiguracionError(
            f"{VARIABLE_CLAVE} debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres."
        )
    return Configuracion(clave_acceso=clave)
