
def autodiscover():
    from django.conf import settings
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        # Attempt to import the app's view module.
        # TODO: catch only some exceptions
        try:
            import_module('%s.views' % app)
        except ImportError as ex:
            pass

VERSION = (0, 2, 7)

def get_version():
    return '.'.join(map(str, VERSION))

