import os
from pathlib import Path
from datetime import timedelta
from django.core.management.utils import get_random_secret_key
from corsheaders.defaults import default_headers

# ─────────────────────────────────────────────
# 1. Chemins & Environnement
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ENV = os.getenv("DJANGO_ENV", "dev")  # dev | prod
DEBUG = os.getenv("DEBUG", "True") == "True"

# ─────────────────────────────────────────────
# 2. Logging
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'django.security': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'rest_framework': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
    },
}

# ─────────────────────────────────────────────
# 3. Templates
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ─────────────────────────────────────────────
# 4. Sécurité
# ─────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY") or get_random_secret_key()
ALLOWED_HOSTS = ["*", "192.168.61.131"]

# ─────────────────────────────────────────────
# 5. Applications (MODIFICATIONS ICI)
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    # Apps Django par défaut
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps tiers EXISTANTES
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_spectacular",

    # NOUVELLES extensions admin (doivent venir AVANT django.contrib.admin)
    "admin_interface",
    "colorfield",
    "import_export",
    "rangefilter",
    "django_admin_listfilter_dropdown",

    # Admin Django (doit être APRÈS les extensions)
    "django.contrib.admin",

    # Apps projet
    "core",
    "users",
]


# ─────────────────────────────────────────────
# 6. Middleware (inchangé)
# ─────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"
WSGI_APPLICATION = "mysite.wsgi.application"
ASGI_APPLICATION = "mysite.asgi.application"

# ─────────────────────────────────────────────
# 7. Base de données (inchangé)
# ─────────────────────────────────────────────
if ENV == "prod":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "mysite"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ─────────────────────────────────────────────
# 8. Authentification & API REST (inchangé)
# ─────────────────────────────────────────────
AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "core.authentication.FirebaseAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_MINUTES", 30))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_DAYS", 7))),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─────────────────────────────────────────────
# 9. drf-spectacular (inchangé)
# ─────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Mutooni API",
    "DESCRIPTION": "Documentation de l'API Mutooni avec Swagger et ReDoc",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
    },
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",
}

# ─────────────────────────────────────────────
# 10. Internationalisation (inchangé)
# ─────────────────────────────────────────────
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = os.getenv("TZ", "Africa/Dakar")
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────
# 11. Statics & Médias (inchangé)
# ─────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─────────────────────────────────────────────
# 12. CORS (inchangé)
# ─────────────────────────────────────────────
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "https://9002-firebase-mutooni-front-1751399486531.cluster-l6vkdperq5ebaqo3qy4ksvoqom.cloudworkstations.dev",
    "https://9000-firebase-mutooni-front-1751399486531.cluster-l6vkdperq5ebaqo3qy4ksvoqom.cloudworkstations.dev",
    "http://localhost:8000",
    "http://10.88.0.3:9000",
    "http://10.88.0.3:9002",
    "http://localhost:5271",
    "https://8000-firebase-mutooni-back-1751236955562.cluster-l6vkdperq5ebaqo3qy4ksvoqom.cloudworkstations.dev",
    "http://192.168.61.131:8000",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/(\d+)-firebase-mutooni-(front|back)-.+\.cloudworkstations\.dev$"
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
    "x-requested-with",
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS"
]
CSRF_TRUSTED_ORIGINS = [
    'https://9800-firebase-mutconi-back-1751236955562.cluster-16.widperq5ebaqo3gy4ksvoqom.cloudworkstations.dev',
    'https://*.cloudworkstations.dev'
]

# ─────────────────────────────────────────────
# 13. Firebase (inchangé)
# ─────────────────────────────────────────────
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
if FIREBASE_CREDENTIALS:
    try:
        import json
        FIREBASE_CONFIG = json.loads(FIREBASE_CREDENTIALS)
    except json.JSONDecodeError:
        FIREBASE_CONFIG = None
else:
    FIREBASE_CONFIG = None

# ─────────────────────────────────────────────
# 14. Nouvelle section : Configuration Admin
# ─────────────────────────────────────────────
X_FRAME_OPTIONS = "SAMEORIGIN"  # Nécessaire pour admin_interface
SILENCED_SYSTEM_CHECKS = ["security.W019"]  # Pour admin_interface

IMPORT_EXPORT_USE_TRANSACTIONS = True  # Pour l'intégrité des données lors des imports

# Configuration du thème admin
ADMIN_SITE_HEADER = "Administration Mutooni"
ADMIN_SITE_TITLE = "Portail d'administration"
ADMIN_INDEX_TITLE = "Gestion du backoffice"
ADMIN_INTERFACE_CONFIG = {
    'THEME': 'Mutooni',
    'DARK_MODE': True,  # Activer le mode sombre
    'COLOR_SCHEME': 'auto',  # auto | light | dark
    'DEFAULT_COLOR_SCHEME': 'dark',  # Préférer le mode sombre
}