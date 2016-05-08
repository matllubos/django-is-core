from django.utils.datastructures import SortedDict
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.encoding import force_text


class App(object):

    def __init__(self):
        self.cores = set()


class CoresLoader(object):

    def __init__(self):
        self.apps = SortedDict()

    def register_core(self, app_label, core):
        app = self.apps.get(app_label, App())
        app.cores.add(core)
        self.apps[app_label] = app

    def _init_apps(self):
        import_module('is_core.main')
        for app in settings.INSTALLED_APPS:
            try:
                import_module('%s.cores' % app)
            except ImportError as ex:
                if force_text(ex) != 'No module named cores':
                    print app
                    raise ex

    def get_cores(self):
        self._init_apps()

        for app in self.apps.values():
            for core in app.cores:
                yield core

loader = CoresLoader()
register_core = loader.register_core
get_cores = loader.get_cores
