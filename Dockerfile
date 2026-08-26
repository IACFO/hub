FROM python:3.12-slim-bookworm

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY agents ./agents

ENV PYTHONPATH=/app/src
ENV PORT=8080

EXPOSE 8080
CMD ["sh", "-c", "uvicorn hub.server:app --host 0.0.0.0 --port ${PORT}"]
