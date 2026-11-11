# Generador de turnos

Servicio web que genera un **horario semanal de turnos** para un equipo pequeño.
El usuario indica quiénes conforman el equipo y las reglas, y un algoritmo genético
busca un horario en el que:

1. cada turno tenga el número pedido de **personas distintas**;
2. nadie supere su **máximo de turnos** en la semana;
3. (opcional) nadie trabaje **dos turnos seguidos**.

**¿Quién lo usaría?** La persona que coordina un equipo que cubre turnos (un punto
de atención, un laboratorio, un grupo de monitores) y hoy arma el horario a mano.

Proyecto de la Actividad 4 de *Técnicas Avanzadas de IA* (Maestría en Ciencia de
Datos, UPB). Lleva a un servicio publicable el algoritmo genético de la Unidad 2.

## Cómo se usa

| Ruta | Qué hace | ¿Requiere clave? |
|---|---|---|
| `GET /` | Página web con el formulario | No |
| `GET /health` | Confirma que el servicio está listo | No |
| `POST /horarios` | Genera un horario (JSON) | Sí: encabezado `X-Clave-Acceso` |
| `GET /docs` | Documentación interactiva de la API | No |

No necesita datos, modelos entrenados ni servicios externos: solo Python y las
dependencias declaradas en `pyproject.toml`.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala por sí mismo la versión de Python indicada en `.python-version`)
- Git
- Docker Desktop (solo para ejecutar el contenedor)

## Instalación

```bash
git clone https://github.com/santiago-montano/generador-turnos.git
cd generador-turnos
uv sync
```

`uv sync` reconstruye el entorno exacto descrito en `uv.lock`.

## Configuración de secretos

El servicio se protege con una **clave de acceso** que no está en el código ni en el
repositorio: se lee de la variable de entorno `TURNOS_CLAVE_ACCESO`.

1. Copie la plantilla:

   ```bash
   cp .env.example .env          # Linux / macOS
   Copy-Item .env.example .env   # Windows (PowerShell)
   ```

2. Abra `.env` y reemplace el valor por una clave propia (mínimo 8 caracteres;
   solo letras, números y guiones).

El archivo `.env` está excluido en `.gitignore` y en `.dockerignore`: nunca se sube
al repositorio ni se copia dentro de la imagen. Si la variable falta, el servicio
**no arranca** y explica cómo configurarla.

## Ejecución local

```bash
uv run --env-file .env uvicorn generador_turnos.api:app --reload
```

Abra <http://localhost:8000>, escriba la clave definida en `.env` y genere un horario.

Ejemplo con la API (reemplace `SU-CLAVE`):

```bash
curl -X POST http://localhost:8000/horarios \
  -H "Content-Type: application/json" \
  -H "X-Clave-Acceso: SU-CLAVE" \
  -d '{"personas": ["Ana", "Luis", "Marta", "Pedro", "Sofia"], "dias": 5, "turnos_por_dia": 2, "personas_por_turno": 2, "max_turnos_por_persona": 4}'
```

Si el problema no tiene solución posible (por ejemplo, el equipo no alcanza a cubrir
todos los cupos), el servicio responde `422` y explica el motivo.

## Verificación

```bash
uv run pytest -v             # pruebas automatizadas
uv run ruff check .          # linting
uv run ruff format --check . # formato
uv run mypy                  # tipos
```

Las pruebas cubren las reglas del problema (`tests/test_horario.py`), el algoritmo
(`tests/test_genetico.py`), la lectura del secreto (`tests/test_config.py`) y el
servicio (`tests/test_api.py`). Para ejecutarlas antes de cada commit:
`uv run pre-commit install`.

## Contenedor

```bash
docker build -t generador-turnos .
docker run --rm -p 8000:8000 --env-file .env generador-turnos
```

La imagen instala solo las dependencias del servicio (`uv sync --no-default-groups`)
y copia solo `src/`. No incluye pruebas, herramientas de desarrollo, el archivo
`.env` ni el historial de Git. La clave entra al contenedor al ejecutarlo
(`--env-file`), no al construir la imagen.

## Publicación temporal

Con el contenedor en ejecución, en otra terminal:

```bash
cloudflared tunnel --url http://localhost:8000
```

Entre los mensajes aparece una dirección `https://….trycloudflare.com`, accesible
desde cualquier dispositivo mientras el comando siga en ejecución.

## Estructura

```
├── pyproject.toml        dependencias y configuración de Ruff, mypy y pytest
├── uv.lock               versiones exactas de todas las dependencias
├── .python-version       versión de Python del proyecto
├── .env.example          plantilla de configuración (sin secretos)
├── Dockerfile            receta de la imagen del servicio
├── src/generador_turnos/
│   ├── horario.py        reglas del problema y conteo de violaciones
│   ├── genetico.py       algoritmo genético
│   ├── config.py         lectura de la configuración desde el entorno
│   ├── api.py            servicio FastAPI
│   └── static/index.html página web
├── tests/                pruebas con pytest
└── .github/workflows/    integración continua (Ruff, mypy, pytest y Docker)
```
