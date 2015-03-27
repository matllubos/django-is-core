def short_description(description):
    """
    Sets 'short_description' attribute (this attribute is used by list_display and formular).
    """
    def decorator(func):
        func.short_description = description
        return func
    return decorator


def filter_class(filter_class):
    """
    Sets 'filter' class (this attribute is used inside grid and rest).
    """
    def decorator(func):
        func.filter = filter_class
        return func
    return decorator


def order_by(field_name):
    """
    Sets 'field name' (this is used for grid ordering)
    """
    def decorator(func):
        func.filter = filter_class
        return func
    return decorator

