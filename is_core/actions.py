from django.utils.encoding import force_text

class Action(dict):

    def __init__(self, name, verbose_name, type, class_name=None):
        super(Action, self).__init__()
        self.update({'name': name, 'verbose_name': force_text(verbose_name), 'type': type})
        if class_name:
            self['class_name'] = class_name


class WebAction(Action):

    def __init__(self, name, verbose_name, class_name=None):
        super(WebAction, self).__init__(name, verbose_name, 'web', class_name)


class RestAction(Action):

    def __init__(self, name, verbose_name, method, data=None, class_name=None):
        super(RestAction, self).__init__(name, verbose_name, 'rest', class_name)
        self['method'] = method
        if data:
            self['data'] = data
