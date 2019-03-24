from .version import *


# Apply patch only if django is installed
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from django.db import models
        from .filters.patch import *
        from .models.patch import *
        from .forms.patch import *
    except ImproperlyConfigured:
        pass
except ImportError:
    pass
