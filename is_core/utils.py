from django.http.request import QueryDict


def query_string_from_dict(qs_dict):
    qdict = QueryDict('').copy()
    qdict.update(qs_dict)
    return qdict.urlencode()
