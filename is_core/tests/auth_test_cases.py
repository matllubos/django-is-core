from germanium.tools.rest import assert_valid_JSON_response

from is_core.config import settings
from is_core.utils import header_name_to_django
from is_core.auth_token.utils import create_auth_header_value


class RESTAuthMixin:

    def authorize(self, username, password):
        if settings.AUTH_USE_TOKENS:
            resp = self.post(settings.LOGIN_API_URL,
                             data={settings.USERNAME: username, settings.PASSWORD: password})
            assert_valid_JSON_response(resp, 'REST authorization fail: %s' % resp)
            self.default_headers[header_name_to_django(settings.AUTH_HEADER_NAME)] = (
                create_auth_header_value(self.deserialize(resp).get('token'))
            )
        else:
            super(RESTAuthMixin, self).authorize(username, password)
