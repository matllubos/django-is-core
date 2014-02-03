from django.views.generic.base import TemplateView
from django.contrib import auth

from utils import query_string_from_dict
from django.forms.models import ModelForm, inlineformset_factory
from is_core.form import form_to_readonly

class LogoutView(TemplateView):
    template_name = "registration/logout.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            auth.logout(self.request)
        return super(LogoutView, self).get(*args, **kwargs)


class DefaultViewMixin(object):

    def __init__(self, is_core, site_name=None, menu_group=None, menu_subgroup=None, model=None):
        self.is_core = is_core
        self.site_name = site_name or is_core.site_name
        self.menu_group = site_name or is_core.menu_group
        self.menu_subgroup = site_name or is_core.menu_subgroup
        self.model = site_name or is_core.model
        super(DefaultViewMixin, self).__init__()

    def get_title(self):
        if self.model:
            return self.model._meta.verbose_name
        return None

    def get_context_data(self, **kwargs):
        context_data = super(DefaultViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
                                'site_name': self.site_name,
                                'active_menu_group': self.menu_group,
                                'active_menu_subgroup': self.menu_subgroup,
                                'title': self.get_title()
                              }
        extra_context_data.update(context_data)
        return extra_context_data


class TableView(DefaultViewMixin, TemplateView):
    list_display = ()
    template_name = 'generic_views/table.html'
    view_type = 'list'
    model = None

    def get_title(self):
        return _('List %s') % self.model._meta.verbose_name

    def get_list_display(self):
        return self.list_display

    def get_header(self, field):
        return TableView.Header(self.model._meta.get_field(field).verbose_name, True)

    def get_headers(self):
        headers = []
        for field in self.get_list_display():
            headers.append(self.get_header(field))
        return headers

    def gel_api_url_name(self):
        return self.is_core.gel_api_url_name()

    def get_query_string_filter(self):
        default_list_filter = self.is_core.get_default_list_filter(self.request)

        filter_vals = default_list_filter.get('filter', {}).copy()
        exclude_vals = default_list_filter.get('exclude', {}).copy()

        for key, val in exclude_vals.items():
            filter_vals[key + '__not'] = val

        return query_string_from_dict(filter_vals)

    def get_context_data(self, **kwargs):
        context_data = super(TableView, self).get_context_data(**kwargs)
        info = self.site_name, self.menu_group, self.menu_subgroup
        context_data.update({
                                'headers': self.get_headers(),
                                'api_url_name': self.gel_api_url_name(),
                                'add_url_name': '%s:add-%s-%s' % info,
                                'edit_url_name': '%s:edit-%s-%s' % info,
                                'module_name': self.menu_subgroup,
                                'verbose_name':  self.model._meta.verbose_name,
                                'view_type': self.view_type,
                                'list_display': self.get_list_display(),
                                'list_action': self.persoo_view.get_list_actions(self.request.user,
                                                                                 self.request.account_pk),
                                'query_string_filter': self.get_query_string_filter()
                            })
        return context_data

    class Header(object):

        def __init__(self, text, sortable):
            self.text = text
            self.sortable = sortable

        def __unicode__(self):
            return self.text

        def __str__(self):
            return self.text


class InlineFormView(object):
    form_class = ModelForm
    model = None
    fk_name = None
    template_name = None
    extra = 0
    exclude = None
    can_add = True
    can_delete = True

    def __init__(self, request, persoo_view, parent_model, instance, readonly):
        self.request = request
        self.parent_model = parent_model
        self.readonly = readonly
        self.persoo_view = persoo_view
        self.parent = instance
        self.formset = self.get_formset(instance, self.request.POST)

    def get_exclude(self):
        return self.exclude

    def get_extra(self):
        return self.extra

    def get_formset_factory(self):
        extra = not self.is_readonly() and self.get_extra() or 0
        return inlineformset_factory(self.parent_model, self.model, form=self.form_class,
                                     fk_name=self.fk_name, extra=extra, formset=BaseInlineFormSet,
                                     can_delete=self.get_can_delete(), exclude=self.get_exclude())

    def get_queryset(self):
        return self.model.objects.all()

    def get_can_delete(self):
        return self.can_delete and not self.is_readonly()

    def get_can_add(self):
        return self.can_add and not self.is_readonly()

    def get_formset(self, instance, data):
        if data and not self.is_readonly():
            formset = self.get_formset_factory()(data=data, instance=instance, queryset=self.get_queryset())
        else:
            formset = self.get_formset_factory()(instance=instance, queryset=self.get_queryset())

        formset.can_add = self.get_can_add()
        formset.can_delete = self.get_can_delete()
        formset.readonly = False

        if self.is_readonly():
            formset.readonly = True
            for form in formset:
                form_to_readonly(form)
        return formset

    def is_readonly(self):
        return self.readonly

    def get_name(self):
        return self.model.__name__

    def form_valid(self, request):
        if not self.is_readonly():
            instances = self.formset.save(commit=False)
            for obj in instances:
                self.save_model(request, obj)
            for obj in self.formset.deleted_objects:
                self.delete_model(request, obj)

    def save_model(self, request, obj):
        obj.save()

    def delete_model(self, request, obj):
        obj.delete()
