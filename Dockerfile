ARG BASE_TAG=3.11-sdk0.6.0
FROM ghcr.io/narisun/ai-python-base:${BASE_TAG}

WORKDIR /app
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY src/ /app/src/
COPY config/ /app/config/

# Pre-create the SQLite-backing directory with appuser ownership so volume mounts
# don't end up root-owned and unwritable by the runtime user.
RUN mkdir -p /var/lib/registry && chown appuser:appuser /var/lib/registry

USER appuser
EXPOSE 8090
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8090"]
