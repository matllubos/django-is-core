from django.db import models
from django.utils.translation import ugettext_lazy as _


class Issue(models.Model):
    title = models.CharField(_('Subject'), max_length=100, null=False, blank=False)