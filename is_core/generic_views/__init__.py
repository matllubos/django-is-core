from django.views.generic.base import TemplateView

class DefaultViewMixin(object):

    def __init__(self, core, site_name=None, menu_group=None, menu_subgroup=None, model=None):
        self.core = core
        self.site_name = site_name or core.site_name
        self.menu_group = site_name or core.menu_group
        self.menu_subgroup = site_name or core.menu_subgroup
        self.model = site_name or core.model
        super(DefaultViewMixin, self).__init__()

    def get_title(self):
        if self.model:
            return self.model._meta.verbose_name
        return None

    def get_context_data(self, **kwargs):
        context_data = super(DefaultViewMixin, self).get_context_data(**kwargs)
        extra_context_data = {
                                'site_name': self.site_name,
                                'active_menu_group': self.menu_group,
                                'active_menu_subgroup': self.menu_subgroup,
                                'title': self.get_title()
                              }
        extra_context_data.update(context_data)
        return extra_context_data


class HomeView(DefaultViewMixin, TemplateView):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user

        if not user.is_superuser and not user.user_access.filter(account__pk=request.account_pk):
            raise PermissionDenied
        return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_title(self):
        return _('Home')
