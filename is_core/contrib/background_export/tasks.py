import import_string

from django.conf import settings as django_settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.http.request import HttpRequest
from django.utils import translation
from django.db.transaction import atomic

from pyston.converters import get_converter_from_request
from pyston.serializer import get_serializer, get_resource_or_none
from pyston.utils import RFS
from pyston.utils.helpers import QuerysetIteratorHelper

from is_core.config import settings

from django_celery_extensions.task import string_to_obj

from security.task import LoggedTask

from celery import shared_task

from .models import ExportedFile

from .signals import export_success


def get_rest_request(user, rest_context):
    request = HttpRequest()
    request._rest_context = rest_context
    request.user = user
    request.kwargs = {}
    return request


class FileBackgroundExportGenerator:

    def __init__(self, model):
        self.model = model

    def generate(self, exported_file, request, queryset, requested_fieldset, serialization_format):
        converter = get_converter_from_request(request)
        converted_dict = get_serializer(queryset, request=request).serialize(
            QuerysetIteratorHelper(queryset), serialization_format, requested_fieldset=requested_fieldset,
            lazy=True, allow_tags=converter.allow_tags
        )
        django_file = exported_file.file
        try:
            django_file.open('wb')
            converter.encode_to_stream(
                django_file.file, converted_dict, resource=get_resource_or_none(request, queryset.model),
                request=request, requested_fields=requested_fieldset
            )
        finally:
            django_file.close()


class BackgroundSerializationTask(LoggedTask):

    abstract = True

    def get_exported_file(self, pk):
        return ExportedFile.objects.get(pk=pk)

    def on_success_task(self, task_run_log, args, kwargs, retval):
        super().on_success_task(task_run_log, args, kwargs, retval)
        exported_file = self.get_exported_file(args[0])
        export_success.send(sender=self.__class__, exported_file=exported_file)


@shared_task(base=BackgroundSerializationTask,
             name='background_export.serializer.serialization',
             time_limit=settings.BACKGROUND_EXPORT_TASK_TIME_LIMIT_MINUTES * 60,
             soft_time_limit=settings.BACKGROUND_EXPORT_TASK_SOFT_TIME_LIMIT_MINUTES * 60,
             bind=True)
@atomic
def background_serialization(self, exported_file_pk, rest_context, language, requested_fieldset, serialization_format,
                             filename, query):
    # Must be here, because handlers is not registered
    import_string(django_settings.ROOT_URLCONF)

    prev_language = translation.get_language()
    translation.activate(language)
    try:
        exported_file = self.get_exported_file(exported_file_pk)
        exported_file.file.save(filename, ContentFile(''))
        request = get_rest_request(exported_file.created_by, rest_context)
        if settings.BACKGROUND_EXPORT_TASK_UPDATE_REQUEST_FUNCTION:
            request = import_string(settings.BACKGROUND_EXPORT_TASK_UPDATE_REQUEST_FUNCTION)(request)
        query = string_to_obj(query)
        queryset = query.model.objects.all()
        queryset.query = query
        FileBackgroundExportGenerator(query.model).generate(
            exported_file, request, queryset, RFS.create_from_string(requested_fieldset), serialization_format
        )
    finally:
        translation.activate(prev_language)
