from django.db.models.query import QuerySet
from django.shortcuts import render
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.translation import ugettext

from is_core.config import settings
from is_core.rest.resource import RESTResource, UIRESTModelResource

from security.tasks import obj_to_string

from .tasks import background_serialization


class ErrorResponseData(dict):

    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['messages'] = {'error': force_text(msg)}


class CeleryResourceMixin:

    def _get_error_response_data(self, message):
        return {
            'messages': {'error': force_text(message)}
        }

    def _get_too_large_response_data(self, http_headers):
        return ErrorResponseData(
            ugettext('Too much data, please use filter or pagination to reduce its amount.')
        ), http_headers, 430, False

    def _get_no_background_permissions_response_data(self, http_headers):
        return ErrorResponseData(
            ugettext('User doesn\'t have permissions to export')
        ), http_headers, 403, False

    def _serialize_data_in_background(self, result):
        background_serialization.apply_async_on_commit(
            args=(
                self.request.user.pk,
                self.request._rest_context,
                translation.get_language(),
                force_text(self._get_requested_fieldset(result)),
                self._get_serialization_format(),
                self._get_filename(),
                obj_to_string(result.query),
            ),
            queue=settings.BACKGROUND_EXPORT_TASK_QUEUE
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

    def _is_excluded_serialization_limit(self, result):
        return (
            'background_serialization' not in self.request._rest_context and
            isinstance(result, QuerySet) and
            result.count() > settings.BACKGROUND_EXPORT_SERIALIZATION_LIMIT
        )

    def _get_response_data(self):
        result, http_headers, status_code, fieldset = super()._get_response_data()
        if self._is_excluded_serialization_limit(result):
            return self._get_too_large_response_data(http_headers)
        elif 'background_serialization' in self.request._rest_context:
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


class CeleryRESTModelResource(CeleryResourceMixin, UIRESTModelResource):
    pass


class CeleryRESTResource(CeleryResourceMixin, RESTResource):
    pass
