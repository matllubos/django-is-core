from django.contrib.auth.forms import AuthenticationForm

from is_core.rest.handler import RestHandler, HeadersResult
from is_core.rest.utils import rc
from is_core.auth_token import login
from is_core.forms import RestFormMixin


class RestAuthenticationForm(RestFormMixin, AuthenticationForm):
    pass


class AuthHandler(RestHandler):

    allowed_methods = ('POST',)
    form_class = AuthenticationForm

    def create(self, request, pk=None):
        if not request.data:
            return rc.BAD_REQUEST
        form = self.form_class(data=request.data)

        errors = form.is_invalid()
        if errors:
            return HeadersResult({'errors': errors}, status_code=400)

        login(request, form.get_user())
        return {'token': request.token.key}
