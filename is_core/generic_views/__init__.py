from django.views.generic.base import TemplateView
from django.utils.translation import ugettext_lazy as _

class DefaultViewMixin(object):

    site_name = None
    menu_group = None
    menu_subgroup = None

    def __init__(self, site_name=None, menu_group=None, menu_subgroup=None):
        super(DefaultViewMixin, self).__init__()
        self.site_name = site_name
        self.menu_group = menu_group
        self.menu_subgroup = menu_subgroup

    def get_title(self):
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

    def get_title(self):
        return _('Home')


class DefaultCoreViewMixin(DefaultViewMixin):

    core = None
    model = None

    def __init__(self, core, site_name=None, menu_group=None, menu_subgroup=None, model=None):
        self.core = core
        self.model = model or core.model
        site_name = site_name or core.site_name
        menu_group = menu_group or core.menu_group
        menu_subgroup = menu_subgroup or core.menu_subgroup
        super(DefaultCoreViewMixin, self).__init__(site_name, menu_group, menu_subgroup, menu_subgroup)

    def get_title(self):
        return self.model._meta.verbose_name
