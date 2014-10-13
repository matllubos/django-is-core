from dj.settings.base import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

ALLOWED_HOSTS = ['localhost']

# URL with protocol (and port)
PROJECT_URL = 'localhost:8000'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'var', 'db', 'sqlite.db'),
        'USER': '',
        'PASSWORD': '',
    },
}

STATIC_ROOT = ''

# Additional locations of static files
STATICFILES_DIRS = (
    STATICFILES_ROOT,
)
