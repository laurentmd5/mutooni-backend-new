# --- STAGE 1: Builder ---
# Ce stage installe les outils de build et compile les dépendances
FROM docker.io/library/python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer les dépendances système NÉCESSAIRES AU BUILD
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
# Ceci installe les paquets dans /usr/local/lib/python3.11/site-packages
# et les exécutables (comme gunicorn) dans /usr/local/bin
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Final ---
# Ce stage est l'image finale, propre et sécurisée
FROM docker.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer UNIQUEMENT les dépendances système D'EXÉTION
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
# Note: Remplacé libpq-dev par libpq5 (plus léger, juste le client runtime)

# Créer l'utilisateur non-privilégié
RUN groupadd -r appgroup && useradd -r -s /bin/false -g appgroup appuser

WORKDIR /app

# --- LA CORRECTION EST ICI ---
# Copier les paquets Python installés depuis le builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copier les exécutables (comme gunicorn) depuis le builder
COPY --from=builder /usr/local/bin /usr/local/bin
# --- FIN DE LA CORRECTION ---

# Copier le code source de l'application
# Le .dockerignore empêchera serviceAccountKey.json d'être copié ici
COPY . .

# Donner la propriété du répertoire à notre nouvel utilisateur
RUN chown -R appuser:appgroup /app

# Changer d'utilisateur pour ne plus être root
USER appuser

EXPOSE 8000

# CMD :
CMD ["sh", "-c", "python manage.py migrate && gunicorn mysite.wsgi:application --bind 0.0.0.0:8000"]