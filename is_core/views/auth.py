from django.contrib.auth.views import LoginView as _LoginView, LogoutView as _LogoutView


class LoginView(_LoginView):

    template_name = 'is_core/login.html'


class LogoutView(_LoginView):

    template_name = 'is_core/logged_out.html'
