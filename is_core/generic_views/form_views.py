from __future__ import unicode_literals

from collections import OrderedDict

import django

from django.forms.models import ModelForm
from django.http.response import HttpResponseRedirect, Http404
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.contrib.messages.api import get_messages, add_message
from django.contrib.messages import constants
from django.db import transaction

from chamber.shortcuts import get_object_or_none
from chamber.utils.forms import formset_has_file_field
from chamber.exceptions import PersistenceException

from is_core.generic_views import DefaultModelCoreViewMixin
from is_core.utils import flatten_fieldsets, get_readonly_field_data
from is_core.generic_views.mixins import ListParentMixin, GetCoreObjViewMixin
from is_core.generic_views.inlines.inline_form_views import InlineFormView
from is_core.response import JsonHttpResponse
from is_core.forms.models import smartmodelform_factory
from is_core.forms.fields import SmartReadonlyField


class DefaultFormView(DefaultModelCoreViewMixin, FormView):
    view_type = 'default'
    fieldsets = None
    form_template = 'forms/default_form.html'
    template_name = 'generic_views/default_form.html'
    messages = {'success': _('Object was saved successfully.'),
                'error': _('Please correct the error below.')}
    readonly_fields = None

    save_button_label = _('Save')
    save_button_title = ''

    cancel_button_label = _('Back')
    cancel_button_title = ''

    atomic_save_form = True

    def get_success_url(self, obj):
        """
        URL string for redirect after saving
        """

        return ''

    def get_has_file_field(self, form, **kwargs):
        return formset_has_file_field(form)

    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())
        form.readonly = not self.has_post_permission()

        for field_name, field in form.fields.items():
            field = self.form_field(form, field_name, field)

        return form

    def get_form_action(self):
        return self.request.get_full_path()

    def get_readonly_fields(self):
        return self.readonly_fields or ()

    def get_message_kwargs(self, obj):
        return {'obj': force_text(obj)}

    def get_message(self, msg_type_or_level, obj=None):
        msg_kwargs = {}
        if obj:
            msg_kwargs = self.get_message_kwargs(obj)

        msg_type = (isinstance(msg_type_or_level, int) and constants.DEFAULT_TAGS.get(msg_type_or_level)
                    or msg_type_or_level)
        return self.messages.get(msg_type) % msg_kwargs

    def is_changed(self, form, **kwargs):
        """
        Retrun true if form was changed
        """
        return form.has_changed()

    def save_obj(self, obj, form, change):
        """
        Must be added for non model forms
        this method should save object or raise exception
        """

        raise NotImplementedError

    def save_form(self, form, **kwargs):
        """
        Contains formset save, prepare obj for saving
        """

        obj = form.save(commit=False)
        change = obj.pk is not None
        self.save_obj(obj, form, change)
        if hasattr(form, 'save_m2m'):
            form.save_m2m()
        return obj

    @transaction.atomic
    def _atomic_save_form(self, *args, **kwargs):
        return self.save_form(*args, **kwargs)

    def form_valid(self, form, msg=None, msg_level=None, **kwargs):
        try:
            if self.atomic_save_form:
                obj = self._atomic_save_form(form, **kwargs)
            else:
                obj = self.save_form(form, **kwargs)
        except PersistenceException as ex:
            return self.form_invalid(form, msg=force_text(ex.message), **kwargs)
        return self.success_render_to_response(obj, msg, msg_level)

    def form_invalid(self, form, msg=None, msg_level=None, **kwargs):
        msg_level = msg_level or constants.ERROR
        msg = msg or self.get_message(msg_level)
        add_message(self.request, msg_level, msg)
        return self.render_to_response(self.get_context_data(form=form, msg=msg, msg_level=msg_level, **kwargs))

    def get_popup_obj(self, obj):
        return {'_obj_name': force_text(obj)}

    @property
    def is_ajax_form(self):
        """
        Return if form will be rendered for ajax
        """
        return self.has_snippet()

    @property
    def is_popup_form(self):
        """
        Return if form will be rendnered as popup
        """
        return 'popup' in self.request.GET

    @property
    def form_snippet_name(self):
        """
        Return name for name for snippet which surround form
        """
        return '%s-%s' % (self.view_name, 'form')

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
                                'form_snippet_name': self.form_snippet_name,
                                'buttons': self.get_buttons()
                             })
        return context_data

    def get_buttons(self):
        buttons = {}
        for key, value in self.get_buttons_dict().items():
            buttons[key] = {
                'label': value.get('label'),
                'title': value.get('title')
            }
        return buttons

    def get_buttons_dict(self):
        return {
            'save': {
                'label': self.save_button_label,
                'title': self.save_button_title
            },
            'cancel': {
                'label':  self.cancel_button_label,
                'title': self.cancel_button_title
            }
        }

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
        initial['_request'] = self.request
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

    def get_snippet_names(self):
        if self.is_popup_form:
            return [self.form_snippet_name]
        else:
            return super(DefaultFormView, self).get_snippet_names()

    def success_render_to_response(self, obj, msg, msg_level):
        msg_level = msg_level or constants.SUCCESS
        msg = msg or self.get_message(msg_level, obj)
        if self.is_popup_form:
            return JsonHttpResponse({'messages': {msg_level: msg}, 'obj': self.get_popup_obj(obj)})
        elif self.is_ajax_form:
            add_message(self.request, msg_level, msg)
            location = self.get_success_url(obj)
            response = JsonHttpResponse({'location': location}, status=202)
            response['Location'] = location
            return response
        else:
            add_message(self.request, msg_level, msg)
            return HttpResponseRedirect(self.get_success_url(obj))

    def render_to_response(self, context, **response_kwargs):
        if self.has_snippet():
            extra_content = response_kwargs['extra_content'] = response_kwargs.get('extra_content', {})
            extra_content_messages = {}
            for message in get_messages(self.request):
                extra_content_messages[message.tags] = force_text(message)
            if extra_content_messages:
                extra_content['messages'] = extra_content_messages
        return super(DefaultFormView, self).render_to_response(context, **response_kwargs)

    def has_permission(self, **kwargs):
        return True

    def has_get_permission(self, **kwargs):
        return self.has_permission(**kwargs)

    def has_post_permission(self, **kwargs):
        return self.has_permission(**kwargs)


class DefaultModelFormView(DefaultFormView):
    model = None
    exclude = None
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

    def get_message_kwargs(self, obj):
        return {'obj': force_text(obj), 'name': force_text(obj._meta.verbose_name)}

    def get_exclude(self):
        return self.exclude or ()

    def generate_readonly_fields(self):
        return self.get_readonly_fields()

    def get_inline_views(self):
        return self.inline_views or ()

    def init_inline_views(self, instance):
        inline_views = OrderedDict()
        for inline_view in self.get_inline_views():
            inline_views[inline_view.__name__] = inline_view(self.request, self, instance)
        return inline_views

    def _filter_inline_form_views(self, inline_views):
        inline_form_views = OrderedDict()
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
        exclude = list(self.get_exclude())
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return smartmodelform_factory(self.model, self.request, form=form_class, exclude=exclude, fields=fields,
                                      formfield_callback=self.formfield_for_dbfield,
                                      readonly_fields=readonly_fields,
                                      formreadonlyfield_callback=self.formfield_for_readonlyfield,
                                      readonly=not self.has_post_permission())

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def formfield_for_readonlyfield(self, name, **kwargs):
        def _get_readonly_field_data(instance):
            return get_readonly_field_data(name, (self, self.core, instance),
                                           {'request':self.request}, self.request)
        return SmartReadonlyField(_get_readonly_field_data)

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

    def has_save_button(self):
        return self.has_post_permission()

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
        inline_forms_is_valid = True

        inline_views = self.init_inline_views(form.instance)
        inline_form_views = self._filter_inline_form_views(inline_views)

        for inline_form_view in inline_form_views.values():
            inline_forms_is_valid = (inline_form_view.formset.is_valid()) \
                                        and inline_forms_is_valid

        is_valid = form.is_valid()
        is_changed = self.is_changed(form, inline_form_views=inline_form_views)

        if is_valid and inline_forms_is_valid and is_changed:
            return self.form_valid(form, inline_form_views=inline_form_views,
                                   inline_views=inline_views)
        else:
            if is_valid and not is_changed:
                return self.form_invalid(form, inline_form_views=inline_form_views,
                                         inline_views=inline_views,
                                         msg=_('No changes have been submitted.'),
                                         msg_level=constants.INFO)
            return self.form_invalid(form, inline_form_views=inline_form_views, inline_views=inline_views)

    def get_obj(self, cached=True):
        return None

    def get_form_kwargs(self):
        kwargs = super(DefaultModelFormView, self).get_form_kwargs()
        kwargs['instance'] = self.get_obj(False)
        return kwargs

    def save_form(self, form, inline_form_views=None, **kwargs):
        inline_form_views = inline_form_views or {}

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

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super(DefaultModelFormView, self).get_context_data(form=form,
                                                                          inline_form_views=inline_form_views,
                                                                          **kwargs)
        if django.VERSION < (1, 7):
            module_name = str(self.model._meta.module_name)
        else:
            module_name = str(self.model._meta.model_name)
        context_data.update({
            'module_name': module_name,
            'cancel_url': self.get_cancel_url(),
            'show_save_button': self.has_save_button()
        })
        return context_data

    def get_popup_obj(self, obj):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.object_name
        return {'_obj_name': force_text(obj), 'pk': obj.pk, '_model': '%s.%s' % (app_label, model_name)}


class DefaultCoreModelFormView(ListParentMixin, DefaultModelFormView):

    show_save_and_continue = True

    save_button_title = _('Save and navigate to the list')

    save_and_continue_button_title = _('Save and stay on the same page')
    save_and_continue_button_label = _("Save and continue")

    cancel_button_title = _('Do not save and go back to the list')

    def get_buttons_dict(self):
        buttons_dict = super(DefaultCoreModelFormView, self).get_buttons_dict()
        buttons_dict.update({
            'save_and_continue': {
                'label': self.save_and_continue_button_label,
                'title':  self.save_and_continue_button_title
            }
        })
        return buttons_dict

    def save_obj(self, obj, form, change):
        self.core.save_model(self.request, obj, form, change)

    def pre_save_obj(self, obj, form, change):
        self.core.pre_save_model(self.request, obj, form, change)

    def post_save_obj(self, obj, form, change):
        self.core.post_save_model(self.request, obj, form, change)

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
        return (self.fieldsets is not None and self.fieldsets or
                self.core.get_form_fieldsets(self.request, self.get_obj(True)))

    def get_fields(self):
        return (self.fields is not None and self.fields or
                self.core.get_ui_form_fields(self.request, self.get_obj(True)))

    def get_form_class(self):
        return self.form_class or self.core.get_ui_form_class(self.request, self.get_obj(True))

    def get_cancel_url(self):
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').get_view(self.request).has_get_permission() \
                and not self.has_snippet():
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        return None

    def has_save_and_continue_button(self):
        return 'list' in self.core.ui_patterns and not self.has_snippet() \
                and self.core.ui_patterns.get('list').get_view(self.request).has_get_permission() \
                and self.show_save_and_continue

    def has_save_button(self):
        return self.view_type in self.core.ui_patterns and self.has_post_permission()

    def get_success_url(self, obj):
        if 'list' in self.core.ui_patterns \
                and self.core.ui_patterns.get('list').get_view(self.request).has_get_permission() \
                and 'save' in self.request.POST:
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        elif 'edit' in self.core.ui_patterns \
                and self.core.ui_patterns.get('edit').get_view(self.request).has_get_permission(obj=obj) \
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
        return (self.title or
                self.model._ui_meta.add_verbose_name % {'verbose_name': self.model._meta.verbose_name,
                                                        'verbose_name_plural': self.model._meta.verbose_name_plural})

    def has_permission(self, **kwargs):
        return self.core.has_ui_create_permission(self.request)


class EditModelFormView(GetCoreObjViewMixin, DefaultCoreModelFormView):
    template_name = 'generic_views/edit_form.html'
    form_template = 'forms/model_edit_form.html'
    view_type = 'edit'
    messages = {'success': _('The %(name)s "%(obj)s" was changed successfully.'),
                'error': _('Please correct the error below.')}
    pk_name = 'pk'

    def get_title(self):
        return (self.title or
                self.model._ui_meta.edit_verbose_name % {
                        'verbose_name': self.model._meta.verbose_name,
                        'verbose_name_plural': self.model._meta.verbose_name_plural,
                        'obj': self.get_obj(True)
                    })

    def link(self, arguments=None, **kwargs):
        if arguments is None:
            arguments = (self.kwargs[self.pk_name],)
        return super(EditModelFormView, self).link(arguments=arguments, **kwargs)

    # TODO: get_obj should not be inside cor. get_obj and _get_perm_obj_or_404 should have same implementation
    # this object shoul return None if object does not exists. Becouase has_get_permission and has_post_permission
    # should be called outside
    def _get_perm_obj_or_404(self, pk=None):
        """
        If is send parameter pk is returned object according this pk,
        else is returned object from get_obj method, but it search only inside filtered values for current user,
        finally if object is still None is returned according the input key from all objects.
        
        If object does not exist is raised Http404
        """
        if pk:
            obj = get_object_or_none(self.core.model, pk=pk)
        else:
            try:
                obj = self.get_obj(False)
            except Http404:
                obj = get_object_or_none(self.core.model, **self.get_obj_filters())
        if not obj:
            raise Http404
        return obj

    # Should return false if object does not exists and 404 should be resolved with different way
    def has_get_permission(self, obj=None, pk=None, **kwargs):
        obj = obj or self._get_perm_obj_or_404(pk)
        return (self.core.has_ui_read_permission(self.request, obj=obj) or
                self.core.has_ui_update_permission(self.request, obj=obj))

    def has_post_permission(self, obj=None, pk=None, **kwargs):
        obj = obj or self._get_perm_obj_or_404(pk)
        return self.core.has_ui_update_permission(self.request, obj=obj)


class DetailModelFormView(EditModelFormView):
    show_save_and_continue = False

    def has_post_permission(self, **kwargs):
        return False

    def has_save_button(self):
        return False
