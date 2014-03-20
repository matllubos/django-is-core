from django.template.base import Node, Library, TemplateSyntaxError

register = Library()


class Permissions(object):
    permissions_validators = {}

    def register_permission_validator(self, name, validator):
        self.permissions_validators[name] = validator

permissions = Permissions()


# TODO: there is possibility cache permissions
class PermissionNode(Node):
    def __init__(self, perm_name, nodelist):
        self.perm_name = perm_name
        self.nodelist = nodelist

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
                return self.nodelist.render(context)

        if permissions.permissions_validators.has_key(perm_name):
            request = context.get('request')
            if permissions.permissions_validators.get(perm_name)(request, **kwargs):
                return self.nodelist.render(context)
        return ''


@register.tag
def has_permission(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise TemplateSyntaxError("%r takes one argument" % bits[0])
    nodelist = parser.parse(('endhas_permission',))
    parser.delete_first_token()
    return PermissionNode(parser.compile_filter(bits[1]), nodelist)
