from is_core import config
from is_core.utils import header_name_to_django


class RESTAuthMixin(object):

    def authorize(self, username, password):
        if config.IS_CORE_AUTH_USE_TOKENS:
            resp = self.post(config.IS_CORE_LOGIN_API_URL,
                             data=self.serialize({config.IS_CORE_USERNAME: username, config.IS_CORE_PASSWORD: password}))
            self.assert_valid_JSON_response(resp, 'REST authorization fail: %s' % resp)
            self.default_headers[header_name_to_django(config.IS_CORE_AUTH_HEADER_NAME)] = (
                self.deserialize(resp).get('token')
            )
        else:
            super(RESTAuthMixin, self).authorize(username, password)