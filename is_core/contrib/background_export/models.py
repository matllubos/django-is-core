import os
from datetime import timedelta
from uuid import uuid4 as uuid

import import_string

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from is_core.config import settings as is_core_settings
from is_core.utils.decorators import short_description

from chamber.models import SmartModel
from chamber.models.fields import FileField


if 'security' not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured('Missing library security, please install it.')


def generate_filename(instance, filename):
    return os.path.join('exports', instance.slug, filename)


class ExportedFileManager(models.QuerySet):

    def filter_expired(self):
        return self.filter_active(
            created_at__lt=timezone.now() - timedelta(days=is_core_settings.BACKGROUND_EXPORT_EXPIRATION_DAYS)
        )

    def filter_active(self, *args, **kwargs):
        return self.exclude(file='').filter(*args, **kwargs)


storage = import_string(is_core_settings.BACKGROUND_EXPORT_STORAGE_CLASS)()


def generate_slug():
    return uuid().hex


class ExportedFile(SmartModel):

    objects = ExportedFileManager.as_manager()

    slug = models.SlugField(
        verbose_name=_('slug'),
        null=False,
        blank=False,
        primary_key=True,
        max_length=32,
        default=generate_slug
    )
    file = FileField(
        verbose_name=_('file'),
        null=True,
        blank=True,
        upload_to=generate_filename,
        max_upload_size=100,
        storage=storage
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('created by'),
        null=False,
        blank=False,
        related_name='created_exported_files',
        on_delete=models.PROTECT,
    )
    downloaded_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('downloaded by'),
        blank=True,
        related_name='downloaded_exported_files'
    )
    content_type = models.ForeignKey(
        ContentType,
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )

    @property
    def download_url(self):
        from security.enums import CeleryTaskLogState

        return (
            resolve_url('pyston-download-export', slug=self.slug)
            if self.file else ''
        )

    @short_description(_('download'))
    def download_link(self):
        return (
            format_html('<a href="{}">{}</a>', self.download_url, os.path.basename(self.file.name))
            if self.download_url else ''
        )

    def generate_slug(self):
        self.slug = uuid().hex

    def clean_slug(self):
        if not self.slug:
            self.generate_slug()

    @short_description(_('expiration'))
    def expiration(self):
        return (
            self.created_at + timedelta(days=is_core_settings.BACKGROUND_EXPORT_EXPIRATION_DAYS)
            if self.created_at else None
        )

    def __str__(self):
        return '#{}'.format(self.pk)

    class Meta:
        verbose_name = _('exported file')
        verbose_name_plural = _('exported files')
        ordering = ('-created_at',)
