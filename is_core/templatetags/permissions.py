from django.template.base import Node, TemplateSyntaxError, NodeList, kwarg_re
from django.utils.encoding import force_text
from django.utils.functional import SimpleLazyObject
from django.template import Library

from is_core.utils import get_link_or_none


register = Library()


class Permissions:
    permissions_validators = {}

    def register_permission_validator(self, name, validator):
        self.permissions_validators[name] = validator


permissions = Permissions()


def get_obj(Model, pk):
    return Model.objects.get(pk=pk)


class PermissionNode(Node):

    def __init__(self, perm_name, vals, nodelist_true, nodelist_false):
        self.perm_name = perm_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.vals = vals

    def render(self, context):
        perm_name = self.perm_name.resolve(context, True)
        request = context.get('request')
        args = []
        for val in self.vals:
            args.append(val.resolve(context))

        core_permission = context.get('core_permission', {})
        view = context.get('view')
        if core_permission.has_permission(perm_name, request, view, *args):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

    def validator_kwargs(self, request, validator):
        if 'pk' in request.kwargs:
            Model = getattr(validator.im_self, 'model')
            if Model:
                return {'obj': SimpleLazyObject(lambda: get_obj(Model, request.kwargs['pk']))}
        return {}


@register.tag
def has_permission(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError("%r takes minimal one argument" % bits[0])
    end_tag = 'end' + bits[0]

    vals = []
    for bit in bits[2:]:
        vals.append(parser.compile_filter(bit))

    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return PermissionNode(parser.compile_filter(bits[1]), vals, nodelist_true, nodelist_false)


class PermissionURLNode(Node):

    def __init__(self, pattern_name, kwargs, nodelist_true, nodelist_false):
        self.pattern_name = pattern_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.kwargs = kwargs

    def render(self, context):
        pattern_name = self.pattern_name.resolve(context, True)
        request = context.get('request')
        kwargs = {
            force_text(k, 'ascii'): v.resolve(context)
            for k, v in self.kwargs.items()
        }

        link = get_link_or_none(pattern_name, request, view_kwargs=kwargs)
        if link:
            return self.nodelist_true.render(context.new({'url': link}))
        else:
            return self.nodelist_false.render(context)


@register.tag
def has_permission_to_url(parser, token):
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError('"has_permission_to_url" takes minimal one argument')

    end_tag = 'end' + bits[0]

    kwargs = {}
    for bit in bits[2:]:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError('Malformed arguments to has_permission_to_url tag')
        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)
        else:
            raise TemplateSyntaxError('Malformed arguments to has_permission_to_url tag')

    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return PermissionURLNode(parser.compile_filter(bits[1]), kwargs, nodelist_true, nodelist_false)
