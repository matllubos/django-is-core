import six

from collections import OrderedDict

from django.conf import settings
from django.utils.encoding import force_text

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module


class App(object):

    def __init__(self):
        self.cores = []

    def add_core(self, core):
        if core not in self.cores:
            self.cores.append(core)


class CoresLoader(object):

    def __init__(self):
        self.apps = OrderedDict()

    def register_core(self, app_label, core):
        app = self.apps.get(app_label, App())
        app.add_core(core)
        self.apps[app_label] = app

    def _init_apps(self):
        import_module('is_core.main')
        for app in settings.INSTALLED_APPS:
            try:
                import_module('%s.cores' % app)
            except ImportError as ex:
                if ((six.PY2 and force_text(ex) != 'No module named cores') or
                        (six.PY3 and force_text(ex) != 'No module named \'%s.cores\'' % app)):
                    raise ex

    def get_cores(self):
        self._init_apps()

        for app in self.apps.values():
            for core in app.cores:
                yield core

loader = CoresLoader()
register_core = loader.register_core
get_cores = loader.get_cores
