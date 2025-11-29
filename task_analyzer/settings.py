
"""
Minimal Django settings for the task-analyzer assignment.
Keep secrets and environment-specific settings out of repo in real projects.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-for-assignment")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") != "0"

ALLOWED_HOSTS = ["*"]  # safe for local dev; lock down in production

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "task_analyzer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",      # <-- required for admin
                "django.contrib.messages.context_processors.messages",  # <-- required for admin
            ],
        },
    }
]


WSGI_APPLICATION = "task_analyzer.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Use sqlite for assignment simplicity
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (if you serve frontend via Django)
STATIC_URL = "/static/"

# Scoring config path (optional) - put a path to JSON to override weights
SCORING_CONFIG_PATH = os.environ.get("SCORING_CONFIG_PATH", "")

# DRF defaults (kept minimal)
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
    ),
}
