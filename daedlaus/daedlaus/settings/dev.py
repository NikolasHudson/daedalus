"""
Development settings for daedlaus project.
"""

import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DATABASE_NAME', 'daedlaus'),
        'USER': os.environ.get('DATABASE_USERNAME', 'daedlaus_user'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'daedlaus_password'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# Tailwind development configuration
TAILWIND_DEV_MODE = True

# Email settings for development (print to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug Toolbar disabled temporarily
from .base import INSTALLED_APPS, MIDDLEWARE
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")