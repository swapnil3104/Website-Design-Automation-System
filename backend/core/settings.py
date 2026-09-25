"""
Django settings for wireframe-ai project.
"""
import os
import re
from pathlib import Path

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

from core.config import config

# Base directory: d:/Downloads/wireframe-ai/backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# Frontend directory: d:/Downloads/wireframe-ai/frontend/
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

SECRET_KEY = config.secret_key
DEBUG = True

ALLOWED_HOSTS = config.allowed_hosts

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'sitemap_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [FRONTEND_DIR],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database — SQLite by default, MySQL if USE_MYSQL=1 in .env
USE_MYSQL = os.getenv('USE_MYSQL', '').lower() in ('1', 'true', 'yes')
mysql_ok = False
if USE_MYSQL:
    try:
        import MySQLdb  # type: ignore
        version = getattr(MySQLdb, '__version__', '')
        m = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        if m:
            major, minor, patch = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            mysql_ok = (major, minor, patch) >= (2, 2, 1)
    except Exception:
        mysql_ok = False

if USE_MYSQL and mysql_ok:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'sitemap_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files served from frontend/css and frontend/js
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    FRONTEND_DIR / 'css',
    FRONTEND_DIR / 'js',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django_error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

CORS_ALLOW_ALL_ORIGINS = True
