from django import template
from django.template.loader import render_to_string
from django.template.base import TemplateSyntaxError, token_kwargs

from is_core.snippets import SnippetsIncludeNode

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
    class_names = [inline_view.get_name().lower()]
    if formset.can_add:
        class_names.append('can-add')
    if formset.can_delete:
        class_names.append('can-delete')
    if formset.readonly:
        class_names.append('readonly')

    if title:
        class_names.append('with-title')
    else:
        class_names.append('without-title')

    context.update({
                        'formset': formset,
                        'name': inline_view.get_name(),
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


@register.filter
def get_field(form, field_name):
    return form[field_name]


@register.filter
def model_name(form):
    return form._meta.model._meta.module_name


@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)
