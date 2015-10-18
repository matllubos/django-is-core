from __future__ import unicode_literals

from django import template
from django.forms import CheckboxInput
from django.template.loader import render_to_string
from django.template.base import TemplateSyntaxError, token_kwargs
from django.template.loader_tags import IncludeNode

from is_core.forms.widgets import WrapperWidget


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
    return IncludeNode(template_name, extra_context=options)


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
        'class': values.get('class'),
        'fieldsets': values.get('fieldsets')
    })
    return render_to_string(template, context)


@register.assignment_tag(takes_context=True)
def get_field(context, form, field_name):
    search_instances = []

    view = context.get('view')
    if view:
        search_instances.append(view)

    core = context.get('core')
    if core:
        search_instances.append(core)

    if hasattr(form, 'instance'):
        search_instances.append(form.instance)

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
    return (hasattr(field, 'field') and hasattr(field.field, 'widget') and
            (isinstance(field.field.widget, CheckboxInput) or
             (isinstance(field.field.widget, WrapperWidget) and isinstance(field.field.widget.widget, CheckboxInput))))
