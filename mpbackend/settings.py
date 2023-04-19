import os
from pathlib import Path

import environ
from django.conf.global_settings import LANGUAGES as GLOBAL_LANGUAGES
from django.core.exceptions import ImproperlyConfigured

CONFIG_FILE_NAME = "config_dev.env"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
root = environ.Path(__file__) - 2  # two levels back in hierarchy

env = environ.Env(
    DEBUG=(bool, False),
    LANGUAGES=(list, ["fi", "sv", "en"]),
    DATABASE_URL=(str, "postgis:///servicemap"),
    ALLOWED_HOSTS=(list, []),
)
# WARN about env file not being preset. Here we pre-empt it.
env_file_path = os.path.join(BASE_DIR, CONFIG_FILE_NAME)
if os.path.exists(env_file_path):
    # Logging configuration is not available at this point
    print(f"Reading config from {env_file_path}")
    environ.Env.read_env(env_file_path)

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
    "modeltranslation",
    "profiles.apps.ProfilesConfig",
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

ROOT_URLCONF = "mpbackend.urls"

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

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

WSGI_APPLICATION = "mpbackend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {"default": env.db()}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

# Map language codes to the (code, name) tuples used by Django
# We want to keep the ordering in LANGUAGES configuration variable,
# thus some gyrations
language_map = {x: y for x, y in GLOBAL_LANGUAGES}
try:
    LANGUAGES = tuple((lang, language_map[lang]) for lang in env("LANGUAGES"))
except KeyError as e:
    raise ImproperlyConfigured(f'unknown language code "{e.args[0]}"')

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = env("LANGUAGES")[0]
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE

TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
if "SECRET_KEY" not in locals():
    secret_file = os.path.join(BASE_DIR, ".django_secret")
    try:
        SECRET_KEY = open(secret_file).read().strip()
    except IOError:
        import random

        system_random = random.SystemRandom()
        try:
            SECRET_KEY = "".join(
                [
                    system_random.choice(
                        "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
                    )
                    for i in range(64)
                ]
            )
            secret = open(secret_file, "w")
            import os

            os.chmod(secret_file, 0o0600)
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception(
                "Please create a %s file with random characters to generate your secret key!"
                % secret_file
            )
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped_named": {
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamped_named",
        },
        # Just for reference, not used
        "blackhole": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "profiles": {"handlers": ["console"], "level": "DEBUG"},
    },
}
