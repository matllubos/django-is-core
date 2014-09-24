from __future__ import unicode_literals

from is_core.auth_token.default.views import TokenLoginView as DefaultTokenLoginView

from security.middleware import SecurityData
from security.models import LoggedRequest
from security.decorators import hide_request_body_all


@hide_request_body_all
class TokenLoginView(DefaultTokenLoginView):

    def form_invalid(self, form):
        self.request._security_data = SecurityData(LoggedRequest.UNSUCCESSFUL_LOGIN_REQUEST)
        return super(TokenLoginView, self).form_invalid(form)

    def form_valid(self, form):
        self.request._security_data = SecurityData(LoggedRequest.SUCCESSFUL_LOGIN_REQUEST)
        return super(TokenLoginView, self).form_valid(form)
