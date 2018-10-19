from functools import wraps

from urllib.parse import urlunparse, urlparse

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import QueryDict
from django.utils.functional import cached_property
from django.urls import reverse
from django.http import Http404

from block_snippets.views import JSONSnippetTemplateResponseMixin

from chamber.shortcuts import get_object_or_404

from is_core.auth.permissions import PermissionsSet, CoreReadAllowed
from is_core.menu import LinkMenuItem
from is_core.patterns import reverse_pattern
from is_core.exceptions import (
    HTTPForbiddenResponseException, HTTPUnauthorizedResponseException, HTTPRedirectResponseException
)

from .exceptions import GenericViewException


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


def cached_method(func):
    @wraps(func)
    def wrapper(self, cached=True):
        cached_name = '_cached_{}'.format(func.__name__)
        cached_value = getattr(self, cached_name, None)
        if cached and cached_value is not None:
            return cached_value
        value = func(self)
        if value and cached_value is None:
            setattr(self, cached_name, value)
        return value
    return wrapper


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

    @classmethod
    def __init_core__(cls, core, pattern):
        super().__init_core__(core, pattern)
        cls.model = cls.model or core.model

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        extra_context_data = {
            'core': self.core
        }
        extra_context_data.update(context_data)
        return extra_context_data


class ListParentMixin:

    def list_bread_crumbs_menu_item(self):
        from is_core.menu import LinkMenuItem

        list_pattern = self.core.ui_patterns.get('list')
        list_view = list_pattern.get_view(self.request)
        return LinkMenuItem(self.model._ui_meta.list_verbose_name %
                            {'verbose_name': list_view.model._meta.verbose_name,
                             'verbose_name_plural': list_view.model._meta.verbose_name_plural},
                             list_pattern.get_url_string(self.request),
                             active=not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = []
        if 'list' in self.core.ui_patterns and self.core.ui_patterns.get('list').has_permission('get', self.request):
            menu_items.append(self.list_bread_crumbs_menu_item())
        return menu_items

    def bread_crumbs_menu_items(self):
        return self.parent_bread_crumbs_menu_items() + super(ListParentMixin, self).bread_crumbs_menu_items()


class DetailParentMixin(ListParentMixin):

    def edit_bread_crumbs_menu_item(self):
        from is_core.menu import LinkMenuItem

        detail_pattern = self.core.ui_patterns.get('detail')
        detail_view = detail_pattern.get_view(self.request)
        parent_obj = self.get_parent_obj()
        if not isinstance(parent_obj, detail_view.model):
            raise GenericViewException('Parent obj must be instance of edit view model')

        return LinkMenuItem(self.model._ui_meta.detail_verbose_name %
                            {'verbose_name': detail_view.model._meta.verbose_name,
                             'verbose_name_plural': detail_view.model._meta.verbose_name_plural,
                             'obj': parent_obj},
                            detail_pattern.get_url_string(self.request, view_kwargs={'pk': parent_obj.pk}),
                             active=not self.add_current_to_breadcrumbs)

    def parent_bread_crumbs_menu_items(self):
        menu_items = super().parent_bread_crumbs_menu_items()
        if ('detail' in self.core.ui_patterns and
              self.core.ui_patterns.get('detail').has_permission('get', self.request, obj=self.get_obj())):
            menu_items.append(self.edit_bread_crumbs_menu_item())
        return menu_items

    def get_parent_obj(self):
        return self.get_obj()


class TabItem:

    def __init__(self, pattern_name, label, can_show=None, is_active=None, pattern_kwargs=None,
                 is_active_starts_with=True):
        self._pattern_name = pattern_name
        self._label = label
        self._is_active = is_active
        self._pattern_kwargs = pattern_kwargs
        self._can_show = can_show
        self._is_active_starts_with = is_active_starts_with

    @cached_property
    def pattern(self):
        pattern = reverse_pattern(self._pattern_name)
        assert pattern is not None, 'Invalid pattern name {} in TabItem'.format(self._pattern_name)
        return pattern

    def get_pattern_kwargs(self, view):
        pattern_kwargs = self._pattern_kwargs or {}
        return pattern_kwargs(view) if hasattr(pattern_kwargs, '__call__') else pattern_kwargs

    def can_show(self, view):
        can_show = self._can_show
        if can_show is not None:
            return can_show(view) if hasattr(can_show, '__call__') else can_show
        else:
            return self.pattern.has_permission('get', view.request, view_kwargs=self.get_pattern_kwargs(view))

    def get_url(self, view):
        return self.pattern.get_url_string(view.request, view_kwargs=self.get_pattern_kwargs(view))

    def is_active(self, view):
        is_active = self._is_active
        if is_active is not None:
            return is_active(view) if hasattr(is_active, '__call__') else is_active
        else:
            return (
                (self._is_active_starts_with and view.request.path.startswith(self.get_url(view))) or
                (not self._is_active_starts_with and view.request.path == self.get_url(view))
            )

    def get_menu_link_item_or_none(self, view):
        from is_core.menu import LinkMenuItem

        return LinkMenuItem(
            self._label, self.get_url(view), active=self.is_active(view)) if self.can_show(view) else None


class TabsViewMixin:

    tabs = ()

    def get_tabs(self):
        return self.tabs

    def get_tab_menu_items(self):
        return [tab.get_menu_link_item_or_none(self) for tab in self.get_tabs() if tab.can_show(self)]

    def get_context_data(self, **kwargs):
        context_data = super(TabsViewMixin, self).get_context_data(**kwargs)
        context_data.update({
            'tabs': self.get_tab_menu_items(),
        })
        return context_data


class GetObjViewMixin:

    pk_name = 'pk'
    model = None

    def get_obj_filters(self):
        filters = {'pk': self.kwargs.get(self.pk_name)}
        return filters

    def _has_permission(self, name, obj=None):
        obj = obj or self.get_obj()

        return super()._has_permission(name, obj=obj)

    @cached_method
    def get_obj(self):
        return get_object_or_404(self.model, self.get_obj_filters())

    def get_obj_or_none(self, cached=True):
        try:
            return self.get_obj()
        except Http404:
            return None


class CoreGetObjViewMixin(GetObjViewMixin):

    @cached_method
    def get_obj(self):
        return self.core.get_obj(self.request, **self.get_obj_filters())
