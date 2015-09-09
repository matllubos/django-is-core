from importlib import import_module

from is_core.config import CORE_LOGIN_THROTTLING_VALIDATORS
from django.core.exceptions import ImproperlyConfigured

try:
    LOGIN_THROTTLING_VALIDATORS_MODULE, LOGIN_THROTTLING_VALIDATORS_VAR = CORE_LOGIN_THROTTLING_VALIDATORS.rsplit('.',
                                                                                                                  1)
    LOGIN_THROTTLING_VALIDATORS = getattr(import_module(LOGIN_THROTTLING_VALIDATORS_MODULE), 
                                          LOGIN_THROTTLING_VALIDATORS_VAR)
except ImportError:
    raise ImproperlyConfigured('Configuration CORE_LOGIN_THROTTLING_VALIDATORS does not contain valid module')
