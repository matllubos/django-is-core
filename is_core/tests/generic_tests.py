from django.core.urlresolvers import reverse

from is_core.main import UIModelISCore

from germanium.client import ClientTestCase


class ModelViewSeleniumTestCaseMiddleware(object):

    add_disabled_views = ()
    edit_disabled_views = ()
    list_disabled_views = ()

    def get_model_main_views(self):
        from is_core.site import registered_model_views
        return [model_view for model_view in registered_model_views.values() if isinstance(model_view, UIModelISCore)]

    def list_url(self, site_name, menu_groups):
        return reverse('%s:list-%s' % (site_name, '-'.join(menu_groups)))

    def add_url(self, site_name, menu_groups):
        return reverse('%s:add-%s' % (site_name, '-'.join(menu_groups)))

    def edit_url(self, site_name, menu_groups, obj):
        return reverse('%s:edit-%s' % (site_name, '-'.join(menu_groups)), args=(obj.pk,))

    def view_name(self, model_view):
        return '%s-%s' % (model_view.site_name, '-'.join(model_view.get_menu_groups()))


class AsUserTestCase(object):

    def setUp(self):
        super(AsUserTestCase, self).setUp()
        self.login(self.get_user())


class TestSiteAvailability(ModelViewSeleniumTestCaseMiddleware, AsUserTestCase, ClientTestCase):

    def test_should_return_right_list_page_for_all_model_views(self):

        for model_view in self.get_model_main_views():
            if self.view_name(model_view) not in self.list_disabled_views:
                url = self.list_url(model_view.site_name, model_view.get_menu_groups())
                self.assert_http_ok(self.get(url), '%s should return 200' % url)

    def test_should_return_right_add_page_for_all_model_view(self):

        for model_view in self.get_model_main_views():
            if self.view_name(model_view) not in self.add_disabled_views:
                url = self.add_url(model_view.site_name, model_view.get_menu_groups())
                self.assert_http_ok(self.get(url), '%s should return 200' % url)

    def test_should_return_right_edit_page_for_all_model_view(self):

        for model_view in self.get_model_main_views():
            if self.view_name(model_view) not in self.edit_disabled_views:
                obj_list = model_view.model.objects.all()
                if obj_list:
                    obj = obj_list[0]
                    url = self.edit_url(model_view.site_name, model_view.get_menu_groups(), obj)
                    self.assert_http_ok(self.get(url), '%s should return 200' % url)
