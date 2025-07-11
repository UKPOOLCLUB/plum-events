from .base import *
import dj_database_url
import os

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = [
    'plum-events.onrender.com',
    'www.plumevents.co.uk',
    'plumevents.co.uk',
]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'contact@plumevents.co.uk')

print("DEBUG: STRIPE_SECRET_KEY (first 5 chars):", os.environ.get('STRIPE_SECRET_KEY', '')[:5])

# Stripe keys from environment (load these in your .env or Render dashboard)
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Production security
SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
