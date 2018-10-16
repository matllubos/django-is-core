import re

from urllib.parse import urlunparse, urlparse

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import QueryDict
from django.http.response import Http404
from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.urls import reverse

from block_snippets.views import JSONSnippetTemplateResponseMixin

from is_core.auth.permissions import PermissionsSet, CoreReadAllowed
from is_core.menu import LinkMenuItem
from is_core.exceptions import (
    HTTPForbiddenResponseException, HTTPUnauthorizedResponseException, HTTPRedirectResponseException
)
from is_core.generic_views.exceptions import GenericViewException


def redirect_to_login(next, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirects the user to the login page, passing the given 'next' page
    """
    resolved_url = reverse('IS:login')

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    raise HTTPRedirectResponseException(urlunparse(login_url_parts))


class PermissionsViewMixin:

    permission = None

    auto_login_redirect = True

    def __init__(self):
        super().__init__()
        assert self.permission, 'Permissions must be set'

    def dispatch(self, request, *args, **kwargs):
        rm = request.method.lower()
        if rm in self.http_method_names and hasattr(self, rm):
            self._check_permission(rm)
            handler = getattr(self, rm)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)

    def has_permission(self, name, obj=None):
        return self.permission.has_permission(name, self.request, self, obj)

    def _check_permission(self, name, obj=None):
        if not self.has_permission(name, obj):
            if not self.request.user or not self.request.user.is_authenticated:
                if self.auto_login_redirect:
                    redirect_to_login(self.request.get_full_path())
                else:
                    raise HTTPUnauthorizedResponseException
            else:
                raise HTTPForbiddenResponseException


class DefaultViewMixin(PermissionsViewMixin, JSONSnippetTemplateResponseMixin):

    site_name = None
    menu_groups = None
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
    permission = PermissionsSet(
        get=CoreReadAllowed()
    )

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

    def get_context_data(self, **kwargs):
        context_data = super(DefaultCoreViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
            'core_permission': self.core.permission,
            'permission': self.permission,
            'view': self
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
