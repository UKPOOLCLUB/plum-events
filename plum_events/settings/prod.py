from .base import *
import dj_database_url

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = [
    'plum-events.onrender.com',  # ✅ this must match your actual Render subdomain
    'www.plumevents.com',        # optional, for when you add a custom domain
    'plumevents.com',
]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Production security settings
SECURE_HSTS_SECONDS = 3600
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
