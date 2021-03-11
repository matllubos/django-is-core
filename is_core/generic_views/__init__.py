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

from is_core.auth.permissions import PermissionsSet, CoreReadAllowed, CoreAllowed, DEFAULT_PERMISSION
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
        # For core obj view mixin is object required to check permissions. If no object is found False is returned.
        try:
            return self._has_permission(name, obj)
        except Http404:
            return False

    def _has_permission(self, name, obj=None):
        return self.permission.has_permission(name, self.request, self, obj)

    def _check_permission(self, name, obj=None):
        """
        If customer is not authorized he should not get information that object is exists.
        Therefore 403 is returned if object was not found or is redirected to the login page.
        If custmer is authorized and object was not found is returned 404.
        If object was found and user is not authorized is returned 403 or redirect to login page.
        If object was found and user is authorized is returned 403 or 200 according of result of _has_permission method.
        """
        def redirect_or_exception(ex):
            if not self.request.user or not self.request.user.is_authenticated:
                if self.auto_login_redirect:
                    redirect_to_login(self.request.get_full_path())
                else:
                    raise HTTPUnauthorizedResponseException
            else:
                raise ex

        try:
            if not self._has_permission(name, obj):
                redirect_or_exception(HTTPForbiddenResponseException)
        except Http404 as ex:
            redirect_or_exception(ex)


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
    view_type = None
    title = None
    permission = PermissionsSet(
        get=CoreReadAllowed(),
        **{
            DEFAULT_PERMISSION: CoreAllowed(),
        }
    )

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern
        cls.site_name = core.site_name
        cls.menu_groups = core.get_menu_groups()

    def dispatch(self, request, *args, **kwargs):
        self.core.init_ui_request(request)
        return super(DefaultCoreViewMixin, self).dispatch(request, *args, **kwargs)

    def get_title(self):
        return self.title

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

    @property
    def verbose_name(self):
        return self.core.verbose_name

    @property
    def verbose_name_plural(self):
        return self.core.verbose_name_plural

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

    def get_title(self):
        return self.title or self.verbose_name


class HomeView(DefaultCoreViewMixin, TemplateView):

    template_name = 'is_core/home.html'
    view_name = 'home'

    def get_title(self):
        return _('Home')
