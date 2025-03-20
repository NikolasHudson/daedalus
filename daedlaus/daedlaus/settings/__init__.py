from .base import *

import os

# Default to development settings
environment = os.environ.get('DJANGO_ENVIRONMENT', 'dev')

if environment == 'prod':
    from .prod import *
else:
    from .dev import *