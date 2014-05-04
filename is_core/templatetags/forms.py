from __future__ import unicode_literals

from django import template
from django.forms import CheckboxInput
from django.template.loader import render_to_string
from django.template.base import TemplateSyntaxError, token_kwargs
from django.db.models.fields import FieldDoesNotExist, DateTimeField
from django.db.models.fields.related import ForeignKey, ManyToManyRel
from django.contrib.admin.util import display_for_value
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

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
def inline_form_view_renderer(context, inline_view, title=None):
    template = inline_view.template_name

    formset = inline_view.formset
    fieldset = inline_view.get_fieldset(formset)
    class_names = [inline_view.get_name().lower()]
    if formset.can_add:
        class_names.append('can-add')
    if formset.can_delete:
        class_names.append('can-delete')

    if title:
        class_names.append('with-title')
    else:
        class_names.append('without-title')

    context.update({
                        'formset': formset,
                        'fieldset': fieldset,
                        'name': inline_view.get_name(),
                        'button_value': inline_view.get_button_value(),
                        'title': title,
                        'class_names': class_names,
                    })
    return render_to_string(template, context)


@register.simple_tag(takes_context=True)
def fieldset_renderer(context, form, fieldset):
    values = fieldset[1]
    inline_form_view = values.get('inline_form_view')
    if inline_form_view:
        return inline_form_view_renderer(context, context.get('inline_form_views').get(inline_form_view), fieldset[0])

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


def get_model_field_value_and_label(field_name, instance, request):
    if '__' in field_name:
        current_field_name, next_field_name = field_name.split('__', 1)
        return get_model_field_value_and_label(next_field_name, getattr(instance, current_field_name), request)
    else:
        callable_value = getattr(instance, 'get_%s_display' % field_name, None)
        if not callable_value:
            callable_value = getattr(instance, field_name)
        if hasattr(callable_value, '__call__'):
            value = callable_value()
        else:
            value = callable_value

        if isinstance(callable_value, bool):
            value = _('Yes') if value else _('No')
        else:
            value = display_for_value(value)

        try:
            field = instance._meta.get_field_by_name(field_name)[0]
        except FieldDoesNotExist:
            field = None

        if field:
            label = field.verbose_name

            if isinstance(field.rel, ManyToManyRel) and callable_value is not None and \
                    hasattr(getattr(callable_value, 'all'), '__call__'):
                value = mark_safe('<ul>%s</ul>' %
                                  ''.join(['<li>%s</li>' % force_text(obj) for obj in callable_value.all()]))

            if isinstance(field, ForeignKey) \
                and hasattr(getattr(callable_value, 'get_absolute_url', None), '__call__') \
                and hasattr(getattr(callable_value, 'can_see_edit_link', None), '__call__') \
                and callable_value.can_see_edit_link(request):
                value = '<a href="%s">%s</a>' % (callable_value.get_absolute_url(), force_text(value))

            elif hasattr(instance, field_name):
                humanize_method_name = 'get_%s_humanized' % field_name
                if hasattr(getattr(instance, humanize_method_name, None), '__call__'):
                    value = '<span title="%s">%s</span>' % (force_text(value), getattr(instance, humanize_method_name)())

        else:
            label = callable_value.short_description

        return mark_safe(linebreaks(force_text(value))), label


@register.assignment_tag(takes_context=True)
def get_field(context, form, field_name):
    request = context['request']
    field = form.fields.get(field_name)
    if not field:
        instance = form.instance
        value, label = get_model_field_value_and_label(field_name, instance, request)

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
