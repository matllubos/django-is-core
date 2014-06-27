from __future__ import unicode_literals

from piston.utils import rc

from is_core.rest.resource import RestResource, HeadersResult
from is_core.auth_token import login, logout
from is_core.auth_token.forms import TokenAuthenticationForm


class AuthResource(RestResource):
    login_required = False
    allowed_methods = ('POST', 'DELETE')
    form_class = TokenAuthenticationForm

    def create(self, request, pk=None):
        if not request.data:
            return rc.BAD_REQUEST
        form = self.form_class(data=request.data)

        errors = form.is_invalid()
        if errors:
            return HeadersResult({'errors': errors}, status_code=400)

        login(self.request, form.get_user(), not form.is_permanent())
        return {'token': request.token.key}

    def delete(self, request, pk=None):
        if self.request.user.is_authenticated():
            logout(self.request)
        return rc.DELETED

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern
