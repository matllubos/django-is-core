from functools import wraps

from django.utils.decorators import available_attrs


def auth_token_renewal_exempt(view_func):
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    wrapped_view.auth_token_renewal_exempt = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
