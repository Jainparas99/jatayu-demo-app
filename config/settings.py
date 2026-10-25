"""Local-only demo settings with deliberately retained Django 4.2 conventions."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# An obvious disposable development value, never a production credential.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "queuedesk-local-demo-not-a-production-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "workboard.apps.WorkboardConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ]
        },
    }
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
USE_I18N = True
# Billing values must remain machine-readable even for a translated interface.
USE_L10N = False
STATIC_URL = "/static/"
MEDIA_ROOT = BASE_DIR / "var" / "uploads"
MEDIA_URL = "/uploads/"
EXPORT_ROOT = BASE_DIR / "var" / "exports"
# Export files go through a separate backend rather than the general uploads directory.
DEFAULT_FILE_STORAGE = "workboard.storage.ExportStorage"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
