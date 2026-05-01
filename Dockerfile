ARG BASE_TAG=3.11-sdk0.5.0
FROM ghcr.io/narisun/ai-python-base:${BASE_TAG}

WORKDIR /app
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY src/ /app/src/

USER appuser
EXPOSE 8090
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8090"]
