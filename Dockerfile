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

# Installer les dépendances Python (ceci compile les roues)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Final ---
# Ce stage est l'image finale, propre et sécurisée
FROM docker.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installer UNIQUEMENT les dépendances système D'EXÉCUTION
# (libpq-dev est nécessaire pour que psycopg2 s'exécute, pas seulement pour le build)
# Note: On pourrait affiner en 'libpq5' mais 'libpq-dev' est plus sûr si vous n'êtes pas sûr.
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer l'utilisateur non-privilégié
# -r = compte système, -s /bin/false = pas de shell, -g = créer un groupe
RUN groupadd -r appgroup && useradd -r -s /bin/false -g appgroup appuser

# Créer le répertoire de l'application
WORKDIR /app

# Copier les dépendances Python installées depuis le stage 'builder'
COPY --from=builder /app /app

# Copier le code source de l'application
COPY . .

# Donner la propriété du répertoire à notre nouvel utilisateur
RUN chown -R appuser:appgroup /app

# Changer d'utilisateur pour ne plus être root
USER appuser

# Exposer le port
EXPOSE 8000

# CMD : Nous gardons votre CMD pour l'instant, mais nous en avons parlé.
# Idéalement, ceci devrait être UNIQUEMENT la commande gunicorn.
CMD ["sh", "-c", "python manage.py migrate && gunicorn mysite.wsgi:application --bind 0.0.0.0:8000"]