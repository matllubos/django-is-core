from __future__ import unicode_literals

from django.http import Http404

from is_core.generic_views.form_views import DefaultModelFormView


class BulkChangeFormView(DefaultModelFormView):
    form_template = 'views/bulk-change-view.html'
    is_ajax_form = False

    def dispatch(self, request, *args, **kwargs):
        if 'snippet' not in request.GET:
            raise Http404
        return super(BulkChangeFormView, self).dispatch(request, *args, **kwargs)

    def get_fields(self):
        return self.fields or (self.core.bulk_change_fields if hasattr(self.core, 'bulk_change_fields') else ())

    def get_fieldsets(self):
        return (self.fieldsets or
                (self.core.bulk_change_fieldsets if hasattr(self.core, 'bulk_change_fieldsets') else None))

    def get_readonly_fields(self):
        return ()
