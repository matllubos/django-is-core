from django.contrib.auth.models import User

from germanium.rest import ClientTestCase
from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase


class UIPermissionsTestCase(AsSuperuserTestCase, HelperTestCase, ClientTestCase):
    USER_UI_URL = '/user/'

    def test_non_logged_user_should_receive_302(self):
        resp = self.get(self.USER_UI_URL)
        self.assert_http_redirect(resp)

    @login(is_superuser=False)
    def test_home_view_should_return_ok(self):
        resp = self.get('/')
        self.assert_http_ok(resp)

    @login(is_superuser=True)
    def test_superuser_may_read_users_grid(self):
        resp = self.get(self.USER_UI_URL)
        self.assert_http_ok(resp)

    @login(is_superuser=False)
    def test_ouser_can_read_users_grid(self):
        resp = self.get(self.USER_UI_URL)
        self.assert_http_ok(resp)

    @login(is_superuser=True)
    def test_superuser_may_edit_user(self):
        user = self.get_user_obj()
        resp = self.get('%s%s/' % (self.USER_UI_URL, user.pk))
        self.assert_http_ok(resp)

        CHANGED_USERNAME = 'changed_nick'
        self.post('%s%s/' % (self.USER_UI_URL, user.pk), data={'edit-is-user-username': CHANGED_USERNAME})
        self.assert_http_ok(resp)
        self.assert_equal(User.objects.get(pk=user.pk).username, CHANGED_USERNAME)

    @login(is_superuser=False)
    def test_only_superuser_may_edit_user(self):
        user = self.get_user_obj()
        resp = self.get('%s%s/' % (self.USER_UI_URL, user.pk))
        self.assert_http_forbidden(resp)

        CHANGED_USERNAME = 'changed_nick'
        self.post('%s%s/' % (self.USER_UI_URL, user.pk), data={'edit-is-user-username': CHANGED_USERNAME})
        self.assert_http_forbidden(resp)
        self.assert_not_equal(User.objects.get(pk=user.pk).username, CHANGED_USERNAME)

    @login(is_superuser=False)
    def test_user_may_edit_itself(self):
        user = self.logged_user.user
        resp = self.get('%s%s/' % (self.USER_UI_URL, user.pk))
        self.assert_http_ok(resp)

        CHANGED_USERNAME = 'changed_nick'
        self.post('%s%s/' % (self.USER_UI_URL, user.pk), data={'edit-is-user-username': CHANGED_USERNAME})
        self.assert_http_ok(resp)
        self.assert_equal(User.objects.get(pk=user.pk).username, CHANGED_USERNAME)

    @login(is_superuser=True)
    def test_superuser_may_add_user(self):
        USERNAME = 'new_nick'

        resp = self.post('%sadd/' % self.USER_UI_URL, data={'add-is-user-username': USERNAME,
                                                             'add-is-user-password': 'password'})
        self.assert_http_redirect(resp)
        self.assert_true(User.objects.filter(username=USERNAME).exists())

    @login(is_superuser=False)
    def test_only_superuser_may_add_user(self):
        USERNAME = 'new_nick'

        resp = self.post('%sadd/' % self.USER_UI_URL, data={'add-is-user-username': USERNAME,
                                                             'add-is-user-password': 'password'})
        self.assert_http_forbidden(resp)
        self.assert_false(User.objects.filter(username=USERNAME).exists())
