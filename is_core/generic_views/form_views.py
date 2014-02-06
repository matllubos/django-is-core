from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import ModelMultipleChoiceField, modelform_factory
from django.http.response import HttpResponseRedirect, Http404
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from is_core.form.widgets import RelatedFieldWidgetWrapper
from is_core.form import form_to_readonly
from is_core.generic_views.exceptions import SaveObjectException
from is_core.generic_views import DefaultCoreViewMixin
from is_core.utils.models import get_object_or_none


class DefaultFormView(DefaultCoreViewMixin, FormView):
    view_type = None
    fieldsets = None
    form_template = 'forms/default_form.html'
    template_name = 'generic_views/default_form.html'
    allowed_snippets = ('form-fields',)
    messages = {'success': _('Object was saved successfully.'),
                'error': _('Please correct the error below.')}

    def __init__(self, core, site_name=None, menu_group=None, menu_subgroup=None, model=None, form_class=None):
        super(DefaultFormView, self).__init__(core, site_name, menu_group, menu_subgroup, model)
        self.form_class = self.form_class or form_class or core.form_class

    def get_success_url(self, obj):
        return ''

    def is_readonly(self):
        return False

    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())

        if self.is_readonly():
            form_to_readonly(form)

        for field in form.fields.values():
            field = self.form_field(field)
        return form

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj)}
        return self.messages.get(type) % msg_dict

    def save_obj(self, obj, form):
        raise NotImplemented

    def form_valid(self, form, msg=None):
        if not self.is_readonly():
            obj = form.save(commit=False)
            try:
                self.save_obj(obj, form)
            except SaveObjectException as ex:
                return self.form_invalid(form, force_text(ex))
            if hasattr(form, 'save_m2m'):
                form.save_m2m()
        else:
            obj = self.get_obj()

        msg = msg or self.get_message('success', obj)
        messages.success(self.request, msg)
        return HttpResponseRedirect(self.get_success_url(obj))

    def form_invalid(self, form, msg=None):
        msg = msg or self.get_message('error')
        messages.error(self.request, msg)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, form=None, **kwargs):
        context_data = super(DefaultFormView, self).get_context_data(form=form, **kwargs)
        context_data.update({
                                'view_type': self.view_type,
                                'fieldsets': self.get_fieldsets(form),
                                'form_template': self.form_template,
                                'form_name': '-'.join((self.view_type, self.site_name, self.menu_group,
                                                       self.menu_subgroup, 'form')).lower()
                             })
        return context_data

    def get_fieldsets(self, form):
        if self.fieldsets:
            return self.fieldsets
        else:
            return [(None, {'fields': form.fields.keys()})]

    def get_initial(self):
        initial = super(DefaultFormView, self).get_initial()
        initial['_user'] = self.request.user
        return initial

    def form_field(self, form_field):
        if isinstance(form_field, ModelMultipleChoiceField):
            form_field.widget = RelatedFieldWidgetWrapper(form_field.widget, form_field.queryset.model, self.site_name)
        return form_field

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if (self.is_readonly() or form.is_valid()):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(DefaultFormView, self).get_form_kwargs()
        if self.request.method in ('POST', 'PUT') and self.is_readonly():
            del kwargs['data']
            del kwargs['files']
        return kwargs


class DefaultModelFormView(DefaultFormView):
    model = None
    exclude = []
    inline_form_views = ()
    form_template = 'forms/model_default_form.html'

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj), 'name': force_text(obj._meta.verbose_name)}
        return self.messages.get(type) % msg_dict

    def get_exclude(self):
        return list(self.exclude)

    def get_form_class(self):
        form_class = self.form_class or self.core.get_form_class(self.request, obj=self.get_obj())
        exclude = self.get_exclude()
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return modelform_factory(self.model, form=form_class, exclude=exclude)

    def get_context_data(self, form=None, **kwargs):
        context_data = super(DefaultModelFormView, self).get_context_data(form=form, **kwargs)
        context_data.update({
                                'module_name': self.model._meta.module_name,
                                'cancel_url': self.get_cancel_url(),
                                'show_save_and_continue': 'list' in self.core.allowed_views
                             })
        return context_data

    def get_cancel_url(self):
        if 'list' in self.core.allowed_views:
            info = self.site_name, self.menu_group, self.menu_subgroup
            return reverse('%s:list-%s-%s' % info)
        return None

    def get_inline_form_views(self):
        return self.core.get_inline_form_views(self.request, self.get_obj())

    def get_success_url(self, obj):
        info = self.site_name, self.menu_group, self.menu_subgroup
        if 'list' in self.core.allowed_views and 'save' in self.request.POST:
            return reverse('%s:list-%s-%s' % info)
        elif 'edit' in self.core.allowed_views and 'save-and-continue' in self.request.POST:
            return reverse('%s:edit-%s-%s' % info, args=(obj.pk,))
        return ''

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        inline_form_views = SortedDict()
        for inline_form_view in self.get_inline_form_views():
            inline_form_views[inline_form_view.__name__] = inline_form_view(self.request, self.core, self.model,
                                                                            form.instance, self.is_readonly())
        return self.render_to_response(self.get_context_data(form=form, inline_form_views=inline_form_views))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        inline_form_views = SortedDict()
        inline_forms_is_valid = True
        for inline_form_view in self.get_inline_form_views():
            inline_form_view_instance = inline_form_view(self.request, self.core, self.model,
                                                         form.instance, self.is_readonly())
            inline_forms_is_valid = (inline_form_view_instance.is_readonly() \
                                        or inline_form_view_instance.formset.is_valid()) \
                                        and inline_forms_is_valid
            inline_form_views[inline_form_view.__name__] = inline_form_view_instance

        if (self.is_readonly() or form.is_valid()) and inline_forms_is_valid:
            return self.form_valid(form, inline_form_views)
        else:
            return self.form_invalid(form, inline_form_views)

    def get_obj(self):
        return None

    def get_form_kwargs(self):
        kwargs = super(DefaultModelFormView, self).get_form_kwargs()
        kwargs['instance'] = self.get_obj()
        return kwargs

    def form_valid(self, form, inline_form_views, msg=None):
        try:
            if not self.is_readonly():
                obj = form.save(commit=False)
                self.save_obj(obj, form)
                if hasattr(form, 'save_m2m'):
                    form.save_m2m()
            else:
                obj = self.get_obj()

            for inline_form_view in inline_form_views.values():
                inline_form_view.form_valid(self.request)

        except SaveObjectException as ex:
            return self.form_invalid(form, inline_form_views, force_text(ex))

        msg = msg or self.get_message('success', obj)

        messages.success(self.request, msg)

        return HttpResponseRedirect(self.get_success_url(obj))

    def form_invalid(self, form, inline_form_views, msg=None):
        msg = msg or self.get_message('error')
        messages.error(self.request, msg)
        return self.render_to_response(self.get_context_data(form=form, inline_form_views=inline_form_views))

    def get_fieldsets(self, form):
        core_fieldsets = None
        if self.core:
            core_fieldsets = self.core.get_fieldsets(form)

        if self.fieldsets:
            return self.fieldsets
        elif core_fieldsets:
            return core_fieldsets
        else:
            fieldsets = [(None, {'fields': form.fields.keys()})]
            for inline_form_view in self.get_inline_form_views():
                fieldsets.append((inline_form_view.model._meta.verbose_name_plural,
                                  {'inline_form_view': inline_form_view.__name__}))
            return list(fieldsets)


class AddModelFormView(DefaultModelFormView):
    template_name = 'generic_views/add_form.html'
    view_type = 'add'
    messages = {'success': _('The %(name)s "%(obj)s" was added successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return _('Add %s') % self.model._meta.verbose_name

    def save_obj(self, obj, form):
        self.core.save_model(self.request, obj, False)


class EditModelFormView(DefaultModelFormView):
    template_name = 'generic_views/add_form.html'
    view_type = 'edit'
    messages = {'success': _('The %(name)s "%(obj)s" was changed successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return _('Edit %s') % self.model._meta.verbose_name

    def save_obj(self, obj, form):
        self.core.save_model(self.request, obj, True)

    def get_obj_filters(self):
        filters = {'pk': self.kwargs.get('pk')}
        return filters

    def get_obj(self):
        obj = get_object_or_none(self.model, **self.get_obj_filters())
        if not obj:
            raise Http404
        return obj

    def link(self, arguments=None, **kwargs):
        if arguments is None:
            arguments = (self.kwargs['pk'],)
        return super(EditModelFormView, self).link(arguments=arguments, **kwargs)

