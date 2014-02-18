from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms.models import ModelMultipleChoiceField, modelform_factory, ModelForm
from django.http.response import HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404

from is_core.form.widgets import RelatedFieldWidgetWrapper
from is_core.generic_views.exceptions import SaveObjectException
from is_core.generic_views import DefaultCoreViewMixin
from is_core.utils import flatten_fieldsets
from is_core.response import JsonCreatedHttpResponse
from is_core.utils.forms import formset_has_file_field


class DefaultFormView(DefaultCoreViewMixin, FormView):
    view_type = 'default'
    fieldsets = None
    form_template = 'forms/default_form.html'
    template_name = 'generic_views/default_form.html'
    messages = {'success': _('Object was saved successfully.'),
                'error': _('Please correct the error below.')}
    readonly_fields = ()

    def __init__(self, core, site_name=None, menu_groups=None, model=None, form_class=None, readonly_fields=()):
        super(DefaultFormView, self).__init__(core, site_name, menu_groups, model)
        self.form_class = form_class or self.form_class
        self.readonly_fields = readonly_fields or self.readonly_fields

    def get_success_url(self, obj):
        return ''

    def get_has_file_field(self, form, **kwargs):
        return formset_has_file_field(form)

    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())

        for field in form.fields.values():
            field = self.form_field(field)
        return form

    def get_readonly_fields(self):
        return self.readonly_fields

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj)}
        return self.messages.get(type) % msg_dict

    def save_obj(self, obj, form):
        raise NotImplemented

    def is_popup(self):
        return 'popup' in self.request.GET

    def form_valid(self, form, msg=None):
        obj = form.save(commit=False)
        try:
            self.save_obj(obj, form)
        except SaveObjectException as ex:
            return self.form_invalid(form, force_text(ex))
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        msg = msg or self.get_message('success', obj)

        if self.is_popup():
            return JsonCreatedHttpResponse(content={'message': {'success': (msg,)}, 'id': obj.pk})

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
                                'fieldsets': self.generate_fieldsets(),
                                'form_template': self.form_template,
                                'form_name': '-'.join((self.view_type, self.site_name,
                                                       self.core.get_menu_group_pattern_name(), 'form',)).lower(),
                                'has_file_field': self.get_has_file_field(form, **kwargs)
                             })
        return context_data

    def generate_fieldsets(self):
        fieldsets = self.get_fieldsets()
        if fieldsets:
            return fieldsets
        else:
            return [(None, {'fields': list(self.get_form_class().base_fields.keys())})]

    def get_fieldsets(self):
        return self.fieldsets

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
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_snippet_names(self):
        if self.is_popup():
            return ('content',)

        return super(DefaultFormView, self).get_snippet_names()


class DefaultModelFormView(DefaultFormView):
    model = None
    exclude = ()
    fieldset = ()
    fields = None
    inline_form_views = ()
    form_template = 'forms/model_default_form.html'

    def __init__(self, core, site_name=None, menu_groups=None, model=None, form_class=None,
                 exclude=None, fieldset=None, fields=None, readonly_fields=None, inline_form_views=None):
        super(DefaultModelFormView, self).__init__(core, site_name, menu_groups, model, form_class,
                                                   readonly_fields)
        self.exclude = exclude or self.exclude
        self.fieldset = fieldset or self.fieldset
        self.fields = fields or self.fields
        self.inline_form_views = inline_form_views or self.inline_form_views

    def pre_save_obj(self, obj, change):
        pass

    def post_save_obj(self, obj, change):
        pass

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj), 'name': force_text(obj._meta.verbose_name)}
        return self.messages.get(type) % msg_dict

    def get_exclude(self):
        return self.exclude

    def generate_readonly_fields(self):
        if not self.has_post_permission(self.request, self.core):
            return list(self.generate_form_class().base_fields.keys()) + list(self.get_readonly_fields())
        return self.get_readonly_fields()

    def get_readonly_fields(self):
        return self.readonly_fields

    def get_inline_form_views(self):
        return self.inline_form_views

    def generate_fieldsets(self):
        fieldsets = self.get_fieldsets()

        if fieldsets:
            return fieldsets
        else:
            fieldsets = [(None, {'fields': self.generate_fields() or list(self.generate_form_class().base_fields.keys())})]
            for inline_form_view in self.get_inline_form_views():
                if not inline_form_view.max_num or inline_form_view.max_num > 1:
                    title = inline_form_view.model._meta.verbose_name_plural
                else:
                    title = inline_form_view.model._meta.verbose_name
                fieldsets.append((title,
                                  {'inline_form_view': inline_form_view.__name__}))
            return list(fieldsets)

    def get_fields(self):
        return self.fields

    def generate_fields(self):
        fieldsets = self.get_fieldsets()

        if fieldsets:
            return flatten_fieldsets(fieldsets)
        return self.fields

    def get_form_class(self):
        return self.form_class or ModelForm

    def generate_form_class(self, fields=None, readonly_fields=()):
        form_class = self.get_form_class()
        exclude = list(self.get_exclude()) + list(readonly_fields)

        if hasattr(self.form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return modelform_factory(self.model, form=form_class, exclude=exclude, fields=fields)

    def get_has_file_field(self, form, inline_form_views=(), **kwargs):
        if super(DefaultModelFormView, self).get_has_file_field(form, **kwargs):
            return True

        inline_form_views = inline_form_views and inline_form_views.values() or ()
        for inline_form_view in inline_form_views:
            if inline_form_view.get_has_file_field():
                return True

        return False

    def get_cancel_url(self):
        return None

    def get_success_url(self, obj):
        return ''

    def get(self, request, *args, **kwargs):
        fields = self.generate_fields()
        readonly_fields = self.generate_readonly_fields()

        form_class = self.generate_form_class(fields, readonly_fields)
        form = self.get_form(form_class)
        inline_form_views = SortedDict()
        for inline_form_view in self.get_inline_form_views():
            inline_form_views[inline_form_view.__name__] = inline_form_view(self.request, self.core, self.model,
                                                                            form.instance,
                                                                            not self.has_post_permission(self.request,
                                                                                                         self.core))
        return self.render_to_response(self.get_context_data(form=form, inline_form_views=inline_form_views))

    def post(self, request, *args, **kwargs):
        fields = self.generate_fields()
        readonly_fields = self.generate_readonly_fields()

        form_class = self.generate_form_class(fields, readonly_fields)
        form = self.get_form(form_class)
        inline_form_views = SortedDict()
        inline_forms_is_valid = True
        for inline_form_view in self.get_inline_form_views():
            inline_form_view_instance = inline_form_view(self.request, self.core, self.model,
                                                         form.instance, not self.has_post_permission(self.request,
                                                                                                     self.core))
            inline_forms_is_valid = (inline_form_view_instance.formset.is_valid()) \
                                        and inline_forms_is_valid
            inline_form_views[inline_form_view.__name__] = inline_form_view_instance

        if form.is_valid() and inline_forms_is_valid:
            return self.form_valid(form, inline_form_views)
        else:
            return self.form_invalid(form, inline_form_views)

    def get_obj(self, cached=True):
        return None

    def get_form_kwargs(self):
        kwargs = super(DefaultModelFormView, self).get_form_kwargs()
        kwargs['instance'] = self.get_obj()
        return kwargs

    def form_valid(self, form, inline_form_views, msg=None):
        try:
            obj = form.save(commit=False)
            change = obj.pk is not None

            self.pre_save_obj(obj, change)
            self.save_obj(obj, form)
            if hasattr(form, 'save_m2m'):
                form.save_m2m()

            for inline_form_view in inline_form_views.values():
                inline_form_view.form_valid(self.request)

            self.post_save_obj(obj, change)
        except SaveObjectException as ex:
            return self.form_invalid(form, inline_form_views, force_text(ex))

        msg = msg or self.get_message('success', obj)
        if self.is_popup():
            return JsonCreatedHttpResponse(content={'message': {'success': (msg,)}, 'id': obj.pk})

        messages.success(self.request, msg)

        return HttpResponseRedirect(self.get_success_url(obj))

    def form_invalid(self, form, inline_form_views, msg=None):
        msg = msg or self.get_message('error')
        messages.error(self.request, msg)
        return self.render_to_response(self.get_context_data(form=form, inline_form_views=inline_form_views))

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super(DefaultModelFormView, self).get_context_data(form=form,
                                                                          inline_form_views=inline_form_views, **kwargs)
        context_data.update({
                                'module_name': self.model._meta.module_name,
                                'cancel_url': self.get_cancel_url(),
                             })
        return context_data

    @classmethod
    def has_get_permission(cls, request, core, **kwargs):
        return True

    @classmethod
    def has_post_permission(cls, request, core, **kwargs):
        return True


class DefaultCoreModelFormView(DefaultModelFormView):

    def pre_save_obj(self, obj, change):
        self.core.post_save_model(self.request, obj, change)

    def post_save_obj(self, obj, change):
        self.core.post_save_model(self.request, obj, change)

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj), 'name': force_text(self.core.verbose_name)}
        return self.messages.get(type) % msg_dict

    def get_exclude(self):
        return self.exclude or self.core.get_exclude(self.request, self.get_obj(True))

    def get_readonly_fields(self):
        return self.readonly_fields or self.core.get_readonly_fields(self.request, self.get_obj(True))

    def get_inline_form_views(self):
        return self.inline_form_views or self.core.get_inline_form_views(self.request, self.get_obj(True))

    def get_fieldsets(self):
        return self.fieldset or self.core.get_fieldsets(self.request, self.get_obj(True))

    def get_fields(self):
        return self.fields or self.core.get_fields(self.request, self.get_obj(True))

    def get_form_class(self, fields=None, readonly_fields=()):
        return self.form_class or self.core.get_form_class(self.request, self.get_obj(True))

    def get_cancel_url(self):
        if 'list' in self.core.view_classes and not self.is_popup():
            info = self.site_name, self.core.get_menu_group_pattern_name()
            return reverse('%s:list-%s' % info)
        return None

    def get_success_url(self, obj):
        info = self.site_name, self.core.get_menu_group_pattern_name()
        if 'list' in self.core.view_classes and 'save' in self.request.POST:
            return reverse('%s:list-%s' % info)
        elif 'edit' in self.core.view_classes and 'save-and-continue' in self.request.POST:
            return reverse('%s:edit-%s' % info, args=(obj.pk,))
        return ''

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super(DefaultCoreModelFormView, self).get_context_data(form=form,
                                                                              inline_form_views=inline_form_views,
                                                                              **kwargs)
        context_data.update({
                                'show_save_and_continue': 'list' in self.core.view_classes and not self.is_popup()
                             })
        return context_data


class AddModelFormView(DefaultCoreModelFormView):
    template_name = 'generic_views/add_form.html'
    form_template = 'forms/model_add_form.html'
    view_type = 'add'
    messages = {'success': _('The %(name)s "%(obj)s" was added successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return _('Add %s') % self.core.verbose_name

    def save_obj(self, obj, form):
        self.core.save_model(self.request, obj, False)

    @classmethod
    def has_get_permission(cls, request, core, **kwargs):
        return core.has_create_permission(request)

    @classmethod
    def has_post_permission(cls, request, core, **kwargs):
        return core.has_create_permission(request)


class EditModelFormView(DefaultCoreModelFormView):
    template_name = 'generic_views/edit_form.html'
    form_template = 'forms/model_edit_form.html'
    view_type = 'edit'
    messages = {'success': _('The %(name)s "%(obj)s" was changed successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return _('Edit %s') % self.core.verbose_name

    def save_obj(self, obj, form):
        self.core.save_model(self.request, obj, True)

    def get_obj_filters(self):
        filters = {'pk': self.kwargs.get('pk')}
        return filters

    _obj = None
    def get_obj(self, cached=True):
        if cached and self._obj:
            return self._obj
        obj = get_object_or_404(self.core.get_queryset(self.request), **self.get_obj_filters())
        if cached and not self._obj:
            self._obj = obj
        return obj

    def link(self, arguments=None, **kwargs):
        if arguments is None:
            arguments = (self.kwargs['pk'],)
        return super(EditModelFormView, self).link(arguments=arguments, **kwargs)

    @classmethod
    def has_get_permission(cls, request, core, **kwargs):
        return core.has_update_permission(request) or core.has_read_permission(request)

    @classmethod
    def has_post_permission(cls, request, core, **kwargs):
        return core.has_update_permission(request)
