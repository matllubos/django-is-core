from django import template
from django.forms import CheckboxInput
from django.template.base import TemplateSyntaxError, token_kwargs, Node
from django.template.loader import render_to_string

from is_core.config import settings
from is_core.utils import pretty_class_name
from is_core.forms.widgets import WrapperWidget


register = template.Library()


class FormNode(Node):

    def __init__(self, template, *args, **kwargs):
        self.template = template
        self.extra_context = kwargs.pop('extra_context', {})
        super().__init__(*args, **kwargs)

    def render(self, context):
        template = self.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, 'render', None)):
            # If not, we'll try our cache, and get_template()
            template_name = template
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.get_template(template_name)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, 'template'):
            template = template.template
        values = {
            name: var.resolve(context)
            for name, var in self.extra_context.items()
        }
        with context.push(**values):
            return template.render(context)


@register.tag('form_renderer')
def do_form_renderer(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag takes at least one argument: the form that will be rendered" % bits[0])
    remaining_bits = bits[2:]
    options = token_kwargs(remaining_bits, parser, support_legacy=False)
    template_name = options.get('template', parser.compile_filter("'is_core/forms/default_form.html'"))
    options['use_csrf'] = options.get('use_csrf', parser.compile_filter('True'))
    options['form'] = parser.compile_filter(bits[1])
    options['method'] = options.get('method', parser.compile_filter("'POST'"))
    return FormNode(template_name, extra_context=options)


@register.simple_tag(takes_context=True)
def fieldset_renderer(context, form, fieldset):
    context_dict = {}
    for data in context:
        context_dict.update(data)
    request = context_dict.pop('request', None)
    values = fieldset[1]
    inline_view = values.get('inline_view_inst')
    context_dict.update({
        'class': values.get('class'),
    })

    rendered_inline_view = (
        inline_view.render(context.new(context_dict), fieldset[0]) if inline_view else ''
    )

    rendered_fieldsets = []
    for sub_fieldset in values.get('fieldsets', ()):
        rendered_fieldset = fieldset_renderer(context, form, sub_fieldset)
        if rendered_fieldset:
            rendered_fieldsets.append(rendered_fieldset)

    fields = values.get('fields')

    if fields or rendered_fieldsets or rendered_inline_view:
        template = values.get('template') or settings.DEFAULT_FIELDSET_TEMPLATE
        context_dict.update({
            'fields': fields,
            'form': form,
            'title': fieldset[0],
            'class': values.get('class'),
            'fieldsets': values.get('fieldsets'),
            'rendered_fieldsets': rendered_fieldsets,
            'rendered_inline_view': rendered_inline_view,
        })
        return render_to_string(template, context_dict, request=request)
    else:
        return ''


@register.simple_tag(takes_context=True)
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


@register.simple_tag(takes_context=True)
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


@register.filter
def field_type(field):
    return field.type if hasattr(field, 'type') else pretty_class_name(field.field.widget.__class__.__name__)
