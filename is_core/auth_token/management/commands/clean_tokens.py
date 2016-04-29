from __future__ import unicode_literals

import logging

from datetime import timedelta

from django.utils import timezone

from is_core import config
from is_core.auth_token.models import Token

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    logger = logging.getLogger('is-core')

    def handle_noargs(self, **options):
        removing_tokens_qs = Token.objects.filter(
            last_access__lt=timezone.now() - timedelta(seconds=config.IS_CORE_AUTH_MAX_TOKEN_AGE)
        )
        self.logger.info('Removing %s tokens' % removing_tokens_qs.count())
        removing_tokens_qs.delete()
