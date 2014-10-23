from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from is_core.exceptions.response import responseexception_factory


def throttling_failure_view(request, exception):
    return responseexception_factory(request, 429, _('Too Many Requests'), force_text(exception))
