import re

from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from block_snippets.views import JSONSnippetTemplateResponseMixin

from is_core.menu import LinkMenuItem
from is_core.exceptions import HTTPForbiddenResponseException
from is_core.generic_views.exceptions import GenericViewException
from django.http.response import Http404


class PermissionsViewMixin:

    def dispatch(self, request, *args, **kwargs):
        rm = request.method.lower()
        if rm in self.http_method_names and hasattr(self, rm):
            self._check_permission(rm)
            handler = getattr(self, rm)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def __getattr__(self, name):
        for regex, method in (
                (r'_check_(\w+)_permission', self._check_permission),
                (r'can_call_(\w+)', self._check_call)):
            m = re.match(regex, name)
            if m:
                def _call(*args, **kwargs):
                    return method(m.group(1), *args, **kwargs)
                return _call
        raise AttributeError("%r object has no attribute %r" % (self.__class__, name))

    def _check_call(self, name, *args, **kwargs):
        if not hasattr(self, 'has_%s_permission' % name):
            if settings.DEBUG:
                raise NotImplementedError('Please implement method has_%s_permission to %s' % (name, self.__class__))
            else:
                return False

        try:
            return getattr(self, 'has_%s_permission' % name)(*args, **kwargs)
        except Http404:
            return False

    def _check_permission(self, name, *args, **kwargs):
        if not hasattr(self, 'has_%s_permission' % name):
            if settings.DEBUG:
                raise NotImplementedError('Please implement method has_%s_permission to %s' % (name, self.__class__))
            else:
                raise HTTPForbiddenResponseException

        if not getattr(self, 'has_%s_permission' % name)(*args, **kwargs):
            raise HTTPForbiddenResponseException

    def has_options_permission(self, **kwargs):
        return True


class DefaultViewMixin(PermissionsViewMixin, JSONSnippetTemplateResponseMixin):

    site_name = None
    menu_groups = None
    login_required = True
    allowed_snippets = ('content',)
    view_name = None
    add_current_to_breadcrumbs = True
    kwargs = {}
    args = {}
    title = None
    page_title = None

    def __init__(self):
        super(DefaultViewMixin, self).__init__()

    def get_title(self):
        return self.title

    def get_page_title(self):
        return self.page_title or self.get_title()

    def get_context_data(self, **kwargs):
        context_data = super(DefaultViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
            'site_name': self.site_name,
            'active_menu_groups': self.menu_groups,
            'title': self.get_title(),
            'page_title': self.get_page_title(),
            'view_name': self.view_name,
            'bread_crumbs_menu_items': self.bread_crumbs_menu_items(),
        }
        extra_context_data.update(context_data)
        return extra_context_data

    def bread_crumbs_menu_items(self):
        if self.add_current_to_breadcrumbs:
            return [LinkMenuItem(self.get_title(), self.request.path, active=True)]
        return []


class DefaultCoreViewMixin(DefaultViewMixin):

    core = None
    view_name = None
    title = None

    def __init__(self):
        super(DefaultCoreViewMixin, self).__init__()
        self.site_name = self.core.site_name
        self.menu_groups = self.core.get_menu_groups()

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    def dispatch(self, request, *args, **kwargs):
        self.core.init_ui_request(request)
        return super(DefaultCoreViewMixin, self).dispatch(request, *args, **kwargs)

    def get_title(self):
        return self.title or self.model._meta.verbose_name

    @property
    def view_name(self):
        return '%s-%s' % (self.view_type, '-'.join(self.menu_groups))

    def get_permissions(self):
        return {
            'read': self.core.has_ui_read_permission,
            'create': self.core.has_ui_create_permission,
            'update': self.core.has_ui_update_permission,
            'delete': self.core.has_ui_delete_permission,
        }

    def get_context_data(self, **kwargs):
        context_data = super(DefaultCoreViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
            'permissions': self.get_permissions(),
        }
        extra_context_data.update(context_data)
        return extra_context_data


class DefaultModelCoreViewMixin(DefaultCoreViewMixin):

    model = None

    def __init__(self):
        super(DefaultModelCoreViewMixin, self).__init__()

    @classmethod
    def __init_core__(cls, core, pattern):
        super(DefaultModelCoreViewMixin, cls).__init_core__(core, pattern)
        cls.model = cls.model or core.model

    def get_context_data(self, **kwargs):
        context_data = super(DefaultModelCoreViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
            'core': self.core
        }
        extra_context_data.update(context_data)
        return extra_context_data


class HomeView(DefaultCoreViewMixin, TemplateView):
    template_name = 'is_core/home.html'
    view_name = 'home'

    def get_title(self):
        return _('Home')

    def has_get_permission(self, **kwargs):
        return True
