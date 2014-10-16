

class HttpRedirectException(Exception):

    def __init__(self, url):
        self.url = url


class HttpUnauthorizedException(Exception):
    pass


class HttpForbiddenException(Exception):
    pass
