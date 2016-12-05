from django.core.exceptions import ImproperlyConfigured

from security.utils import get_throttling_validators
from security.throttling import UnsuccessfulLoginThrottlingValidator, SuccessfulLoginThrottlingValidator


try:
    LOGIN_THROTTLING_VALIDATORS = get_throttling_validators('is_core_login_validators')
except ImproperlyConfigured:
    LOGIN_THROTTLING_VALIDATORS = (
        UnsuccessfulLoginThrottlingValidator(60, 2),
        UnsuccessfulLoginThrottlingValidator(10 * 60, 10),
        SuccessfulLoginThrottlingValidator(60, 2),
        SuccessfulLoginThrottlingValidator(10 * 60, 10),
    )
