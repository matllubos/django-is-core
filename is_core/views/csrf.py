from django.utils.translation import ugettext_lazy as _

from is_core.exceptions.response import response_exception_factory


def csrf_failure(request, reason=''):
    return response_exception_factory(request, 403, _('Csrf Token expired'), reason)
