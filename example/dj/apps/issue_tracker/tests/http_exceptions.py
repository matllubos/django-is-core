from germanium.rest import RESTTestCase
from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase


class HttpExceptionsTestCase(AsSuperuserTestCase, HelperTestCase, RESTTestCase):
    ISSUE_API_URL = '/api/issue/'
    USER_API_URL = '/api/user/'
    ACCEPT_TYPES = ('application/json', 'text/xml', 'text/csv',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    def test_401_exception(self):
        for accept_type in self.ACCEPT_TYPES:
            resp = self.get(self.ISSUE_API_URL, headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_unauthorized(resp)

    @login(is_superuser=False)
    def test_403_exception(self):
        user = self.get_user_obj()
        for accept_type in self.ACCEPT_TYPES:
            resp = self.get('%s%s/' % (self.USER_API_URL, user.pk), headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_forbidden(resp)

    @login(is_superuser=False)
    def test_404_exception(self):
        for accept_type in self.ACCEPT_TYPES:
            resp = self.get('%s%s/' % (self.ISSUE_API_URL, 5), headers={'HTTP_ACCEPT': accept_type})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_not_found(resp)

    @login(is_superuser=True)
    def test_403_csrf_exception(self):
        self.c = self.client_class(enforce_csrf_checks=True)
        for accept_type in self.ACCEPT_TYPES:
            resp = self.post(self.ISSUE_API_URL, self.serialize({}), headers={'HTTP_ACCEPT': accept_type, 'CONTENT_TYPE': 'application/json'})
            self.assert_in(accept_type, resp['Content-Type'])
            self.assert_http_forbidden(resp)
