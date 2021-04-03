from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from is_core.utils.decorators import relation


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Issue(models.Model):

    name = models.CharField(verbose_name='Name', max_length=100, null=False, blank=False)
    watched_by = models.ManyToManyField(AUTH_USER_MODEL, verbose_name='Watched by', blank=True,
                                        related_name='watching_issues')
    created_by = models.ForeignKey(AUTH_USER_MODEL, verbose_name='Created by', null=False, blank=False,
                                   related_name='created_issues', on_delete=models.CASCADE)

    solver = models.OneToOneField(AUTH_USER_MODEL, verbose_name='Solver', null=True, blank=True,
                                  related_name='solving_issue', on_delete=models.CASCADE)
    leader = models.OneToOneField(AUTH_USER_MODEL, verbose_name='Leader', null=False, blank=False,
                                  related_name='leading_issue', on_delete=models.CASCADE)

    related_object_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('related_object_ct', 'related_object_id')

    is_issue = True


    def watched_by_string(self):
        return ', '.join(str(user) for user in self.watched_by.all())
    watched_by_string.order_by = 'watched_by'

    @property
    @relation(AUTH_USER_MODEL)
    def watched_by_method(self):
        return list(self.watched_by.all())

    def __unicode__(self):
        return 'issue: %s' % self.name
