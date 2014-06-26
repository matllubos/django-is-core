from __future__ import unicode_literals

from django.contrib import messages
from django.forms.models import modelform_factory, ModelForm
from django.http.response import HttpResponseRedirect
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.contrib.messages.api import get_messages, add_message
from django.contrib.messages import constants

from is_core.generic_views.exceptions import SaveObjectException
from is_core.generic_views import DefaultModelCoreViewMixin
from is_core.utils import flatten_fieldsets
from is_core.utils.forms import formset_has_file_field
from is_core.generic_views.mixins import ListParentMixin, GetCoreObjViewMixin
from is_core.generic_views.inlines.inline_form_views import InlineFormView


class DefaultFormView(DefaultModelCoreViewMixin, FormView):
    view_type = 'default'
    fieldsets = None
    form_template = 'forms/default_form.html'
    template_name = 'generic_views/default_form.html'
    messages = {'success': _('Object was saved successfully.'),
                'error': _('Please correct the error below.')}
    readonly_fields = None

    def render_to_response(self, context, **response_kwargs):
        if self.has_snippet():
            extra_content = response_kwargs['extra_content'] = response_kwargs.get('extra_content', {})
            extra_content_messages = extra_content['messages'] = {}
            for message in get_messages(self.request):
                extra_content_messages[message.tags] = force_text(message)
        return super(DefaultFormView, self).render_to_response(context, **response_kwargs)

    def get_success_url(self, obj):
        return ''

    def get_has_file_field(self, form, **kwargs):
        return formset_has_file_field(form)

    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())

        for field_name, field in form.fields.items():
            field = self.form_field(form, field_name, field)
        return form

    def get_form_action(self):
        return self.request.get_full_path()

    def get_readonly_fields(self):
        return self.readonly_fields or ()

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj)}
        return self.messages.get(type) % msg_dict

    def is_changed(self, form, **kwargs):
        return form.has_changed()

    def save_obj(self, obj, form, change):
        raise NotImplemented

    def form_valid(self, form, msg=None):
        obj = form.save(commit=False)

        change = obj.pk is not None

        try:
            self.save_obj(obj, form, change)
        except SaveObjectException as ex:
            return self.form_invalid(form, force_text(ex))
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        msg = msg or self.get_message('success', obj)

        messages.success(self.request, msg)
        return HttpResponseRedirect(self.get_success_url(obj))

    def form_invalid(self, form, msg=None, msg_level=constants.ERROR):
        msg = msg or self.get_message('error')
        add_message(self.request, msg_level, msg)
        return self.render_to_response(self.get_context_data(form=form))

    @property
    def is_ajax_form(self):
        return self.has_snippet()

    def get_form_class_names(self):
        class_names = ['-'.join((self.view_type, self.site_name,
                                 self.core.get_menu_group_pattern_name(), 'form',)).lower()]
        if self.is_ajax_form:
            class_names.append('ajax')
        return class_names

    def get_prefix(self):
        return '-'.join((self.view_type, self.site_name, self.core.get_menu_group_pattern_name())).lower()

    def get_context_data(self, form=None, **kwargs):
        context_data = super(DefaultFormView, self).get_context_data(form=form, **kwargs)
        context_data.update({
                                'view_type': self.view_type,
                                'fieldsets': self.generate_fieldsets(),
                                'form_template': self.form_template,
                                'form_class_names': self.get_form_class_names(),
                                'has_file_field': self.get_has_file_field(form, **kwargs),
                                'action': self.get_form_action(),
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

    def form_field(self, form, field_name, form_field):
        return form_field

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        is_valid = form.is_valid()
        is_changed = self.is_changed(form)

        if is_valid and is_changed:
            return self.form_valid(form)
        else:
            if is_valid and not is_changed:
                return self.form_invalid(form, msg=_('No changes have been submitted.'), msg_level=constants.INFO)
            return self.form_invalid(form)


class DefaultModelFormView(DefaultFormView):
    model = None
    exclude = None
    fieldset = None
    fields = None
    inline_views = None
    form_template = 'forms/model_default_form.html'

    def pre_save_obj(self, obj, form, change):
        pass

    def post_save_obj(self, obj, form, change):
        pass

    def form_field(self, form, field_name, form_field):
        form_field = super(DefaultModelFormView, self).form_field(form, field_name, form_field)
        placeholder = self.model._ui_meta.placeholders.get(field_name, None)
        if placeholder:
            form_field.widget.placeholder = placeholder
        return form_field

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj), 'name': force_text(obj._meta.verbose_name)}
        return self.messages.get(type) % msg_dict

    def get_exclude(self):
        return self.exclude or ()

    def generate_readonly_fields(self):
        if not self.has_post_permission(self.request, obj=self.get_obj()):
            return list(self.generate_form_class().base_fields.keys()) + list(self.get_readonly_fields())
        return self.get_readonly_fields()

    def get_inline_views(self):
        return self.inline_views

    def init_inline_views(self, instance):
        inline_views = SortedDict()
        for inline_view in self.get_inline_views():
            inline_views[inline_view.__name__] = inline_view(self.request, self, instance)
        return inline_views

    def _filter_inline_form_views(self, inline_views):
        inline_form_views = SortedDict()
        for name, view in inline_views.items():
            if isinstance(view, InlineFormView):
                inline_form_views[name] = view
        return inline_form_views

    def generate_fieldsets(self):
        fieldsets = self.get_fieldsets()

        if fieldsets is not None:
            return fieldsets
        else:
            fieldsets = [(None, {'fields': self.generate_fields() or
                                 list(self.generate_form_class().base_fields.keys())})]
            for inline_view in self.get_inline_views():
                if (issubclass(inline_view, InlineFormView) and (not inline_view.max_num or
                    inline_view.max_num > 1)):
                    title = inline_view.model._meta.verbose_name_plural
                else:
                    title = inline_view.model._meta.verbose_name
                fieldsets.append((title,
                                  {'inline_view': inline_view.__name__}))
            return list(fieldsets)

    def get_fields(self):
        return self.fields

    def generate_fields(self):
        fieldsets = self.get_fieldsets()

        if fieldsets is not None:
            return flatten_fieldsets(fieldsets)
        return self.get_fields()

    def get_form_class(self):
        return self.form_class or ModelForm

    def generate_form_class(self, fields=None, readonly_fields=()):
        form_class = self.get_form_class()
        exclude = list(self.get_exclude()) + list(readonly_fields)
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return modelform_factory(self.model, form=form_class, exclude=exclude, fields=fields,
                                 formfield_callback=self.formfield_for_dbfield)

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

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

    def has_save_button(self):
        return self.has_post_permission(self.request, obj=self.get_obj())

    def is_changed(self, form, inline_form_views, **kwargs):
        for inline_form_view_instance in inline_form_views.values():
            if inline_form_view_instance.formset.has_changed():
                return True
        return form.has_changed()

    def get(self, request, *args, **kwargs):
        fields = self.generate_fields()
        readonly_fields = self.generate_readonly_fields()

        form_class = self.generate_form_class(fields, readonly_fields)
        form = self.get_form(form_class)
        inline_views = self.init_inline_views(form.instance)
        inline_form_views = self._filter_inline_form_views(inline_views)
        return self.render_to_response(self.get_context_data(form=form, inline_views=inline_views,
                                                             inline_form_views=inline_form_views))

    def post(self, request, *args, **kwargs):
        fields = self.generate_fields()
        readonly_fields = self.generate_readonly_fields()

        form_class = self.generate_form_class(fields, readonly_fields)
        form = self.get_form(form_class)
        inline_form_views = SortedDict()
        inline_forms_is_valid = True

        inline_views = self.init_inline_views(form.instance)
        inline_form_views = self._filter_inline_form_views(inline_views)

        for inline_form_view in inline_form_views:
            inline_forms_is_valid = (inline_form_view.formset.is_valid()) \
                                        and inline_forms_is_valid

        is_valid = form.is_valid()
        is_changed = self.is_changed(form, inline_form_views=inline_form_views)

        if is_valid and inline_forms_is_valid and is_changed:
            return self.form_valid(form, inline_form_views)
        else:
            if is_valid and not is_changed:
                return self.form_invalid(form, inline_form_views, msg=_('No changes have been submitted.'),
                                         msg_level=constants.INFO)
            return self.form_invalid(form, inline_form_views)

    def get_obj(self, cached=True):
        return None

    def get_form_kwargs(self):
        kwargs = super(DefaultModelFormView, self).get_form_kwargs()
        kwargs['instance'] = self.get_obj()
        return kwargs

    def save_form(self, form, inline_form_views):
        obj = form.save(commit=False)
        change = obj.pk is not None

        self.pre_save_obj(obj, form, change)
        self.save_obj(obj, form, change)
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        for inline_form_view in inline_form_views.values():
            inline_form_view.form_valid(self.request)

        self.post_save_obj(obj, form, change)
        return obj

    def form_valid(self, form, inline_form_views, inline_views, msg=None):
        try:
            obj = self.save_form(form, inline_form_views)
        except SaveObjectException as ex:
            return self.form_invalid(form, inline_form_views, force_text(ex))

        msg = msg or self.get_message('success', obj)
        messages.success(self.request, msg)

        return HttpResponseRedirect(self.get_success_url(obj))

    def form_invalid(self, form, inline_form_views, inline_views, msg=None, msg_level=constants.ERROR):
        msg = msg or self.get_message('error')
        add_message(self.request, msg_level, msg)
        return self.render_to_response(self.get_context_data(form=form, inline_views=inline_views,
                                                             inline_form_views=inline_form_views))

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super(DefaultModelFormView, self).get_context_data(form=form,
                                                                          inline_form_views=inline_form_views, **kwargs)
        context_data.update({
                                'module_name': self.model._meta.module_name,
                                'cancel_url': self.get_cancel_url(),
                                'show_save_button': self.has_save_button()
                             })
        return context_data

    @classmethod
    def has_permission(cls, request, **kwargs):
        return True

    @classmethod
    def has_get_permission(cls, request, **kwargs):
        return cls.has_permission(request, **kwargs)

    @classmethod
    def has_post_permission(cls, request, **kwargs):
        return cls.has_permission(request, **kwargs)


class DefaultCoreModelFormView(ListParentMixin, DefaultModelFormView):

    show_save_and_continue = True

    def save_obj(self, obj, form, change):
        self.core.save_model(self.request, obj, form, change)

    def pre_save_obj(self, obj, form, change):
        self.core.pre_save_model(self.request, obj, form, change)

    def post_save_obj(self, obj, form, change):
        self.core.post_save_model(self.request, obj, form, change)

    def get_message(self, type, obj=None):
        msg_dict = {}
        if obj:
            msg_dict = {'obj': force_text(obj), 'name': force_text(self.core.verbose_name)}
        return self.messages.get(type) % msg_dict

    def get_exclude(self):
        return (self.exclude is not None and self.exclude or
                self.core.get_ui_form_exclude(self.request, self.get_obj(True)))

    def get_readonly_fields(self):
        return (self.readonly_fields is not None and self.readonly_fields or
                self.core.get_form_readonly_fields(self.request, self.get_obj(True)))

    def get_inline_views(self):
        return (self.inline_views is not None and self.inline_views or
                self.core.get_form_inline_views(self.request, self.get_obj(True)))

    def get_fieldsets(self):
        return (self.fieldset is not None and self.fieldset or
                self.core.get_form_fieldsets(self.request, self.get_obj(True)))

    def get_fields(self):
        return (self.fields is not None and self.fields or
                self.core.get_ui_form_fields(self.request, self.get_obj(True)))

    def get_form_class(self):
        return self.form_class or self.core.get_ui_form_class(self.request, self.get_obj(True))

    def get_cancel_url(self):
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request) \
                and not self.has_snippet():
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        return None

    def has_save_and_continue_button(self):
        return 'list' in self.core.ui_patterns and not self.has_snippet() \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request) \
                and self.show_save_and_continue

    def has_save_button(self):
        return self.view_type in self.core.ui_patterns and \
               self.core.ui_patterns.get(self.view_type).view.has_post_permission(self.request, obj=self.get_obj())

    def get_success_url(self, obj):
        menu_group = self.core.get_menu_group_pattern_name()
        info = self.site_name, menu_group
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').view.has_get_permission(self.request) \
                and 'save' in self.request.POST:
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        elif 'edit' in self.core.ui_patterns \
                and self.core.ui_patterns.get('edit').view.has_get_permission(self.request, obj=obj) \
                and 'save-and-continue' in self.request.POST:
            return self.core.ui_patterns.get('edit').get_url_string(self.request, kwargs={'pk': obj.pk})
        return ''

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super(DefaultCoreModelFormView, self).get_context_data(form=form,
                                                                              inline_form_views=inline_form_views,
                                                                              **kwargs)
        context_data.update({
                                'show_save_and_continue': self.has_save_and_continue_button()
                             })
        return context_data


class AddModelFormView(DefaultCoreModelFormView):
    template_name = 'generic_views/add_form.html'
    form_template = 'forms/model_add_form.html'
    view_type = 'add'
    messages = {'success': _('The %(name)s "%(obj)s" was added successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return self.model._ui_meta.add_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                       'verbose_name_plural': self.model._meta.verbose_name_plural}

    @classmethod
    def has_get_permission(cls, request, **kwargs):
        return cls.core.has_create_permission(request, **kwargs)

    @classmethod
    def has_post_permission(cls, request, **kwargs):
        return cls.core.has_create_permission(request, **kwargs)


class EditModelFormView(GetCoreObjViewMixin, DefaultCoreModelFormView):
    template_name = 'generic_views/edit_form.html'
    form_template = 'forms/model_edit_form.html'
    view_type = 'edit'
    messages = {'success': _('The %(name)s "%(obj)s" was changed successfully.'),
                'error': _('Please correct the error below.')}

    def get_title(self):
        return self.model._ui_meta.edit_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural,
                                                        'obj': self.get_obj(True)}

    def link(self, arguments=None, **kwargs):
        if arguments is None:
            arguments = (self.kwargs['pk'],)
        return super(EditModelFormView, self).link(arguments=arguments, **kwargs)

    @classmethod
    def has_get_permission(cls, request, **kwargs):
        return cls.core.has_ui_update_permission(request, **kwargs) \
                or cls.core.has_ui_read_permission(request, **kwargs)

    @classmethod
    def has_post_permission(cls, request, **kwargs):
        return cls.core.has_ui_update_permission(request, **kwargs)
