from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

from is_core.config import IS_CORE_LOGIN_THROTTLING_VALIDATORS


try:
    LOGIN_THROTTLING_VALIDATORS_MODULE, LOGIN_THROTTLING_VALIDATORS_VAR = (
        IS_CORE_LOGIN_THROTTLING_VALIDATORS.rsplit('.', 1)
    )
    LOGIN_THROTTLING_VALIDATORS = getattr(import_module(LOGIN_THROTTLING_VALIDATORS_MODULE),
                                          LOGIN_THROTTLING_VALIDATORS_VAR)
except ImportError:
    raise ImproperlyConfigured('Configuration IS_CORE_LOGIN_THROTTLING_VALIDATORS does not contain valid module')
