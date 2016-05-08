from django.core.urlresolvers import reverse

from germanium.client import ClientTestCase
from germanium.anotations import login_all, data_provider

from is_core.tests.data_generator_test_case import DataGeneratorTestCase


class ModelUITestCaseMiddleware(DataGeneratorTestCase):

    add_disabled_views = ()
    edit_disabled_views = ()
    list_disabled_views = ()

    @classmethod
    def setUpClass(cls):
        super(ModelUITestCaseMiddleware, cls).setUpClass()
        cls.ui_main_views = cls.set_up_main_views()

    @classmethod
    def set_up_main_views(cls):
        # Must be here, because hanlers is not registered
        import urls
        from is_core.site import registered_model_cores
        from is_core.main import UIRESTModelISCore

        ui_main_views = []
        for main_view in [model_view for model_view in registered_model_cores.values() if isinstance(model_view,
                                                                                                     UIRESTModelISCore)]:
            model = main_view.model
            if cls.get_model_label(model) in cls.factories:
                ui_main_views.append((main_view, model))
            else:
                cls.logger.warning('Model %s has not created factory class' % model)

        return ui_main_views

    def list_url(self, site_name, menu_groups):
        return reverse('%s:list-%s' % (site_name, '-'.join(menu_groups)))

    def add_url(self, site_name, menu_groups):
        return reverse('%s:add-%s' % (site_name, '-'.join(menu_groups)))

    def edit_url(self, site_name, menu_groups, obj):
        return reverse('%s:edit-%s' % (site_name, '-'.join(menu_groups)), args=(obj.pk,))

    def view_name(self, model_view):
        return '%s-%s' % (model_view.site_name, '-'.join(model_view.get_menu_groups()))


@login_all
class TestSiteAvailability(ModelUITestCaseMiddleware, ClientTestCase):

    def get_ui_main_views(self):
        return self.ui_main_views

    @data_provider(get_ui_main_views)
    def test_should_return_right_list_page_for_all_model_views(self, model_view, model):

        if 'list' in model_view.ui_patterns:
            url = self.list_url(model_view.site_name, model_view.get_menu_groups())
            if model_view.has_ui_read_permission(self.get_request_with_user(self.r_factory.get(url))):
                self.assert_http_ok(self.get(url), '%s should return 200' % url)

    @data_provider(get_ui_main_views)
    def test_should_return_right_add_page_for_all_model_view(self, model_view, model):

        if 'add' in model_view.ui_patterns:
            url = self.add_url(model_view.site_name, model_view.get_menu_groups())
            if model_view.has_ui_create_permission(self.get_request_with_user(self.r_factory.get(url))):
                self.assert_http_ok(self.get(url), '%s should return 200' % url)

    @data_provider(get_ui_main_views)
    def test_should_return_right_edit_page_for_all_model_view(self, model_view, model):

        if 'edit' in model_view.ui_patterns:
            inst = self.new_instance(model)

            url = self.edit_url(model_view.site_name, model_view.get_menu_groups(), inst)
            request = self.get_request_with_user(self.r_factory.get(url))
            if model_view.has_ui_read_permission(request, inst) or model_view.has_ui_update_permission(request, inst.pk):
                self.assert_http_ok(self.get(url), '%s should return 200' % url)
