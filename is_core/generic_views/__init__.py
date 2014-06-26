from __future__ import unicode_literals

from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from is_core.auth import AuthWrapper
from is_core.menu import LinkMenuItem

from block_snippets.views import JsonSnippetTemplateResponseMixin


class DefaultViewMixin(JsonSnippetTemplateResponseMixin):

    site_name = None
    menu_groups = None
    login_required = True
    allowed_snippets = ('content',)
    view_name = None
    add_current_to_breadcrumbs = True

    def __init__(self):
        super(DefaultViewMixin, self).__init__()

    def get_title(self):
        return None

    def get_context_data(self, **kwargs):
        context_data = super(DefaultViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
                                'site_name': self.site_name,
                                'active_menu_groups': self.menu_groups,
                                'title': self.get_title(),
                                'view_name': self.view_name,
                                'bread_crumbs_menu_items': self.bread_crumbs_menu_items(),
                              }
        extra_context_data.update(context_data)
        return extra_context_data

    @classmethod
    def get_permission_validators(cls):
        return {
                    'GET': cls.has_get_permission,
                    'POST': cls.has_post_permission,
                }

    @classmethod
    def has_get_permission(cls, request, **kwargs):
        return True

    @classmethod
    def has_post_permission(cls, request, **kwargs):
        return False

    @classmethod
    def as_wrapped_view(cls, allowed_methods=None, **initkwargs):
        return AuthWrapper(cls.get_permission_validators(), **initkwargs).wrap(cls.as_view(**initkwargs))

    def bread_crumbs_menu_items(self):
        if self.add_current_to_breadcrumbs:
            return [LinkMenuItem(self.get_title(), self.request.path, True)]
        return []


class DefaultCoreViewMixin(DefaultViewMixin):

    core = None
    view_name = None
    title = None

    def __init__(self):
        super(DefaultCoreViewMixin, self).__init__()
        self.site_name = self.core.site_name
        self.menu_groups = self.core.get_menu_groups()

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

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern


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
    template_name = 'home.html'
    view_name = 'home'

    def get_title(self):
        return _('Home')
