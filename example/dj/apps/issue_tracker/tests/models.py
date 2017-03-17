from __future__ import unicode_literals

from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from germanium.test_cases.default import GermaniumTestCase
from germanium.tools import assert_equal

from is_core.auth_token.models import Token
from is_core.config import settings


class TokenTestCase(GermaniumTestCase):

    def test_should_return_proper_string_format_for_expiration(self):
        user = User.objects._create_user('test', 'test@test.cz', 'test', is_staff=False, is_superuser=False)
        expired_token = Token.objects.create(user=user, ip='127.0.0.1')
        Token.objects.filter(pk=expired_token.pk).update(
            last_access=timezone.now() - timedelta(seconds=settings.AUTH_MAX_TOKEN_AGE))
        expired_token = Token.objects.get(pk=expired_token.pk)
        assert_equal('00:00:00', Token.objects.get(pk=expired_token.pk).str_time_to_expiration)

        non_expired_token = Token.objects.create(user=user, ip='127.0.0.1')
        assert_equal('0:59:59', non_expired_token.str_time_to_expiration.split('.')[0])
