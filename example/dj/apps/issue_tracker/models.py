from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Issue(models.Model):

    name = models.CharField(verbose_name=_('Name'), max_length=100, null=False, blank=False)
    watched_by = models.ManyToManyField(AUTH_USER_MODEL, verbose_name=_('Watched by'), null=True, blank=True,
                                        related_name='watching_issues')
    created_by = models.ForeignKey(AUTH_USER_MODEL, verbose_name=_('Created by'), null=False, blank=False,
                                   related_name='created_issues')

    solver = models.OneToOneField(AUTH_USER_MODEL, verbose_name=_('Solver'), null=True, blank=True,
                                  related_name='solving_issue')
    leader = models.OneToOneField(AUTH_USER_MODEL, verbose_name=_('Leader'), null=False, blank=False,
                                  related_name='leading_issue')

    def watched_by_string(self):
        return ', '.join(self.watched_by.all())
    watched_by_string.order_by = 'watched_by'

    def __unicode__(self):
        return 'issue: %s' % self.name
