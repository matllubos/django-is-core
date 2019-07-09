from germanium.decorators import login
from germanium.test_cases.rest import RESTTestCase
from germanium.tools import assert_equal, assert_false
from germanium.tools.http import (assert_http_forbidden, assert_http_unauthorized, assert_http_accepted,
                                  assert_http_not_found, assert_http_method_not_allowed)
from germanium.tools.rest import assert_valid_JSON_response, assert_valid_JSON_created_response

from .factories import IssueFactory, UserFactory
from .test_case import HelperTestCase, AsSuperuserTestCase

from issue_tracker.models import Issue


__all__ =(
    'RESTPermissionsTestCase',
)


class RESTPermissionsTestCase(AsSuperuserTestCase, HelperTestCase, RESTTestCase):

    USER_API_URL = '/api/user/'
    ISSUE_API_URL = '/api/issue/'
    USER_ISSUES_API_URL = '/api/user/%(user_pk)s/issue-number/'

    def test_non_logged_user_should_receive_401(self):
        resp = self.get(self.USER_API_URL)
        assert_http_unauthorized(resp)

    @login(is_superuser=True)
    def test_superuser_may_read_user_data(self):
        [self.get_user_obj() for _ in range(5)]

        resp = self.get(self.USER_API_URL)
        assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        assert_equal(len(output), 6)

    @login(is_superuser=False)
    def test_user_can_read_all_user_data(self):
        [self.get_user_obj() for _ in range(5)]

        resp = self.get(self.USER_API_URL)
        assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        assert_equal(len(output), 1)
        assert_equal(output[0]['id'], self.logged_user.user.pk)

    @login(is_superuser=False)
    def test_user_can_read_only_itself(self):
        resp = self.get(('%s%s/') % (self.USER_API_URL, self.logged_user.user.pk))
        assert_valid_JSON_response(resp)

        user = self.get_user_obj()
        resp = self.get(('%s%s/') % (self.USER_API_URL, user.pk))
        assert_http_not_found(resp)

    @login(is_superuser=True)
    def test_superuser_can_add_new_user(self):
        resp = self.post(self.USER_API_URL, data=self.get_user_data())
        assert_valid_JSON_created_response(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_add_new_user(self):
        resp = self.post(self.USER_API_URL, data=self.get_user_data())
        assert_http_forbidden(resp)

    @login(is_superuser=True)
    def test_superuser_can_add_update_user(self):
        user = self.get_user_obj()
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data={})
        assert_valid_JSON_response(resp)

    @login(is_superuser=False)
    def test_user_can_update_only_itself(self):
        user = self.get_user_obj()
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data={})
        assert_http_not_found(resp)

        user = self.logged_user.user
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data={})
        assert_valid_JSON_response(resp)

    @login(is_superuser=True)
    def test_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s%s/' % (self.USER_API_URL, user.pk))
        assert_http_accepted(resp)

    @login(is_superuser=False)
    def test_only_superuser_can_delete_new_user(self):
        user = self.get_user_obj()
        resp = self.delete('%s%s/' % (self.USER_API_URL, user.pk))
        assert_http_forbidden(resp)

    @login(is_superuser=False)
    def test_superuser_should_not_delete_another_superuser(self):
        user = self.get_user_obj(is_superuser=True)
        resp = self.delete('%s%s/' % (self.USER_API_URL, user.pk))
        assert_http_forbidden(resp)

    def test_not_logged_user_can_not_get_number_of_user_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        assert_http_unauthorized(resp)

    @login(is_superuser=True)
    def test_superuser_can_get_number_of_user_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        assert_valid_JSON_response(resp)

        output = self.deserialize(resp)
        assert_equal(output['created'], 0)
        assert_equal(output['watching'], 0)

    @login(is_superuser=False)
    def test_only_superuser_can_get_number_of_other_users_issues(self):
        user = self.get_user_obj()
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        assert_http_not_found(resp)

    @login(is_superuser=False)
    def test_user_can_get_number_of_its_issues(self):
        user = self.logged_user.user
        resp = self.get(self.USER_ISSUES_API_URL % {'user_pk': user.pk})
        assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        assert_equal(output['created'], 0)
        assert_equal(output['watching'], 0)

    @login(is_superuser=True)
    def test_issue_delete_should_not_be_supported_because_can_delete_is_disabled(self):
        assert_http_method_not_allowed(self.delete(self.ISSUE_API_URL + '1/'))

    @login(is_superuser=True)
    def test_issue_post_should_not_be_supported_because_can_create_is_disabled(self):
        assert_http_method_not_allowed(self.post(self.ISSUE_API_URL, data={}))

    @login(is_superuser=True)
    def test_issue_actions_should_not_contains_edit_because_update_is_disabled(self):
        IssueFactory()
        resp = self.get(self.ISSUE_API_URL+'?_fields=_actions')
        assert_equal(len(resp.json()[0]['_actions']), 1)
        assert_equal(resp.json()[0]['_actions'][0]['class_name'], 'detail')

    @login(is_superuser=True)
    def test_new_user_actions_should_contains_edit_and_delete_because_update_is_disabled(self):
        UserFactory()
        resp = self.get(self.USER_API_URL+'?_fields=_actions')
        assert_equal(len(resp.json()[1]['_actions']), 2)
        assert_equal({action['class_name'] for action in resp.json()[1]['_actions']}, {'edit', 'delete'})

    @login(is_superuser=True)
    def test_logged_user_actions_should_contains_only_edit_action(self):
        resp = self.get(self.USER_API_URL+'?_fields=_actions')
        assert_equal(len(resp.json()[0]['_actions']), 1)
        assert_equal({action['class_name'] for action in resp.json()[0]['_actions']}, {'edit'})

    @login(is_superuser=True)
    def test_superuser_should_read_username_and_is_superuser_fields(self):
        resp = self.get(self.USER_API_URL+'?_fields=username,is_superuser')
        assert_equal(set(resp.json()[0].keys()), {'username', 'is_superuser'})

    @login(is_superuser=False)
    def test_user_should_not_read_read_is_superuser_fields(self):
        resp = self.get(self.USER_API_URL+'?_fields=username,is_superuser')
        assert_equal(set(resp.json()[0].keys()), {'username'})

    @login(is_superuser=False)
    def test_user_should_not_update_is_superuser(self):
        user = self.logged_user.user
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data={'is_superuser': True})
        assert_valid_JSON_response(resp)
        user.refresh_from_db()
        assert_false(user.is_superuser)

    @login(is_superuser=True)
    def test_superuser_should_update_is_superuser(self):
        user = self.logged_user.user
        resp = self.put('%s%s/' % (self.USER_API_URL, user.pk), data={'is_superuser': False})
        assert_valid_JSON_response(resp)
        user.refresh_from_db()
        assert_false(user.is_superuser)
