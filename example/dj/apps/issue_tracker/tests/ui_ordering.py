from germanium.annotations import login
from germanium.test_cases.client import ClientTestCase
from germanium.tools import assert_in

from .test_case import HelperTestCase, AsSuperuserTestCase


__all__ =(
    'UIOrderingTestCase',
)


class UIOrderingTestCase(AsSuperuserTestCase, HelperTestCase, ClientTestCase):
    ISSUE_UI_URL = '/issue/'

    @login(is_superuser=True)
    def test_superuser_may_read_users_grid(self):
        resp = self.get(self.ISSUE_UI_URL)
        assert_in(b'data-col="watched_by_string"', resp.content)
