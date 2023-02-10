"""
Django settings for optiserver project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from datetime import timedelta
import environ

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(
        str,
        "django-insecure-2kp2o(f+5*c-zuh744sd(ag3q#*)zc(edpyjzorf+3q!hz8-%r",
    ),
    ALLOWED_HOSTS=(list, []),
    OSRM_BASE_URL=(str, "http://router.project-osrm.org"),
    ROOT_LOG_LEVEL=(str, "WARNING"),
    DJANGO_LOG_LEVEL=(str, "INFO"),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(BASE_DIR / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "solver",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "optiserver.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "optiserver.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": env.db(default="sqlite:////tmp/optiserver-db.sqlite3"),
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django logging
# https://docs.djangoproject.com/en/4.1/topics/logging/#logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {module} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("ROOT_LOG_LEVEL"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
            "propagate": False,
        },
    },
}

# Django REST Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# drf-spectacular
# https://github.com/tfranzel/drf-spectacular/

SPECTACULAR_SETTINGS = {
    "TITLE": "OptiServer",
    "DESCRIPTION": "Last-mile warehouse routing microservice",
    "VERSION": "0.2.0",
}

# OptiRider

OPTIRIDER_SETTINGS = {
    "CONSTANTS": {
        "MISS_PENALTY": 2000000,
        "MISS_PENALTY_REDUCER": 20,
        "WAIT_TIME_AT_WAREHOUSE": timedelta(seconds=0),
        "LATE_DELIVERY_PENALTY_PER_SEC": 10,
        "GLOBAL_START_TIME": timedelta(hours=9),  # '9 a.m.'
        "GLOBAL_END_TIME": timedelta(hours=21),  # '9 p.m.'
        # Handle that a trip time cannot exceed 5:30 hrs (19800s)
        "MAX_TRIP_TIME": timedelta(hours=5, minutes=30),
        "DEFAULT_TIME_LIMIT": timedelta(minutes=5),
    },
    # OSRM
    "OSRM": {
        "BASE_URL": env("OSRM_BASE_URL"),
    },
}
