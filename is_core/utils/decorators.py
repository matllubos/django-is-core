def short_description(description):
    """Sets 'short_description' attribute (this attribute is used by list_display and formular)."""
    def decorator(func):
        if isinstance(func, property):
            func = func.fget
        func.short_description = description
        return func
    return decorator
