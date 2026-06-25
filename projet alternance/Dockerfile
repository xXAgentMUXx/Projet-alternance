FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Empêche Selenium de chercher un display X11
ENV DISPLAY=:99
# Chrome headless n'a pas besoin de sandbox dans Docker
ENV CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --headless=new --disable-gpu"

WORKDIR /app

# ── Dépendances système ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Outils de base
    gcc curl wget gnupg unzip \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    libpangocairo-1.0-0 libcairo2 libgtk-3-0 \
    libx11-6 libx11-xcb1 libxcb1 libxext6 \
    libxss1 libxtst6 fonts-liberation \
    # Nécessaire pour Chromedriver
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ───────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Playwright (pour les autres scrapers qui l'utilisent) ─────────────────────
RUN playwright install chromium --with-deps || true

# ── Code applicatif ───────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]