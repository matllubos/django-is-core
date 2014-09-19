from __future__ import unicode_literals

import inspect

from django import template
from django.forms import CheckboxInput
from django.template.loader import render_to_string
from django.template.base import TemplateSyntaxError, token_kwargs
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignKey, ManyToManyRel
from django.contrib.admin.util import display_for_value
from django.utils.html import linebreaks, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from block_snippets.templatetags import SnippetsIncludeNode


register = template.Library()


@register.tag('form_renderer')
def do_form_renderer(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag takes at least one argument: the form that will be rendered" % bits[0])
    remaining_bits = bits[2:]
    options = token_kwargs(remaining_bits, parser, support_legacy=False)
    template_name = options.get('template', parser.compile_filter("'forms/default_form.html'"))
    options['use_csrf'] = options.get('use_csrf', parser.compile_filter('True'))
    options['form'] = parser.compile_filter(bits[1])
    options['method'] = options.get('method', parser.compile_filter("'POST'"))
    return SnippetsIncludeNode(template_name, extra_context=options)


@register.simple_tag(takes_context=True)
def fieldset_renderer(context, form, fieldset):
    values = fieldset[1]
    inline_view_name = values.get('inline_view')
    if inline_view_name:
        return context.get('inline_views').get(inline_view_name).render(context, fieldset[0])
    template = values.get('template') or 'forms/default_fieldset.html'
    context.update({
                        'fields': values.get('fields'),
                        'form': form,
                        'title': fieldset[0],
                        'class': values.get('class')
                    })
    return render_to_string(template, context)


class ReadonlyField(object):

    is_readonly = True
    is_hidden = False

    def __init__(self, label, content):
        self.label = label
        self.content = content

    def __unicode__(self):
        return self.content


def get_callable_value(callable_value, fun_kwargs):
    if hasattr(callable_value, '__call__'):
        maybe_kwargs_names = inspect.getargspec(callable_value)[0][1:]
        maybe_kwargs = {}

        for arg_name in maybe_kwargs_names:
            if arg_name in fun_kwargs:
                maybe_kwargs[arg_name] = fun_kwargs[arg_name]

        if len(maybe_kwargs_names) == len(maybe_kwargs):
            return callable_value(**maybe_kwargs)
        else:
            raise AttributeError
    else:
        return callable_value


def display_for_field_value(instance, field, value, callable_value, request):
    if (isinstance(field.rel, ManyToManyRel) and callable_value is not None and
        hasattr(getattr(callable_value, 'all'), '__call__')):
        return mark_safe('<ul>%s</ul>' % ''.join(['<li>%s</li>' % force_text(obj) for obj in callable_value.all()]))

    elif (isinstance(field, ForeignKey)
          and hasattr(getattr(callable_value, 'get_absolute_url', None), '__call__')
          and hasattr(getattr(callable_value, 'can_see_edit_link', None), '__call__')
          and callable_value.can_see_edit_link(request)):
        return mark_safe('<a href="%s">%s</a>' % (callable_value.get_absolute_url(), force_text(value)))

    elif hasattr(instance, field.name):
        humanize_method_name = 'get_%s_humanized' % field.name
        if hasattr(getattr(instance, humanize_method_name, None), '__call__'):
            return mark_safe('<span title="%s">%s</span>' % (force_text(value), getattr(instance,
                                                                                        humanize_method_name)()))
    return value


def get_instance_field_value_and_label(field_name, instance, fun_kwargs, request):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        return get_instance_field_value_and_label(next_field_name, getattr(instance, current_field_name), fun_kwargs,
                                                  request)
    else:
        callable_value = getattr(instance, 'get_%s_display' % field_name, None)
        if not callable_value:
            # Exeption because OneToOne Field
            try:
                callable_value = getattr(instance, field_name)
            except ObjectDoesNotExist:
                callable_value = None
        value = get_callable_value(callable_value, fun_kwargs)

        if isinstance(value, bool):
            value = _('Yes') if value else _('No')
        else:
            value = display_for_value(value)

        try:
            field = instance._meta.get_field_by_name(field_name)[0]
        except (FieldDoesNotExist, AttributeError):
            field = None

        if field:
            label = field.verbose_name

            value = display_for_field_value(instance, field, value, callable_value, request)

        else:
            label = callable_value.short_description

        return mark_safe(linebreaks(conditional_escape(force_text(value)))), label


def get_field_value_and_label(field_name, instances, fun_kwargs, request):
    for inst in instances:
        try:
            return get_instance_field_value_and_label(field_name, inst, fun_kwargs, request)
        except AttributeError:
            pass
    raise AttributeError('Field with name %s not found' % field_name)


@register.assignment_tag(takes_context=True)
def get_field(context, form, field_name):
    request = context['request']

    search_instances = []

    view = context.get('view')
    if view:
        search_instances.append(view)

    core = context.get('core')
    if core:
        search_instances.append(core)

    if hasattr(form, 'instance'):
        search_instances.append(form.instance)

    field = form.fields.get(field_name)
    if not field:
        value, label = get_field_value_and_label(field_name, search_instances, context, request)
        return ReadonlyField(label, value or '')

    return form[field_name]


@register.assignment_tag(takes_context=True)
def get_visible_fields(context, form, fieldset):
    visible_fields = []
    for field_name in fieldset:
        field = get_field(context, form, field_name)
        if not field.is_hidden:
            visible_fields.append(field)
    return visible_fields


@register.filter
def model_name(form):
    return form._meta.model._meta.module_name


@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)


@register.filter
def is_checkbox(field):
    return hasattr(field, 'field') and hasattr(field.field, 'widget') and isinstance(field.field.widget, CheckboxInput)
