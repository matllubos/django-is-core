from django.utils.translation import ugettext_lazy as _

from pyston.utils import JsonObj


class Action(JsonObj):

    def __init__(self, name, verbose_name, type, class_name=None):
        super(Action, self).__init__()
        self.name = name
        self.verbose_name = verbose_name
        self.type = type
        if class_name:
            self.class_name = class_name


class WebAction(Action):

    def __init__(self, name, verbose_name, class_name=None, target=None, rel=None):
        super(WebAction, self).__init__(name, verbose_name, 'web', class_name)
        if target:
            self.target = target
        if rel:
            self.rel = rel


class RESTAction(Action):

    def __init__(self, name, verbose_name, method, data=None, class_name=None, success_text=None):
        super(RESTAction, self).__init__(name, verbose_name, 'rest', class_name)
        self.method = method
        if data:
            self.data = data
        if success_text:
            self.success_text = success_text


class ConfirmRESTAction(RESTAction):

    def __init__(self, name, verbose_name, method, data=None, class_name=None, confirm_dialog=None, success_text=None):
        super(ConfirmRESTAction, self).__init__(name, verbose_name, method, data, class_name, success_text)
        self.confirm = confirm_dialog

    class ConfirmDialog(JsonObj):

        def __init__(self, text, title=None, true_label=None, false_label=None):
            self.true_label = true_label or _('Yes')
            self.false_label = false_label or _('No')
            self.title = title or _('Are you sure?')
            self.text = text
