from __future__ import unicode_literals

from django.template.base import Node, Library, TemplateSyntaxError, NodeList
from django.template.defaulttags import IfNode

register = Library()


class Permissions(object):
    permissions_validators = {}

    def register_permission_validator(self, name, validator):
        self.permissions_validators[name] = validator

permissions = Permissions()

IfNode

# TODO: there is possibility cache permissions
class PermissionNode(Node):
    def __init__(self, perm_name, nodelist_true, nodelist_false):
        self.perm_name = perm_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        perm_name = self.perm_name.resolve(context, True)
        request = context.get('request')
        kwargs = {}
        if request.kwargs.has_key('pk'):
            kwargs['pk'] = request.kwargs['pk']

        view_permissions = context.get('permissions', {})

        if view_permissions.has_key(perm_name):
            perm_fun_or_bool = view_permissions.get(perm_name)
            if (isinstance(perm_fun_or_bool, bool) and perm_fun_or_bool) \
                or (hasattr(perm_fun_or_bool, '__call__') and perm_fun_or_bool(request, **kwargs)):
                return self.nodelist_true.render(context)

        if permissions.permissions_validators.has_key(perm_name):
            request = context.get('request')
            if permissions.permissions_validators.get(perm_name)(request, **kwargs):
                return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


@register.tag
def has_permission(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise TemplateSyntaxError("%r takes one argument" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return PermissionNode(parser.compile_filter(bits[1]), nodelist_true, nodelist_false)
