from django.views.generic.base import TemplateView, View
from django.utils.translation import ugettext_lazy as _

from .mixins import DefaultCoreViewMixin


class HomeView(DefaultCoreViewMixin, TemplateView):

    template_name = 'is_core/home.html'
    view_name = 'home'

    def get_title(self):
        return _('Home')
