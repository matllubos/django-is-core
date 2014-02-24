from is_core.rest.auth import RestAuthentication


class RestTokenAuthentication(RestAuthentication):

    def is_authenticated(self, request):
        if not request.token.is_from_header:
            return False
        return super(RestTokenAuthentication, self).is_authenticated(request)
