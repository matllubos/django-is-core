# Apply patch only if django is installed
try:
    import django
    from .models.patch import *
except ImportError:
    pass
