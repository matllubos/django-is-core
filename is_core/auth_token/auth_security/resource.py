from __future__ import unicode_literals

from is_core.auth_token.default.resource import AuthResource as DefaultAuthResource

from security.models import LoggedRequest
from security.decorators import hide_request_body_all


@hide_request_body_all
class AuthResource(DefaultAuthResource):

    def _sucessful_login(self, request):
        if getattr(self.request, '_logged_request', False):
            self.request._logged_request.type = LoggedRequest.UNSUCCESSFUL_LOGIN_REQUEST

    def _unsucessful_login(self, request):
        if getattr(self.request, '_logged_request', False):
            self.request._logged_request.type = LoggedRequest.UNSUCCESSFUL_LOGIN_REQUEST
