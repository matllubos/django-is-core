def merge(origin, *args):
    """
    Merges given dictionaries, `origin` will not be changed.
    TODO: Remove this function after `django-chamber` upgrade
    """
    copy = origin.copy()
    for dictionary in args:
        copy.update(dictionary)
    return copy
