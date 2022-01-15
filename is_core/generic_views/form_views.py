from copy import deepcopy

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http.response import HttpResponseRedirect, Http404
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.contrib.messages.api import get_messages, add_message
from django.contrib.messages import constants

from chamber.utils.forms import formset_has_file_field
from chamber.utils import transaction

from is_core.auth.permissions import PermissionsSet, CoreUpdateAllowed, CoreAllowed, DEFAULT_PERMISSION
from is_core.auth.views import FieldPermissionViewMixin
from is_core.generic_views.base import DefaultModelCoreViewMixin
from is_core.utils import (
    flatten_fieldsets, get_readonly_field_data, get_inline_views_from_fieldsets, get_inline_views_opts_from_fieldsets,
    GetMethodFieldMixin, get_model_name, get_fieldsets_without_disallowed_fields
)
from is_core.generic_views.mixins import ListParentMixin
from is_core.generic_views.inlines.inline_form_views import InlineFormView
from is_core.response import JsonHttpResponse
from is_core.forms.models import smartmodelform_factory
from is_core.forms.fields import SmartReadonlyField
from is_core.forms import SmartModelForm


class BaseFormView(GetMethodFieldMixin, DefaultModelCoreViewMixin, FormView):

    view_type = 'default'
    fieldsets = None
    fields = None
    form_template = 'is_core/forms/default_form.html'
    template_name = 'is_core/generic_views/default_form.html'
    messages = {
        'success': _('Object was saved successfully.'),
        'error': _('Please correct the error below.'),
    }
    readonly_fields = None

    save_button_label = _('Save')
    save_button_title = ''
    save_button_disable_on_submit = True

    cancel_button_label = _('Back')
    cancel_button_title = ''
    cancel_button_disable_on_submit = True

    atomic_save_form = True

    def get_success_url(self, obj):
        """
        URL string for redirect after saving
        """

        return self.request.get_full_path()

    def get_has_file_field(self, form, **kwargs):
        return formset_has_file_field(form)

    def is_readonly(self):
        return not self.has_permission('post')

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.readonly = self.is_readonly()

        for field_name, field in form.fields.items():
            self.form_field(form, field_name, field)
        return form

    def get_form_action(self):
        return self.request.get_full_path()

    def get_readonly_fields(self):
        return () if self.readonly_fields is None else self.readonly_fields

    def get_message_kwargs(self, obj):
        return {'obj': force_text(obj)}

    def get_message(self, msg_type_or_level, obj=None):
        msg_kwargs = {}
        if obj:
            msg_kwargs = self.get_message_kwargs(obj)

        msg_type = (isinstance(msg_type_or_level, int) and constants.DEFAULT_TAGS.get(msg_type_or_level) or
                    msg_type_or_level)
        return self.messages.get(msg_type) % msg_kwargs

    def is_changed(self, form, **kwargs):
        """Return true if form was changed"""
        return form.has_changed()

    def save_obj(self, obj, form, change):
        """
        Must be added for non model forms
        this method should save object or raise exception
        """

        raise NotImplementedError

    def save_form(self, form, **kwargs):
        """Contains formset save, prepare obj for saving"""

        obj = form.save(commit=False)
        change = obj.pk is not None
        self.save_obj(obj, form, change)
        if hasattr(form, 'save_m2m'):
            form.save_m2m()
        return obj

    @transaction.smart_atomic
    def _atomic_save_form(self, *args, **kwargs):
        return self.save_form(*args, **kwargs)

    def form_valid(self, form, msg=None, msg_level=None, **kwargs):
        try:
            if self.atomic_save_form:
                obj = self._atomic_save_form(form, **kwargs)
            else:
                obj = self.save_form(form, **kwargs)
            return self.success_render_to_response(obj, msg, msg_level)
        except ValidationError as ex:
            return self.form_invalid(form, msg=force_text(ex.message), **kwargs)

    def form_invalid(self, form, msg=None, msg_level=None, **kwargs):
        msg_level = msg_level or constants.ERROR
        msg = msg or self.get_message(msg_level)
        add_message(self.request, msg_level, msg)
        return self.render_to_response(self.get_context_data(form=form, msg=msg, msg_level=msg_level, **kwargs))

    def get_popup_obj(self, obj):
        return {'_obj_name': force_text(obj)}

    @property
    def is_ajax_form(self):
        """Return if form will be rendered for ajax"""
        return self.has_snippet()

    @property
    def is_popup_form(self):
        """Return if form will be rendnered as popup"""
        return 'popup' in self.request.GET

    @property
    def form_snippet_name(self):
        """Return name for name for snippet which surround form"""
        return '%s-%s' % (self.view_name, 'form')

    def get_form_class_names(self):
        class_names = ['-'.join((self.view_type, self.site_name,
                                 self.core.get_menu_group_pattern_name(), 'form',)).lower()]
        if self.is_ajax_form:
            class_names.append('ajax')
        return class_names

    def get_prefix(self):
        return '-'.join((self.view_type, self.site_name)).lower()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        kwargs.pop('form', form)
        context_data.update({
            'view_type': self.view_type,
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
                'title': value.get('title'),
                'disable_on_submit': value.get('disable_on_submit'),
            }
        return buttons

    def get_buttons_dict(self):
        return {
            'save': {
                'label': self.save_button_label,
                'title': self.save_button_title,
                'disable_on_submit': self.save_button_disable_on_submit,
            },
            'cancel': {
                'label': self.cancel_button_label,
                'title': self.cancel_button_title,
                'disable_on_submit': self.cancel_button_disable_on_submit,
            }
        }

    def get_fields(self):
        fieldsets = self.get_fieldsets()
        return self.fields if fieldsets is None else flatten_fieldsets(fieldsets)

    def get_fieldsets(self):
        return self.fieldsets

    def generate_fieldsets(self, form):
        fieldsets = self.get_fieldsets()
        return [
            (None, {'fields': self.get_fields() or list(form.base_fields.keys())})
        ] if fieldsets is None else fieldsets

    def get_initial(self):
        initial = super().get_initial()
        initial['_user'] = self.request.user
        initial['_request'] = self.request
        return initial

    def form_field(self, form, field_name, form_field):
        return form_field

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        fieldsets = self.generate_fieldsets(form)
        return self.render_to_response(self.get_context_data(form=form, fieldsets=fieldsets))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        fieldsets = self.generate_fieldsets(form)

        is_valid = form.is_valid()
        is_changed = self.is_changed(form)

        if is_valid and is_changed:
            return self.form_valid(form)
        else:
            if is_valid and not is_changed:
                return self.form_invalid(
                    form, msg=_('No changes have been submitted.'), msg_level=constants.INFO,
                    fieldsets=fieldsets
                )
            return self.form_invalid(form, fieldsets=fieldsets)

    def get_snippet_names(self):
        if self.is_popup_form:
            return [self.form_snippet_name]
        else:
            return super().get_snippet_names()

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
        return super().render_to_response(context, **response_kwargs)


class DjangoBaseFormView(FieldPermissionViewMixin, BaseFormView):

    model = None
    exclude = ()
    field_labels = None
    inline_views = None
    form_template = 'is_core/forms/model_default_form.html'
    show_buttons = True

    def _get_field_labels(self):
        return self.field_labels

    def pre_save_obj(self, obj, form, change):
        pass

    def post_save_obj(self, obj, form, change):
        pass

    def form_field(self, form, field_name, form_field):
        form_field = super().form_field(form, field_name, form_field)
        placeholder = self.model._ui_meta.placeholders.get(field_name, None)
        if placeholder:
            form_field.widget.placeholder = placeholder
        return form_field

    def get_message_kwargs(self, obj):
        return {'obj': force_text(obj), 'name': force_text(obj._meta.verbose_name)}

    def get_exclude(self):
        return self.exclude

    def generate_readonly_fields(self):
        return list(self.get_readonly_fields()) + list(self._get_readonly_fields_from_permissions())

    def get_inline_views(self):
        return self.inline_views

    def _filter_inline_form_views(self, inline_views):
        return [view for view in inline_views if isinstance(view, InlineFormView)]

    def generate_fieldsets(self, form):
        fieldsets = deepcopy(self.get_fieldsets())

        if fieldsets and self.get_inline_views():
            raise ImproperlyConfigured('You can define either inline views or fieldsets.')

        if fieldsets is None:
            fieldsets = [
                (None, {
                    'fields': self.get_fields() or form.base_fields.keys()
                })
            ]
            for inline_view in self.get_inline_views() or ():
                inline_view_inst = (
                    inline_view(self.request, self, form.instance) if isinstance(inline_view, type) else inline_view
                )
                if inline_view_inst.can_render():
                    # Only inline view that can be rendered is added to formset
                    fieldsets.append((
                        inline_view_inst.get_title(), {
                            'inline_view': inline_view,
                            'inline_view_inst': inline_view_inst
                        }
                    ))
        else:
            inline_view_opts = get_inline_views_opts_from_fieldsets(fieldsets)
            for inline_view_opt in inline_view_opts:
                inline_view = inline_view_opt['inline_view']
                inline_view_inst = (
                    inline_view(self.request, self, form.instance) if isinstance(inline_view, type) else inline_view
                )
                if inline_view_inst.can_render():
                    # Only inline view that can be rendered is added to formset
                    inline_view_opt['inline_view_inst'] = inline_view_inst

        return get_fieldsets_without_disallowed_fields(
            self.request, fieldsets, self._get_disallowed_fields_from_permissions() | set(self.get_exclude())
        )

    def get_form_class(self):
        fields = self.get_fields()
        readonly_fields = self.generate_readonly_fields()
        return self.generate_form_class(fields, readonly_fields)

    def get_form_class_base(self):
        return self.form_class or SmartModelForm

    def get_is_bulk(self):
        return False

    def generate_form_class(self, fields=None, readonly_fields=()):
        form_class = self.get_form_class_base()
        exclude = list(self.get_exclude())
        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return smartmodelform_factory(self.model, self.request, form=form_class, exclude=exclude, fields=fields,
                                      formfield_callback=self.formfield_for_dbfield,
                                      readonly_fields=readonly_fields,
                                      formreadonlyfield_callback=self.formfield_for_readonlyfield,
                                      readonly=self.is_readonly(),
                                      labels=self._get_field_labels(), is_bulk=self.get_is_bulk())

    def update_form_initial(self, form):
        # Only new instance can get data from request queryset
        if not form.instance.pk:
            form.initial.update({k: self.request.GET.get(k) for k in self.request.GET.keys()
                                 if k not in form.readonly_fields})
        return form

    def get_form(self, form_class=None):
        return self.update_form_initial(super().get_form(form_class=form_class))

    def formfield_for_dbfield(self, db_field, **kwargs):
        return db_field.formfield(**kwargs)

    def formfield_for_readonlyfield(self, name, **kwargs):
        def _get_readonly_field_data(instance):
            return get_readonly_field_data(
                instance, name, self.request, view=self, field_labels=self._get_field_labels()
            )
        return SmartReadonlyField(_get_readonly_field_data)

    def get_has_file_field(self, form, inline_form_views=None, **kwargs):
        if super().get_has_file_field(form, **kwargs):
            return True

        for inline_form_view in () if inline_form_views is None else inline_form_views:
            if inline_form_view.get_has_file_field():
                return True

        return False

    def get_show_buttons(self):
        return self.show_buttons

    def get_cancel_url(self):
        return None

    def has_save_button(self):
        return not self.is_readonly()

    def is_changed(self, form, inline_form_views, **kwargs):
        for inline_form_view_instance in inline_form_views:
            if inline_form_view_instance.has_changed():
                return True
        return form.has_changed()

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        fieldsets = self.generate_fieldsets(form)
        inline_views = get_inline_views_from_fieldsets(fieldsets)
        inline_form_views = self._filter_inline_form_views(inline_views)
        return self.render_to_response(self.get_context_data(form=form, inline_views=inline_views,
                                                             fieldsets=fieldsets,
                                                             inline_form_views=inline_form_views))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        fieldsets = self.generate_fieldsets(form)
        inline_views = get_inline_views_from_fieldsets(fieldsets)
        inline_form_views = self._filter_inline_form_views(inline_views)

        inline_forms_is_valid = True
        for inline_form_view in inline_form_views:
            inline_forms_is_valid = inline_form_view.is_valid() and inline_forms_is_valid

        is_valid = form.is_valid()
        is_changed = self.is_changed(form, inline_form_views=inline_form_views)
        if is_valid and inline_forms_is_valid and is_changed:
            return self.form_valid(form, inline_form_views=inline_form_views,
                                   inline_views=inline_views, fieldsets=fieldsets)
        else:
            if is_valid and not is_changed:
                return self.form_invalid(
                    form,
                    inline_form_views=inline_form_views,
                    inline_views=inline_views,
                    msg=_('No changes have been submitted.'),
                    msg_level=constants.INFO,
                    fieldsets=fieldsets
                )
            return self.form_invalid(
                form,
                inline_form_views=inline_form_views,
                inline_views=inline_views,
                fieldsets=fieldsets
            )

    def get_obj(self, cached=True):
        return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_obj(False)
        return kwargs

    def save_form(self, form, inline_form_views=None, **kwargs):
        inline_form_views = () if inline_form_views is None else inline_form_views
        pre_save_inline_form_views = [
            inline_form_view for inline_form_view in inline_form_views if inline_form_view.save_before_parent
        ]
        post_save_inline_form_views = [
            inline_form_view for inline_form_view in inline_form_views if not inline_form_view.save_before_parent
        ]

        obj = form.save(commit=False)
        change = obj.pk is not None

        self.pre_save_obj(obj, form, change)

        for inline_form_view in pre_save_inline_form_views:
            inline_form_view.form_valid(self.request)

        self.save_obj(obj, form, change)
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        for inline_form_view in post_save_inline_form_views:
            inline_form_view.form_valid(self.request)

        self.post_save_obj(obj, form, change)
        return obj

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super().get_context_data(form=form, inline_form_views=inline_form_views, **kwargs)

        show_buttons = self.get_show_buttons()
        context_data.update({
            'module_name': get_model_name(self.model),
            'cancel_url': self.get_cancel_url() if show_buttons else None,
            'show_save_button': show_buttons and self.has_save_button()
        })
        return context_data

    def get_popup_obj(self, obj):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.object_name
        return {'_obj_name': force_text(obj), 'pk': obj.pk, '_model': '%s.%s' % (app_label, model_name)}


class DjangoCoreFormView(ListParentMixin, DjangoBaseFormView):

    show_save_and_continue = True

    save_button_title = _('Save and navigate to the list')

    save_and_continue_button_title = _('Save and stay on the same page')
    save_and_continue_button_label = _('Save and continue')
    save_and_continue_button_disable_on_submit = True

    cancel_button_title = _('Do not save and go back to the list')

    export_types = None

    def get_prefix(self):
        return '-'.join((self.view_type, self.site_name, self.core.get_menu_group_pattern_name())).lower()

    def get_buttons_dict(self):
        buttons_dict = super().get_buttons_dict()
        buttons_dict.update({
            'save_and_continue': {
                'label': self.save_and_continue_button_label,
                'title': self.save_and_continue_button_title,
                'disable_on_submit': self.save_and_continue_button_disable_on_submit,
            }
        })
        return buttons_dict

    def save_obj(self, obj, form, change):
        self.core.save_model(self.request, obj, form, change)

    def pre_save_obj(self, obj, form, change):
        self.core.pre_save_model(self.request, obj, form, change)

    def post_save_obj(self, obj, form, change):
        self.core.post_save_model(self.request, obj, form, change)

    def get_readonly_fields(self):
        if self.readonly_fields is not None:
            return self.readonly_fields

        readonly_fields = self.core.get_readonly_fields(self.request, self.get_obj(True))
        return () if readonly_fields is None else readonly_fields

    def get_fieldsets(self):
        if self.fieldsets is not None or self.fields is not None:
            return self.fieldsets

        return self.core.get_fieldsets(self.request, self.get_obj(True))

    def get_fields(self):
        fieldsets = self.get_fieldsets()
        if fieldsets is not None:
            return flatten_fieldsets(fieldsets)
        elif self.fields is not None:
            return self.fields
        else:
            return self.core.get_fields(self.request, self.get_obj(True))

    def get_inline_views(self):
        if self.inline_views is not None:
            return self.inline_views

        return self.core.get_inline_views(self.request, self.get_obj(True))

    def _get_field_labels(self):
        return self.field_labels if self.field_labels is not None else self.core.get_field_labels(self.request)

    def get_form_class_base(self):
        obj = self.get_obj(True)
        return (
            self.form_class or
            (
                self.core.get_form_edit_class(self.request, obj)
                if obj
                else self.core.get_form_add_class(self.request, obj)
            )
        )

    def get_cancel_url(self):
        if ('list' in self.core.ui_patterns and
                self.core.ui_patterns.get('list').has_permission('get', self.request) and not self.has_snippet()):
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        return None

    def has_save_and_continue_button(self):
        return (
            'list' in self.core.ui_patterns and not self.has_snippet() and
            self.core.ui_patterns.get('list').has_permission('get', self.request) and
            self.show_save_and_continue and
            not self.is_readonly()
        )

    def has_save_button(self):
        return self.view_type in self.core.ui_patterns and not self.is_readonly()

    def get_success_url(self, obj):
        if ('list' in self.core.ui_patterns and
                self.core.ui_patterns.get('list').has_permission('get', self.request) and
                'save' in self.request.POST):
            return self.core.ui_patterns.get('list').get_url_string(self.request)
        elif ('detail' in self.core.ui_patterns and
                self.core.ui_patterns.get('detail').has_permission('get', self.request, obj=obj) and
                'save-and-continue' in self.request.POST):
            return self.core.ui_patterns.get('detail').get_url_string(self.request, view_kwargs={'pk': obj.pk})
        else:
            return self.request.get_full_path()

    def get_context_data(self, form=None, inline_form_views=None, **kwargs):
        context_data = super().get_context_data(form=form, inline_form_views=inline_form_views, **kwargs)
        context_data.update({
            'show_save_and_continue': self.has_save_and_continue_button()
        })
        return context_data


class BulkChangeFormView(DjangoBaseFormView):

    form_template = 'is_core/views/bulk-change-view.html'
    is_ajax_form = False

    permission = PermissionsSet(
        get=CoreUpdateAllowed(),
        post=CoreUpdateAllowed(),
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    def get_prefix(self):
        return '-'.join((self.view_type, self.site_name, self.core.get_menu_group_pattern_name())).lower()

    def get_form_class_base(self):
        return self.form_class or self.core.get_rest_form_edit_class(self.request)

    def dispatch(self, request, *args, **kwargs):
        if 'snippet' not in request.GET:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_fields(self):
        return self.core.get_bulk_change_fields(self.request) if self.fields is None else self.fields

    def get_fieldsets(self):
        return (
            (None, {'fields': self.get_fields()}),
        )

    def generate_fieldsets(self, form):
        return get_fieldsets_without_disallowed_fields(
            self.request,
            self.get_fieldsets(),
            (
                self._get_disallowed_fields_from_permissions()
                | set(self.generate_readonly_fields())
                | set(self.get_exclude())
            )
        )

    def get_readonly_fields(self):
        return ()

    def get_is_bulk(self):
        return True
