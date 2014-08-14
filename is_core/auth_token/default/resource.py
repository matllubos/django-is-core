from __future__ import unicode_literals

from piston.utils import rc

from is_core.rest.resource import RestResource, HeadersResult
from is_core.auth_token import login, logout
from is_core.auth_token.forms import TokenAuthenticationForm


class AuthResource(RestResource):
    login_required = False
    allowed_methods = ('POST', 'DELETE')
    form_class = TokenAuthenticationForm

    def _sucessful_login(self, request):
        pass

    def _unsucessful_login(self, request):
        pass

    def create(self, request, pk=None):
        if not request.data:
            return rc.BAD_REQUEST
        form = self.form_class(data=request.data)

        errors = form.is_invalid()
        if errors:
            self._unsucessful_login(request)
            return HeadersResult({'errors': errors}, status_code=400)

        self._sucessful_login(request)
        login(self.request, form.get_user(), not form.is_permanent())
        return {'token': request.token.key, 'user': form.get_user()}

    def delete(self, request, pk=None):
        if self.request.user.is_authenticated():
            logout(self.request)
        return rc.DELETED

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    @classmethod
    def has_delete_permission(cls, request, obj=None, via=None):
        return request.user.is_authenticated() and super(AuthResource, cls).has_delete_permission(request, obj)
