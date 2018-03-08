from collections import OrderedDict

from importlib import import_module

from django.conf import settings
from django.utils.encoding import force_text
from django.apps import apps


class App:

    def __init__(self):
        self.cores = []

    def add_core(self, core):
        if core not in self.cores:
            self.cores.append(core)


class CoresLoader:

    def __init__(self):
        self.apps = OrderedDict()

    def register_core(self, app_label, core):
        app = self.apps.get(app_label, App())
        app.add_core(core)
        self.apps[app_label] = app

    def _init_apps(self):
        import_module('is_core.main')

        for app in apps.get_app_configs():
            try:
                import_module('{}.cores'.format(app.name))
            except ImportError as ex:
                if force_text(ex) != 'No module named \'{}.cores\''.format(app.name):
                    raise ex

    def get_cores(self):
        self._init_apps()

        for app in self.apps.values():
            for core in app.cores:
                yield core

loader = CoresLoader()
register_core = loader.register_core
get_cores = loader.get_cores
