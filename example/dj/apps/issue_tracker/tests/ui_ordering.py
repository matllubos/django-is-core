from django.contrib.auth.models import User

from germanium.rest import ClientTestCase
from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase


class UIOrderingTestCase(AsSuperuserTestCase, HelperTestCase, ClientTestCase):
    ISSUE_UI_URL = '/issue'

    @login(is_superuser=True)
    def test_superuser_may_read_users_grid(self):
        resp = self.get(self.ISSUE_UI_URL)
        self.assert_in('data-col="watched_by"', resp.content)
