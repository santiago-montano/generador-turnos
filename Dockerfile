# Imagen del servicio: solo lo necesario para ejecutarlo.
FROM python:3.12-slim

# uv se copia desde su imagen oficial, con la versión fijada
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Dependencias: se instalan exactamente las versiones de uv.lock, sin el
#    grupo de desarrollo (pytest, Ruff, mypy y pre-commit no entran a la imagen).
#    Esta capa solo se reconstruye cuando cambian las dependencias.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-default-groups --no-install-project

# 2) Código de la aplicación (las pruebas no se copian)
COPY src ./src
RUN uv sync --locked --no-default-groups

# El servicio no se ejecuta como administrador
RUN useradd --system --no-create-home servicio
USER servicio

EXPOSE 8000

# Docker consulta /health para saber si el servicio está sano
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"]

CMD ["/app/.venv/bin/uvicorn", "generador_turnos.api:app", "--host", "0.0.0.0", "--port", "8000"]
