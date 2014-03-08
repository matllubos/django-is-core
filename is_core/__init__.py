from .version import *

# Apply patch only if django is installed
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from django.db import models
        from .models.patch import *
    except ImproperlyConfigured:
        pass
except ImportError:
    pass
