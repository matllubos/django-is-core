from django.core.exceptions import ImproperlyConfigured


class UIOptions(object):
    def __init__(self, model):
        self.extra_selecbox_fields = {}

        if hasattr(model, 'UIMeta'):
            self.extra_selecbox_fields = getattr(model.UIMeta, 'extra_selecbox_fields', self.extra_selecbox_fields)


class RestOptions(object):
    def __init__(self, model):
        from is_core.rest.utils import model_default_rest_fields

        self.fields = model_default_rest_fields(model)
        self.default_list_fields = self.fields
        self.default_obj_fields = self.fields

        if hasattr(model, 'RestMeta'):
            self.fields = getattr(model.RestMeta, 'fields', self.fields)
            self.default_list_fields = getattr(model.RestMeta, 'default_list_fields' , self.default_list_fields)
            self.default_obj_fields = getattr(model.RestMeta, 'default_obj_fields', self.default_obj_fields)

        self.fields = set(self.fields)
        self.default_list_fields = set(self.default_list_fields)
        self.default_obj_fields = set(self.default_obj_fields)


try:
    from django.db import models

    for model_cls in models.get_models():
        model_cls._rest_meta = RestOptions(model_cls)
        model_cls._ui_meta = UIOptions(model_cls)
except ImproperlyConfigured:
    pass