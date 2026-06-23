"""
Development settings for EMS project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database — SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use simple static file storage in development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Console email backend for development (prints to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS — allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable CSRF for API testing in development (optional)
# CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']

# Show detailed error pages
INTERNAL_IPS = ['127.0.0.1']
