import re
import sys
import types

from django.http.request import QueryDict
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text


def query_string_from_dict(qs_dict):
    qs_prepared_dict = SortedDict()
    for key, val in qs_dict.items():
        if isinstance(val, list):
            val = '[%s]' % ','.join([force_text(v) for v in val])
        qs_prepared_dict[key] = val

    qdict = QueryDict('').copy()
    qdict.update(qs_prepared_dict)
    return qdict.urlencode()


def str_to_class(class_string):
    module_name, class_name = class_string.rsplit('.', 1)
    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), class_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_new_class_name(prefix, klass):
    prefix = prefix.replace('-', ' ').title()
    prefix = re.sub(r'\s+', '', prefix)
    return prefix + klass.__name__


def flatten_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    field_names = []
    for _, opts in fieldsets:
        for field in opts.get('fields', ()):
            if isinstance(field, (list, tuple)):
                field_names.extend(field)
            else:
                field_names.append(field)
    return field_names


class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
