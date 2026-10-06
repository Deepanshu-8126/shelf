FROM node:20-slim

# Install Python & FFmpeg
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir requests beautifulsoup4

# Copy code
COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python3", "-m", "vox_studio.cli"]
CMD ["trends", "--limit", "3", "--auto-produce"]
