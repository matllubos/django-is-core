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

ELASTICSEARCH_DATABASE = dict(
    hosts=[{'host': 'localhost', 'port': 9200}],
)

PYDJAMODB_DATABASE = {
    'HOST': 'http://localhost:8000',
    'AWS_ACCESS_KEY_ID': '_',
    'AWS_SECRET_ACCESS_KEY': '_',
    'AWS_REGION': None,
    'TABLE_PREFIX': 'pyston',
    'BILLING_MODE': 'PAY_PER_REQUEST',
}

STATIC_ROOT = ''

# Additional locations of static files
STATICFILES_DIRS = (
    STATICFILES_ROOT,
)
