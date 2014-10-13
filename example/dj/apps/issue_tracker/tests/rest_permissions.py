from germanium.rest import RESTTestCase

from is_core.tests.auth_test_cases import RestAuthMixin

from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase


class RestPermissionsTestCase(AsSuperuserTestCase, RestAuthMixin, HelperTestCase, RESTTestCase):
    USER_API_URL = '/api/user'

    def test_non_logged_user_should_receive_401(self):
        resp = self.get(self.USER_API_URL)
        self.assert_http_unauthorized(resp)

    @login(is_superuser=True)
    def test_superuser_may_read_user_data(self):
        resp = self.get(self.USER_API_URL)
        self.assert_valid_JSON_response(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_read_all_user_data(self):
        resp = self.get(self.USER_API_URL)
        self.assert_http_forbidden(resp)

    @login(is_superuser=False)
    def test_user_can_read_only_itself(self):
        resp = self.get(('%s/%s') % (self.USER_API_URL, self.logged_user.user.pk))
        self.assert_valid_JSON_response(resp)

        user = self.get_user_obj()
        resp = self.get(('%s/%s') % (self.USER_API_URL, user.pk))
        self.assert_http_forbidden(resp)

    @login(is_superuser=True)
    def test_superuser_can_add_new_user(self):
        resp = self.post(self.USER_API_URL, data=self.serialize(self.get_user_data()))
        self.assert_valid_JSON_created_response(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_add_new_user(self):
        resp = self.post(self.USER_API_URL, data=self.serialize(self.get_user_data()))
        self.assert_http_forbidden(resp)

    @login(is_superuser=True)
    def test_superuser_can_add_update_user(self):
        user = self.get_user_obj()
        resp = self.put('%s/%s' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_valid_JSON_response(resp)

    @login(is_superuser=False)
    def test_user_can_update_only_itself(self):
        user = self.get_user_obj()
        resp = self.put('%s/%s' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_http_forbidden(resp)

        user = self.logged_user.user
        resp = self.put('%s/%s' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_valid_JSON_response(resp)

    @login(is_superuser=True)
    def test_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s/%s' % (self.USER_API_URL, user.pk))
        self.assert_http_accepted(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s/%s' % (self.USER_API_URL, user.pk))
        self.assert_http_forbidden(resp)
