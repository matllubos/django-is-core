from __future__ import unicode_literals

from django.template import Library
from django.template.base import Node, TemplateSyntaxError, NodeList
from django.utils.functional import SimpleLazyObject

register = Library()


class Permissions(object):
    permissions_validators = {}

    def register_permission_validator(self, name, validator):
        self.permissions_validators[name] = validator

permissions = Permissions()


def get_obj(Model, pk):
    return Model.objects.get(pk=pk)


# TODO: there is possibility cache permissions
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

        view_permissions = context.get('permissions', {})

        if perm_name in view_permissions:
            perm_fun_or_bool = view_permissions.get(perm_name)
            if (isinstance(perm_fun_or_bool, bool) and perm_fun_or_bool) \
                or (hasattr(perm_fun_or_bool, '__call__') and perm_fun_or_bool(request, *args)):
                return self.nodelist_true.render(context)

        if perm_name in permissions.permissions_validators:
            request = context.get('request')
            if permissions.permissions_validators.get(perm_name)(request, *args):
                return self.nodelist_true.render(context)
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
