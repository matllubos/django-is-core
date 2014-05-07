from __future__ import unicode_literals

from django.http.response import HttpResponseForbidden

from is_core.auth import Auth


class RestAuthentication(Auth):

    def challenge(self):
        return HttpResponseForbidden()
