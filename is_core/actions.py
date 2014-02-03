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

    def __init__(self, name, verbose_name, class_name=None):
        super(RestAction, self).__init__(name, verbose_name, 'rest', class_name)


class ActionPattern(object):

    def __init__(self, name, site_name):
        self.name = name
        self.site_name = site_name

    @property
    def pattern(self):
        return '%s:%s' % (self.site_name, self.name)


class WebActionPattern(ActionPattern):
    pass


class RestActionPattern(ActionPattern):

    def __init__(self, name, site_name, methods):
        super(RestActionPattern, self).__init__(name, site_name)
        self.methods = methods
