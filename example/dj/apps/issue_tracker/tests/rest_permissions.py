from germanium.rest import RESTTestCase

from is_core.tests.auth_test_cases import RESTAuthMixin

from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase

from issue_tracker.models import Issue


class RESTPermissionsTestCase(AsSuperuserTestCase, RESTAuthMixin, HelperTestCase, RESTTestCase):
    USER_API_URL = '/api/user/'
    ISSUE_API_URL = '/api/issue/'
    USER_ISSUES_API_URL = '/api/user/%(user_pk)s/issue-number/'

    def test_non_logged_user_should_receive_401(self):
        resp = self.get(self.USER_API_URL)
        self.assert_http_unauthorized(resp)

    @login(is_superuser=True)
    def test_superuser_may_read_user_data(self):
        [self.get_user_obj() for _ in range(5)]

        resp = self.get(self.USER_API_URL)
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_equal(len(output), 6)

    @login(is_superuser=False)
    def test_user_can_read_all_user_data(self):
        [self.get_user_obj() for _ in range(5)]

        resp = self.get(self.USER_API_URL)
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_equal(len(output), 1)
        self.assert_equal(output[0]['id'], self.logged_user.user.pk)

    @login(is_superuser=False)
    def test_user_can_read_only_itself(self):
        resp = self.get(('%s%s/') % (self.USER_API_URL, self.logged_user.user.pk))
        self.assert_valid_JSON_response(resp)

        user = self.get_user_obj()
        resp = self.get(('%s%s/') % (self.USER_API_URL, user.pk))
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
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_valid_JSON_response(resp)

    @login(is_superuser=False)
    def test_user_can_update_only_itself(self):
        user = self.get_user_obj()
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_http_forbidden(resp)

        user = self.logged_user.user
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data=self.serialize({}))
        self.assert_valid_JSON_response(resp)

    @login(is_superuser=True)
    def test_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s%s/' % (self.USER_API_URL, user.pk))
        self.assert_http_accepted(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s%s/' % (self.USER_API_URL, user.pk))
        self.assert_http_forbidden(resp)

    def test_not_logged_user_can_not_get_number_of_user_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        self.assert_http_unauthorized(resp)

    @login(is_superuser=True)
    def test_superuser_can_get_number_of_user_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        self.assert_valid_JSON_response(resp)

        output = self.deserialize(resp)
        self.assert_equal(output['created'], 0)
        self.assert_equal(output['watching'], 0)

    @login(is_superuser=False)
    def test_only_superuser_can_get_number_of_other_users_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        self.assert_http_forbidden(resp)

    @login(is_superuser=False)
    def test_user_can_get_number_of_its_issues(self):
        user = self.logged_user.user
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_equal(output['created'], 0)
        self.assert_equal(output['watching'], 0)

    @login(is_superuser=True)
    def test_issue_can_be_created_only_via_user(self):
        before_issue_count = Issue.objects.count()

        user_data = self.get_user_data()
        issue_data = self.get_issue_data(exclude=['leader'])
        user_data['leading_issue'] = issue_data

        resp = self.post(self.USER_API_URL, data=self.serialize(user_data))
        self.assert_valid_JSON_created_response(resp)
        self.assert_equal(Issue.objects.count(), before_issue_count + 1)

        resp = self.post(self.ISSUE_API_URL, data=self.serialize(self.get_issue_data()))
        self.assert_http_forbidden(resp)
        self.assert_equal(Issue.objects.count(), before_issue_count + 1)
