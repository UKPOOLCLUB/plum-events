from .base import *

DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-local-dev-key')

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'plum_events',
        'USER': 'danielpickering',
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),  # keep this secret!
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Use console backend for emails during dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Stripe keys are loaded from the environment via base.py (do not set here)
