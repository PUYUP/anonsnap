from .project import *


# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'anonsnap',
        'USER': 'anonsnap',
        'PASSWORD': 'LQK$hRFJqHWZQy$@K6',
        'HOST': HOST,   # Or an IP Address that your DB is hosted on
        'PORT': '',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        }
    }
}

# Static files (CSS, JavaScript, Images)
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
IMAGE_FOLDER = os.path.join(BASE_DIR, 'image')
