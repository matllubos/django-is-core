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