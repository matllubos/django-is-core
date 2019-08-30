from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView

from chamber.shortcuts import get_object_or_404

from is_core.exceptions import HTTPForbiddenResponseException
from is_core.site import get_model_core

from .models import ExportedFile


class DownloadExportedDataView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        exported_file = get_object_or_404(
            ExportedFile.objects.filter_active(), slug=kwargs.get('slug')
        )
        core = get_model_core(ExportedFile)

        if (core.permission.has_permission('read_all', self.request, self, obj=exported_file)
                or (core.permission.has_permission('read_own', self.request, self, obj=exported_file)
                    and exported_file.created_by == self.request.user)):
            exported_file.downloaded_by.add(self.request.user)
            return exported_file.file.url
        else:
            raise HTTPForbiddenResponseException


def static_pyston():
    return [
        url(
            r'^{}/(?P<slug>.+)?/'.format(getattr(settings, 'PYSTON_DOWNLOAD_EXPORT_URL', 'export')),
            login_required(DownloadExportedDataView.as_view()),
            name='pyston-download-export'
        )
    ]
