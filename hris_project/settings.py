from pathlib import Path
from datetime import timedelta
import os  # FIX BUG-002: gunakan environment variable

BASE_DIR = Path(__file__).resolve().parent.parent

# FIX BUG-002: SECRET_KEY dari environment variable, bukan hardcoded
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-smartdesk-hris-change-in-production-2024-abc123xyz'
)

# FIX BUG-002: DEBUG dari environment variable, default False di production
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# FIX BUG-002: ALLOWED_HOSTS dari environment variable
_allowed = os.environ.get('ALLOWED_HOSTS', '*')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',')]

INSTALLED_APPS = [
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
    'drf_spectacular',  # API docs / OpenAPI
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
    # ── Add-On: Advanced Psychometric Test ───────────────
    'apps.advanced_psychotest',
    # ── Add-On: Asset Management ─────────────────────────
    'apps.assets',
    'apps.locations',
    'apps.vendors',
    'apps.movements',
    'apps.maintenance',
    'apps.audit',
    'apps.asset_reports',
    'apps.custom_categories',
    'apps.api',
    'apps.wilayah',  # Data wilayah Indonesia
    'apps.portal',   # Portal self-service karyawan
    'apps.shifts',   # Manajemen Shift & Roster
    # ── Add-On: Organisation Development ─────────────────
    'apps.od',
    'apps.performance',
    # ── Registrasi Demo & Trial ───────────────────────────
    'apps.registration',
    # ── Investor Dashboard ────────────────────────────────
    'apps.investor',
]

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
    # FIX: Ganti AuditMiddleware berbasis path-guessing dengan RequestUserMiddleware
    # yang bekerja bersama Django signals untuk audit log yang akurat.
    'apps.core.signals.RequestUserMiddleware',
]

ROOT_URLCONF = 'hris_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'core' / 'templates', BASE_DIR / 'attendance' / 'templates'],
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

# Database — otomatis pakai PostgreSQL kalau ada DATABASE_URL (Railway/production)
# kalau tidak ada, fallback ke SQLite (local development)
import dj_database_url
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'core.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Cloudinary Storage — untuk file media permanen (CV, foto, dll) ───────────
CLOUDINARY_CLOUD_NAME  = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY     = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET  = os.environ.get('CLOUDINARY_API_SECRET', '')

# Pakai Cloudinary jika credentials tersedia (production)
# Fallback ke local storage jika tidak ada (development)
if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    import cloudinary
    cloudinary.config(
        cloud_name = CLOUDINARY_CLOUD_NAME,
        api_key    = CLOUDINARY_API_KEY,
        api_secret = CLOUDINARY_API_SECRET,
        secure     = True,
    )
    DEFAULT_FILE_STORAGE  = 'cloudinary_storage.storage.MediaCloudinaryStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
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
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # untuk API docs
}

# OpenAPI / Swagger docs (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'HRIS SmartDesk API',
    'DESCRIPTION': (
        'REST API untuk HRIS SmartDesk. '
        'Autentikasi menggunakan JWT Bearer token. '
        'Dapatkan token via POST /api/token/ dengan username & password.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# FIX BUG-018: Jangan izinkan semua origin — batasi ke domain yang diizinkan
# Isi CORS_ALLOWED_ORIGINS di environment variable atau di sini secara eksplisit
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if _cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]
else:
    # Fallback untuk development lokal saja
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
# CORS_ALLOW_ALL_ORIGINS = True  # DIHAPUS — BUG-018

# App Config
APP_NAME = 'HRIS-SmartDesk'
APP_VERSION = '1.0.0'
COMPANY_NAME = 'SmartDesk Technology'
TRIAL_DAYS = 30

# Colors (untuk template)
BRAND_COLOR = '#c40000'

# Notification days
CONTRACT_EXPIRY_WARNING_DAYS = 30
PROBATION_END_WARNING_DAYS = 14

# ── Email ─────────────────────────────────────────────────────────────────────
# Otomatis pakai SMTP jika EMAIL_HOST_USER tersedia (production),
# fallback ke console (development/lokal)
_email_user = os.environ.get('EMAIL_HOST_USER', '')
if _email_user:
    EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST         = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT         = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS      = True
    EMAIL_HOST_USER    = _email_user
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get(
        'DEFAULT_FROM_EMAIL',
        f'HRIS SmartDesk <{_email_user}>'
    )
else:
    EMAIL_BACKEND     = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@hris-smartdesk.com'

HR_EMAIL_LIST = [
    e.strip()
    for e in os.environ.get('HR_EMAIL_LIST', '').split(',')
    if e.strip()
]

# Django auth redirect override
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ── Logging — tampilkan semua error Django ke console ─────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ── Demo & Trial Config ───────────────────────────────────────────────────────
TRIAL_DURASI_HARI = 30          # Durasi default trial (hari)
SITE_URL    = os.environ.get('SITE_URL',    'http://localhost:8000')
SALES_WA    = os.environ.get('SALES_WA',    '6281234567890')
SALES_EMAIL = os.environ.get('SALES_EMAIL', 'sales@hris-smartdesk.com')