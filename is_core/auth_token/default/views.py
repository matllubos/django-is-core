from django.http.response import HttpResponseRedirect
from django.views.generic.base import RedirectView

from is_core.config import settings
from is_core.generic_views import DefaultCoreViewMixin
from is_core.generic_views.mixins import GetCoreObjViewMixin
from is_core.generic_views.auth_views import LogoutView, LoginView
from is_core.auth_token.utils import login, logout, takeover
from is_core.auth_token.forms import TokenAuthenticationForm


class TokenLoginView(LoginView):

    form_class = TokenAuthenticationForm

    def _login(self, user, expiration, form):
        login(self.request, user, expiration)

    def dispatch(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        return super(TokenLoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        The user has provided valid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        can check the test cookie stuff and log him in.
        """
        self.check_and_delete_test_cookie()
        self._login(form.get_user(), not form.is_permanent(), form)
        return super(TokenLoginView, self).form_valid(form)


class TokenLogoutView(LogoutView):

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super(LogoutView, self).get(*args, **kwargs)


class UserTakeover(GetCoreObjViewMixin, DefaultCoreViewMixin, RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return settings.AUTH_TAKEOVER_REDIRECT_URL

    def get(self, request, *args, **kwargs):
        user = self.get_obj()
        takeover(self.request, user)
        return super(UserTakeover, self).get(request, *args, **kwargs)

    def has_get_permission(self, *args, **kwargs):
        return self.request.user.is_superuser
