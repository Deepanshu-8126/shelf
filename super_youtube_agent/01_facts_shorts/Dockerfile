# FactShorts Bot container - python + ffmpeg + a display font, nothing else.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# ffmpeg (render + probe), fonts, curl for healthcheck, tini for clean shutdown
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-dejavu-core \
        espeak-ng \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# bring the bundled caption font into the system so libass can fall back to it
RUN mkdir -p /usr/share/fonts/truetype/montserrat \
    && cp -n assets/fonts/*.ttf /usr/share/fonts/truetype/montserrat/ 2>/dev/null || true \
    && fc-cache -f >/dev/null 2>&1 || true

# data (sqlite), cache, output and credentials are mounted volumes in docker-compose
RUN mkdir -p /app/data /app/cache /app/output /app/logs /app/credentials

ENTRYPOINT ["/usr/bin/tini", "--"]
# default: Telegram bot + scheduler. Override with the worker command if you prefer:
#   docker compose run --rm bot python main.py --daemon
CMD ["python", "main.py", "--bot"]
