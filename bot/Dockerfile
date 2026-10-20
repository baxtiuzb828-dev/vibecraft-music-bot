FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 bot \
    && mkdir -p /app/data/inbox \
    && chown -R bot:bot /app

USER bot

CMD ["python", "-m", "music_bot"]