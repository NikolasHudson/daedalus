"""
Local development settings for daedlaus project.
This file allows local development without Docker.
"""

import os
from pathlib import Path
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Database - Use SQLite for local development
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Tailwind development configuration
TAILWIND_DEV_MODE = True

# Email settings for development (print to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]