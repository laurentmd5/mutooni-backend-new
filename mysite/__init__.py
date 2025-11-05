"""
Initialisation du projet Django « mysite ».

– Charge automatiquement les variables d’environnement définies dans un
  fichier `.env` à la racine du projet.
– Place un indicateur de VERSION (facultatif) accessible via `django.conf`.
"""

import os
from pathlib import Path

# Chargement .env (via python‑dotenv) ― utile à la fois en local & prod
try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv non installé
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

# Option : expose une version (issue git, etc.)
__version__ = os.getenv("MYSITE_VERSION", "0.1.0")
