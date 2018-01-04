# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

import celery
import django
import quade


DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "dddddddddddddddddddddddddddddddddddddddddddddddddd"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': ['templates', ],
        'APP_DIRS': True,
        'OPTIONS': {
            'app_dirname': 'jinja2',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

ROOT_URLCONF = "tests.urls"
STATIC_URL = "/static/"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.sessions",
    "quade.apps.QuadeConfig",
]

SITE_ID = 1

middlewares = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

if django.VERSION >= (1, 10):
    MIDDLEWARE = middlewares
else:
    MIDDLEWARE_CLASSES = middlewares

QUADE = quade.Settings(allowed_envs=quade.AllEnvs)

celery.current_app.conf.CELERY_ALWAYS_EAGER = True
celery.current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
