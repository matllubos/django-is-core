from __future__ import unicode_literals

from security.models import LoggedRequest
from security.decorators import hide_request_body_all, throttling_all

from is_core.auth_token.default.views import TokenLoginView as DefaultTokenLoginView
from is_core.auth_token.auth_security import LOGIN_THROTTLING_VALIDATORS


@throttling_all(*LOGIN_THROTTLING_VALIDATORS)
@hide_request_body_all
class TokenLoginView(DefaultTokenLoginView):

    def form_valid(self, form):
        if getattr(self.request, '_logged_request', False):
            self.request._logged_request.type = LoggedRequest.SUCCESSFUL_LOGIN_REQUEST
        return super(TokenLoginView, self).form_valid(form)

    def form_invalid(self, form):
        if getattr(self.request, '_logged_request', False):
            self.request._logged_request.type = LoggedRequest.UNSUCCESSFUL_LOGIN_REQUEST
        return super(TokenLoginView, self).form_invalid(form)
