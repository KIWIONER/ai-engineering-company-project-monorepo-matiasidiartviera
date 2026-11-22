FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Crear usuario y grupo dedicado no-root para ejecutar la API y workers
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY --chown=appuser:appgroup . ./services

# Cambiar a usuario no-root antes de exponer y arrancar el servicio
USER appuser

EXPOSE 8000
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]