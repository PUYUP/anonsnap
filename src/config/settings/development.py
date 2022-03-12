from .project import *

DEBUG = True

# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django-anonsnap',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': HOST,   # Or an IP Address that your DB is hosted on
        'PORT': '',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        }
    }
}

# GMAIL SMTP
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'anonsnap@gmail.com'
EMAIL_HOST_PASSWORD = 'ind0nesi@AA'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# Django CORS
# ------------------------------------------------------------------------------
# https://pypi.org/project/django-cors-headers/
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost',
    'http://localhost:8100',
    'http://localhost:4200',
]

# Django csrf
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/csrf/
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = None
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:8100',
    'http://localhost:8101',
]
