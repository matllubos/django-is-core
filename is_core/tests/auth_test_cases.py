from is_core import config


class RestAuthMixin(object):

    def authorize(self, username, password):
        if config.AUTH_USE_TOKENS:
            resp = self.post('%sapi/' % config.LOGIN_URL,
                             data=self.serialize({config.USERNAME: username, config.PASSWORD: password}))
            self.assert_valid_JSON_response(resp, 'REST authorization fail: %s' % resp)
            self.default_headers[config.AUTH_HEADER_NAME] = self.deserialize(resp).get('token')
        else:
            super(RestAuthMixin, self).authorize(username, password)