# --- STAGE 1: Builder ---
# Ce stage installe les outils de build et compile les dépendances dans un venv
FROM docker.io/library/python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer les dépendances système NÉCESSAIRES AU BUILD
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer un environnement virtuel
RUN python3 -m venv /opt/venv

# Activer le venv pour les commandes suivantes n'est pas nécessaire
# si nous appelons les exécutables directement.

WORKDIR /app
COPY requirements.txt .

# Installer les dépendances DANS le venv
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Final ---
# Ce stage est l'image finale, propre et sécurisée
FROM docker.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer UNIQUEMENT les dépendances système D'EXÉCUTION
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
# Note: Remplacé libpq-dev par libpq5 (plus léger, juste le client runtime)

# Créer l'utilisateur non-privilégié
RUN groupadd -r appgroup && useradd -r -s /bin/false -g appgroup appuser

WORKDIR /app

# Copier l'environnement virtuel complet depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Copier le code source de l'application
# Le .dockerignore empêchera serviceAccountKey.json d'être copié ici
COPY . .

# Donner la propriété du répertoire à notre nouvel utilisateur
RUN chown -R appuser:appgroup /app

# Changer d'utilisateur pour ne plus être root
USER appuser

# --- CORRECTION FINALE ---
# Ajouter le venv au PATH pour que 'python' et 'gunicorn' soient trouvés
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

# CMD :
# 'python' et 'gunicorn' viendront maintenant du /opt/venv/bin
CMD ["sh", "-c", "python manage.py migrate && gunicorn mysite.wsgi:application --bind 0.0.0.0:8000"]