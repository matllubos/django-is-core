from __future__ import unicode_literals

from is_core.auth import RestAuthWrapper


class RestTokenAuthWrapper(RestAuthWrapper):

    def is_authenticated(self, request):
        if not request.token.is_from_header:
            return False
        return super(RestTokenAuthWrapper, self).is_authenticated(request)
