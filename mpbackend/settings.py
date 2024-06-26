import os
import sys
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
    DATABASE_URL=(str, "postgres://mobilityprofile:mobilityprofile"),
    ALLOWED_HOSTS=(list, []),
    MEDIA_ROOT=(environ.Path(), root("media")),
    STATIC_ROOT=(environ.Path(), root("static")),
    MEDIA_URL=(str, "/media/"),
    STATIC_URL=(str, "/static/"),
    CORS_ORIGIN_WHITELIST=(list, []),
    CACHE_LOCATION=(str, "127.0.0.1:11211"),
    TOKEN_SECRET=(str, None),
)
# WARN about env file not being preset. Here we pre-empt it.
env_file_path = os.path.join(BASE_DIR, CONFIG_FILE_NAME)
if os.path.exists(env_file_path):
    # Logging configuration is not available at this point
    print(f"Reading config from {env_file_path}")
    environ.Env.read_env(env_file_path)

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Custom user model
AUTH_USER_MODEL = "account.User"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_extensions",
    "modeltranslation",
    "profiles.apps.ProfilesConfig",
    "account.apps.AccountConfig",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
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

CORS_ALLOW_HEADERS = [
    "X-CSRFTOKEN",
    "csrftoken",
    "Content-Type",
    "Cookie",
    "Authorization",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = env("CORS_ORIGIN_WHITELIST")

CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

SECURE_CROSS_ORIGIN_OPENER_POLICY = None
TOKEN_SECRET = env("TOKEN_SECRET")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly"
    ],
    "DEFAULT_PAGINATION_CLASS": "profiles.api_pagination.Pagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "profiles.api.renderers.CustomBrowsableAPIRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "mpbackend.authentication.ExpiringTokenAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/day", "user": "1000/day"},
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
# Static & Media files
STATIC_ROOT = env("STATIC_ROOT")
STATIC_URL = env("STATIC_URL")
MEDIA_ROOT = env("MEDIA_ROOT")
MEDIA_URL = env("MEDIA_URL")

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
        "normal": {
            "format": "%(asctime)s %(levelname)s %(name)s %(thread)d %(lineno)s %(message)s"
        },
    },
    "handlers": {
        "file_logger": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "django_debug.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 10,
            "formatter": "normal",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamped_named",
        },
        # Just for reference, not used
        "blackhole": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "django": {"handlers": ["console", "file_logger"], "level": "WARNING"},
        "profiles": {"handlers": ["console", "file_logger"], "level": "WARNING"},
        "django.security.DisallowedHost": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mobility Profile API",
    "DESCRIPTION": "Your project description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
    "PREPROCESSING_HOOKS": ["mpbackend.excluded_path.preprocessing_filter_spec"],
}
# After how many hours users authentication token is expired and deleted
TOKEN_EXPIRED_AFTER_HOURS = 24

if "pytest" not in sys.modules:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
            "LOCATION": env("CACHE_LOCATION"),  # Address of the Memcached server
        }
    }
