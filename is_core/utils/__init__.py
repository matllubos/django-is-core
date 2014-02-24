import sys
import types

from django.http.request import QueryDict


def query_string_from_dict(qs_dict):
    qdict = QueryDict('').copy()
    qdict.update(qs_dict)
    return qdict.urlencode()


def str_to_class(class_string):
    module_name, class_name = class_string.rsplit('.', 1)

    # load the module, will raise ImportError if module cannot be loaded
    m = __import__(module_name, globals(), locals(), class_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def flatten_fieldsets(fieldsets):
    """Returns a list of field names from an admin fieldsets structure."""
    field_names = []
    for name, opts in fieldsets:
        for field in opts.get('fields', ()):
            if isinstance(field, (list, tuple)):
                field_names.extend(field)
            else:
                field_names.append(field)
    return field_names


def list_to_dict(list_obj):
    dict_obj = {}
    for val in list_obj:
        if isinstance(val, (list, tuple)):
            dict_obj[val[0]] = list_to_dict(val[1])
        else:
            dict_obj[val] = {}
    return dict_obj


def dict_to_list(dict_obj):
    list_obj = []
    for key, val in dict_obj.items():
        if val:
            list_obj.append((key, dict_to_list(val)))
        else:
            list_obj.append(key)
    return tuple(list_obj)


def flat_list(list_obj):
    flat_list_obj = []
    for val in list_obj:
        if isinstance(val, (list, tuple)):
            flat_list_obj.append(val[0])
        else:
            flat_list_obj.append(val)
    return flat_list_obj
