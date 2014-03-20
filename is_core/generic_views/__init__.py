from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

from is_core.auth import AuthWrapper

from block_snippets.views import JsonSnippetTemplateResponseMixin


class DefaultViewMixin(JsonSnippetTemplateResponseMixin):

    site_name = None
    menu_groups = None
    login_required = True
    allowed_snippets = ('content',)
    view_name = None

    def __init__(self, site_name=None, menu_groups=None):
        super(DefaultViewMixin, self).__init__()
        self.site_name = self.site_name or site_name
        self.menu_groups = self.menu_groups or menu_groups

    def get_title(self):
        return None

    def get_context_data(self, **kwargs):
        context_data = super(DefaultViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
                                'site_name': self.site_name,
                                'active_menu_groups': self.menu_groups,
                                'title': self.get_title(),
                                'view_name': self.view_name,
                                'bread_crumbs_menu_items': self.bread_crumbs_menu_items()
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
    def as_wrapped_view(cls, **initkwargs):
        return AuthWrapper(cls.get_permission_validators(), **initkwargs).wrap(cls.as_view(**initkwargs))

    def bread_crumbs_menu_items(self):
        return []


class HomeView(DefaultViewMixin, TemplateView):
    template_name = 'home.html'
    view_name = 'home'

    def get_title(self):
        return _('Home')


class DefaultCoreViewMixin(DefaultViewMixin):

    core = None
    model = None
    view_name = None
    title = None

    def __init__(self, core, site_name=None, menu_groups=None, model=None):
        self.core = core
        self.model = self.model or model or core.model
        site_name = self.site_name or site_name or core.site_name
        menu_groups = self.menu_groups or menu_groups or core.get_menu_groups()
        super(DefaultCoreViewMixin, self).__init__(site_name, menu_groups)

    def get_title(self):
        return self.title or self.model._meta.verbose_name

    @property
    def view_name(self):
        return '%s-%s' % (self.view_type, '-'.join(self.menu_groups))

    def get_permissions(self):
        return {
                    'read': self.core.has_read_permission,
                    'create': self.core.has_create_permission,
                    'update': self.core.has_update_permission,
                    'delete': self.core.has_delete_permission,
                }

    def get_context_data(self, **kwargs):
        context_data = super(DefaultCoreViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
                                'permissions': self.get_permissions(),
                              }
        extra_context_data.update(context_data)
        return extra_context_data
