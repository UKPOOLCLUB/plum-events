from .base import *

DEBUG = True

SECRET_KEY = 'your-local-dev-key'  # optional: keep it here or load from env

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'plum_events',
        'USER': 'danielpickering',
        'PASSWORD': '',  # or use os.environ.get('DB_PASSWORD')
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
