from germanium.rest import RESTTestCase
from germanium.anotations import login

from is_core.tests.auth_test_cases import RestAuthMixin

from .test_case import HelperTestCase, AsSuperuserTestCase


class HttpExceptionsTestCase(AsSuperuserTestCase, RestAuthMixin, HelperTestCase, RESTTestCase):
    ISSUE_API_URL = '/api/issue'
    USER_API_URL = '/api/user'

    def test_401_exception(self):
        for accept_type in ('application/json', 'text/xml', 'application/x-yaml',
                            'application/python-pickle', 'text/csv', 'text/html'):
            resp = self.get(self.ISSUE_API_URL, headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_unauthorized(resp)

    @login(is_superuser=False)
    def test_403_exception(self):
        user = self.get_user_obj()
        for accept_type in ('application/json', 'text/xml', 'application/x-yaml',
                            'application/python-pickle', 'text/csv', 'text/html'):
            resp = self.get('%s/%s' % (self.USER_API_URL, user.pk), headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_forbidden(resp)

    @login(is_superuser=False)
    def test_404_exception(self):
        for accept_type in ('application/json', 'text/xml', 'application/x-yaml',
                            'application/python-pickle', 'text/csv', 'text/html'):
            resp = self.get('%s/%s' % (self.ISSUE_API_URL, 5), headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_not_found(resp)

    '''@login(is_superuser=False)
    def test_429_exception(self):
        for accept_type in ('application/json', 'text/xml', 'application/x-yaml',
                            'application/python-pickle', 'text/csv', 'text/html'):
            [self.get(self.ISSUE_API_URL, headers={'HTTP_ACCEPT': accept_type}) for _ in range(100)]
            resp = self.get(self.ISSUE_API_URL, headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_too_many_requests(resp)'''
