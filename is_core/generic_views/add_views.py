from django.utils.translation import ugettext_lazy as _

from is_core.auth.permissions import PermissionsSet, CoreCreateAllowed, CoreAllowed, DEFAULT_PERMISSION

from .form_views import DjangoCoreFormView


class DjangoAddFormView(DjangoCoreFormView):

    template_name = 'is_core/generic_views/add_form.html'
    form_template = 'is_core/forms/model_add_form.html'
    view_type = 'add'
    messages = {'success': _('The %(name)s "%(obj)s" was added successfully.'),
                'error': _('Please correct the error below.')}

    permission = PermissionsSet(
        get=CoreCreateAllowed(),
        post=CoreCreateAllowed(),
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    def get_view_title(self):
        return (self.title or
                self.model._ui_meta.add_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural})
