# Apply patch only if django is installed
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from django.db import models  # noqa: F401
        from .models import patch as model_patch  # noqa: F401
        from .forms import patch as form_patch  # noqa: F401
    except ImproperlyConfigured:
        pass
except ImportError:
    pass
