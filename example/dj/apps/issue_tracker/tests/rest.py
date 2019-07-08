from germanium.decorators import login
from germanium.test_cases.rest import RESTTestCase
from germanium.tools import assert_equal
from germanium.tools.rest import assert_valid_JSON_response

from .factories import IssueFactory
from .test_case import HelperTestCase, AsSuperuserTestCase

from issue_tracker.models import Issue


__all__ =(
    'RESTTestCase',
)


class RESTTestCase(AsSuperuserTestCase, HelperTestCase, RESTTestCase):

    USER_API_URL = '/api/user/'

    @login(is_superuser=True)
    def test_core_readonly_methods_should_be_returned(self):
        user = self.get_user_obj()
        IssueFactory(created_by=user)
        resp = self.get('{}{}/?_fields=created_issues_count'.format(self.USER_API_URL, user.pk))
        assert_valid_JSON_response(resp)
        assert_equal(resp.json()['created_issues_count'], 1)
