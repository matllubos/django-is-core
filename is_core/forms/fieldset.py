import itertools


class Fieldsets:

    def __init__(self, *args):
        self.fieldsets = []
        for fieldset in args:
            self.fieldsets.append(fieldset)

    def get_fieldsets(self, request, obj):
        return self.fieldsets

    def get_fields_names(self, request, obj):
        result = []
        for fieldset in self.get_fieldsets(request, obj):
            result = itertools.chain(result, fieldset.get_fields_names(request, obj))
        return result

    def get_readonly_fields(self, request, obj):
        result = []
        for fieldset in self.get_fieldsets(request, obj):
            result = itertools.chain(result, fieldset.get_readonly_fields(request, obj))
        return result


class AbstractFieldset:

    def __init__(self, title):
        self.title = title

    def show(self, request, obj):
        return False

    def get_title(self, request, obj):
        return self.title

    def get_fields_names(self, request, obj):
        return ()

    def get_readonly_fields(self, request, obj):
        return ()


class Fieldset(AbstractFieldset):

    def __init__(self, title, fields):
        super(Fieldset, self).__init__(title)
        self.fields = fields

    def get_fields(self, request, obj):
        result = []
        for field in self.fields:
            if field.show(request, obj):
                result.append(field)
        return result

    def get_fields_names(self, request, obj):
        return [field.name for field in self.get_fields(request, obj)]

    def get_readonly_fields(self, request, obj):
        result = []
        for field in self.fields:
            if field.show(request, obj) and field.is_readonly(request, obj):
                result.append(field.name)
        return result

    def show(self, request, obj):
        return bool(self.get_fields(request, obj))


class InlineFieldset(AbstractFieldset):

    def __init__(self, title, inline_view):
        super(Fieldset, self).__init__(title)
        self.inline_view = inline_view

    def get_inline_view(self, request, obj):
        return self.inline_view

    def show(self, request, obj):
        return True


class Field:

    def __init__(self, name, readonly=None):
        self.name = name
        self.readonly = readonly

    def is_readonly(self, request, obj):
        return self.readonly

    def show(self, request, obj):
        return True
