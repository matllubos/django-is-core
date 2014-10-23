from django.utils.translation import ugettext_lazy as _

from is_core.exceptions.response import responseexception_factory


def csrf_failure(request, reason=''):
    return responseexception_factory(request, 403, _('Csrf Token expired'), reason)
