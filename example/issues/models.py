from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class Issue(models.Model):
    title = models.CharField(_('Subject'), max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, verbose_name=_('User'))

    def __unicode__(self):
        return self.title