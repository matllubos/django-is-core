from __future__ import unicode_literals

from datetime import timedelta

from six import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone

from germanium.testcase import GermaniumTestCase
from germanium.tools import assert_equal, assert_false, assert_true

from is_core import config
from is_core.auth_token.models import Token


class CleanTokensCommandTestCase(GermaniumTestCase):

    def test_clean_tokens_remove_only_old_tokens(self):
        user = User.objects._create_user('test', 'test@test.cz', 'test', is_staff=False, is_superuser=False)
        expired_tokens = [Token.objects.create(user=user, ip='127.0.0.1') for _ in range(10)]
        not_expired_tokens = [Token.objects.create(user=user, ip='127.0.0.1') for _ in
                              range(config.IS_CORE_AUTH_COUNT_USER_PRESERVED_TOKENS - 5)]
        Token.objects.filter(pk__in=[token.pk for token in expired_tokens]).update(
            last_access=timezone.now() - timedelta(seconds=config.IS_CORE_AUTH_MAX_TOKEN_AGE))
        call_command('clean_tokens', stdout=StringIO(), stderr=StringIO())
        assert_equal(Token.objects.filter(pk__in=[token.pk for token in not_expired_tokens]).count(),
                     config.IS_CORE_AUTH_COUNT_USER_PRESERVED_TOKENS - 5)
        assert_equal(Token.objects.filter(pk__in=[token.pk for token in expired_tokens]).count(), 5)
