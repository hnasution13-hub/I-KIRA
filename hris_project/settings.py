"""
HRIS SmartDesk — Django Settings
Production-ready: Render + Neon PostgreSQL + Cloudinary

Environment variables wajib di production (set di Render Dashboard):
  SECRET_KEY, DATABASE_URL,
  CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
  ALLOWED_HOSTS, SITE_URL, CORS_ALLOWED_ORIGINS

Optional (ada default-nya):
  DEBUG (default False), EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
  DEFAULT_FROM_EMAIL, HR_EMAIL_LIST, SALES_WA, SALES_EMAIL
"""

from pathlib import Path
from datetime import timedelta
import os

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY tidak ditemukan di environment! Pakai fallback — JANGAN di production.",
        stacklevel=1,
    )
    SECRET_KEY = 'django-insecure-local-dev-only-change-in-production-abc123xyz'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_allowed = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

# Percayai header dari Render reverse proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Security Headers (aktif di production / HTTPS) ───────────────────────────

if not DEBUG:
    SECURE_SSL_REDIRECT               = True
    SECURE_HSTS_SECONDS               = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS    = True
    SECURE_HSTS_PRELOAD               = True
    SECURE_CONTENT_TYPE_NOSNIFF       = True
    SECURE_BROWSER_XSS_FILTER         = True
    X_FRAME_OPTIONS                   = 'DENY'
    SESSION_COOKIE_SECURE             = True
    SESSION_COOKIE_HTTPONLY           = True
    SESSION_COOKIE_SAMESITE           = 'Lax'
    CSRF_COOKIE_SECURE                = True
    CSRF_COOKIE_HTTPONLY              = True

# ── CSRF Trusted Origins ──────────────────────────────────────────────────────

_site_url = os.environ.get('SITE_URL', 'http://localhost:8000')
CSRF_TRUSTED_ORIGINS = [_site_url]
_cors_raw = os.environ.get('CORS_ALLOWED_ORIGINS', '')
for _origin in [o.strip() for o in _cors_raw.split(',') if o.strip()]:
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

# ── Installed Apps ────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # Cloudinary HARUS sebelum django.contrib.staticfiles
    'cloudinary_storage',
    'cloudinary',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'apps.core',
    'apps.employees',
    'apps.attendance',
    'apps.contracts',
    'apps.payroll',
    'apps.industrial',
    'apps.recruitment',
    'apps.psychotest',
    'apps.reports',
    'apps.advanced_psychotest',
    'apps.assets',
    'apps.locations',
    'apps.vendors',
    'apps.movements',
    'apps.maintenance',
    'apps.audit',
    'apps.asset_reports',
    'apps.custom_categories',
    'apps.api',
    'apps.wilayah',
    'apps.portal',
    'apps.shifts',
    'apps.od',
    'apps.performance',
    'apps.registration',
    'apps.investor',
]

# ── Middleware ────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.CompanyMiddleware',
    'apps.core.middleware.PlanCheckMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.signals.RequestUserMiddleware',
]

ROOT_URLCONF = 'hris_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'core' / 'templates',
            BASE_DIR / 'attendance' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'hris_project.wsgi.application'

# ── Database: Neon PostgreSQL ─────────────────────────────────────────────────

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'core.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'id-id'
TIME_ZONE     = 'Asia/Jakarta'
USE_I18N      = True
USE_TZ        = True

# ── Static Files (Whitenoise) ─────────────────────────────────────────────────
# CompressedStaticFilesStorage — compress & cache tapi tidak strict-manifest
# Menghindari MissingFileError dari .map file milik DRF / third-party

STATIC_URL       = '/static/'
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ── Media Files (Cloudinary) ──────────────────────────────────────────────────

CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY    = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    import cloudinary
    cloudinary.config(
        cloud_name = CLOUDINARY_CLOUD_NAME,
        api_key    = CLOUDINARY_API_KEY,
        api_secret = CLOUDINARY_API_SECRET,
        secure     = True,
    )
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f'https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/'
else:
    MEDIA_URL  = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# ── Email ─────────────────────────────────────────────────────────────────────

_email_user = os.environ.get('EMAIL_HOST_USER', '')
if _email_user:
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS       = True
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL  = os.environ.get(
        'DEFAULT_FROM_EMAIL',
        f'HRIS SmartDesk <{_email_user}>'
    )
else:
    EMAIL_BACKEND      = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@hris-smartdesk.com'

HR_EMAIL_LIST = [
    e.strip()
    for e in os.environ.get('HR_EMAIL_LIST', '').split(',')
    if e.strip()
]

# ── CORS ──────────────────────────────────────────────────────────────────────

_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if _cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

CORS_ALLOW_CREDENTIALS = True

# ── REST Framework ────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '1000/hour',
    },
}

# ── JWT ───────────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': False,
}

# ── OpenAPI / Swagger Docs ────────────────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    'TITLE':       'HRIS SmartDesk API',
    'DESCRIPTION': (
        'REST API untuk HRIS SmartDesk. '
        'Autentikasi menggunakan JWT Bearer token. '
        'Dapatkan token via POST /api/token/ dengan username & password.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# ── Session ───────────────────────────────────────────────────────────────────

SESSION_ENGINE                  = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE              = 28800   # 8 jam, sinkron dengan JWT access token
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST      = False

# ── Cache ─────────────────────────────────────────────────────────────────────
# LocMemCache cukup untuk single-instance Render free/starter tier.
# Upgrade ke Redis kalau sudah multi-instance atau butuh shared cache.

CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ikira-hris-cache',
    }
}

# ── App Config ────────────────────────────────────────────────────────────────

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

APP_NAME     = 'HRIS-SmartDesk'
APP_VERSION  = '1.0.0'
COMPANY_NAME = 'SmartDesk Technology'
BRAND_COLOR  = '#c40000'

TRIAL_DAYS        = 30
TRIAL_DURASI_HARI = 30

CONTRACT_EXPIRY_WARNING_DAYS = 30
PROBATION_END_WARNING_DAYS   = 14

SITE_URL    = os.environ.get('SITE_URL',    'http://localhost:8000')
SALES_WA    = os.environ.get('SALES_WA',    '6281234567890')
SALES_EMAIL = os.environ.get('SALES_EMAIL', 'sales@hris-smartdesk.com')

# ── Logging ───────────────────────────────────────────────────────────────────
# Semua output ke console — Render tangkap otomatis ke log dashboard.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'WARNING',
    },
    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['console'],
            'level':     'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers':  ['console'],
            'level':     'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}
