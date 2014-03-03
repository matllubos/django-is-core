from is_core import config


class RestAuthMixin(object):

    def authorize(self, username, password):
        super(RestAuthMixin, self).authorize(username, password)
        if config.AUTH_USE_TOKENS:
            self.default_headers[config.AUTH_HEADER_NAME] = self.c.cookies.get(config.AUTH_COOKIE_NAME).value
