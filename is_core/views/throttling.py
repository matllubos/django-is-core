from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from is_core.exceptions.response import response_exception_factory


def throttling_failure_view(request, exception):
    return response_exception_factory(request, 429, _('Too Many Requests'), force_text(exception))
