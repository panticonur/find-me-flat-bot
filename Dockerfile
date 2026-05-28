FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    xvfb \
    libxi6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

COPY . .
RUN rm -rf data && mkdir data

VOLUME ["/app/data"]

RUN printf '#!/bin/sh\nexec Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && exec python bot.py\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
