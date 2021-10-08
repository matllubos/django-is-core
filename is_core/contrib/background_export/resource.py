from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.translation import ugettext

from is_core.config import settings
from is_core.rest.resource import RESTResource, RESTModelResource

from django_celery_extensions.task import obj_to_string

from .models import ExportedFile
from .tasks import background_serialization


class ErrorResponseData(dict):

    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['messages'] = {'error': force_text(msg)}


def apply_background_export(user, queryset, rest_context, fieldset, serialization_format, filename):
    exported_file = ExportedFile.objects.create(
        created_by=user,
        content_type=ContentType.objects.get_for_model(queryset.model)
    )

    background_serialization.apply_async_on_commit(
        args=(
            exported_file.pk,
            rest_context,
            translation.get_language(),
            fieldset,
            serialization_format,
            filename,
            obj_to_string(queryset.query),
        ),
        related_objects=[exported_file]
    )


class CeleryResourceMixin:

    def _get_error_response_data(self, message):
        return {
            'messages': {'error': force_text(message)}
        }

    def _get_no_background_permissions_response_data(self, http_headers):
        return ErrorResponseData(
            ugettext('User doesn\'t have permissions to export')
        ), http_headers, 403, False

    def _serialize_data_in_background(self, result):
        apply_background_export(
            self.request.user,
            result,
            self.request._rest_context,
            force_text(self._get_requested_fieldset(result)),
            self._get_serialization_format(),
            self._get_filename(),
        )

    def _get_filename(self):
        parts = super()._get_filename().rsplit(sep='.', maxsplit=1)
        return ('{}{}.{}'.format(parts[0], '_DUVERNE', parts[1]) if len(parts) == 2 else
                '{}{}'.format(super()._get_filename(), '_DUVERNE')
        )

    def _get_background_serialization_response_data(self, result, http_headers):
        if not self.permission.has_permission('export', self.request, self):
            return self._get_no_background_permissions_response_data(http_headers)
        else:
            self._serialize_data_in_background(result)
            response = render(self.request, 'is_core/background_serialization.html')
            return response, response['Content-Type'], 200, False

    def _get_paginator(self):
        # For background serialization paginator is not used
        return None if 'background_serialization' in self.request._rest_context else self.paginator

    def _get_response_data(self):
        result, http_headers, status_code, fieldset = super()._get_response_data()
        if 'background_serialization' in self.request._rest_context:
            return self._get_background_serialization_response_data(result, http_headers)
        else:
            return result, http_headers, status_code, fieldset

    def _get_headers_queryset_context_mapping(self):
        context_mapping = super()._get_headers_queryset_context_mapping()
        context_mapping['background_serialization'] = ('BACKGROUND_SERIALIZATION', '_background_serialization')
        return context_mapping

    def _get_name(self):
        obj = self._get_obj_or_none(pk=self.kwargs.get('pk'))
        return force_text(obj).replace(' ', '-') if obj else super()._get_name()


class CeleryRESTModelResource(CeleryResourceMixin, RESTModelResource):
    pass


class CeleryRESTResource(CeleryResourceMixin, RESTResource):
    pass
