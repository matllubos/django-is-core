from django.urls.resolvers import get_resolver

from germanium.test_cases.client import ClientTestCase
from germanium.annotations import login_all, data_provider
from germanium.tools.http import assert_http_ok

from is_core.tests.data_generator_test_case import DataGeneratorTestCase
from is_core.utils.compatibility import reverse


class ModelUITestCaseMiddleware(DataGeneratorTestCase):

    add_disabled_views = ()
    edit_disabled_views = ()
    list_disabled_views = ()
    ignore_warnings = False

    @classmethod
    def setUpClass(cls):
        super(ModelUITestCaseMiddleware, cls).setUpClass()
        cls.ui_main_views = cls.set_up_main_views()

    @classmethod
    def set_up_main_views(cls):
        from is_core.site import registered_model_cores
        from is_core.main import UIRESTModelISCore

        # Must be here, because hanlers is not registered
        get_resolver().url_patterns

        ui_main_views = []
        for main_view in [model_view for model_view in registered_model_cores.values()
                          if isinstance(model_view, UIRESTModelISCore)]:
            model = main_view.model
            if cls.get_model_label(model) in cls.factories:
                ui_main_views.append((main_view, model))
            elif not cls.ignore_warnings:
                cls.logger.warning('Model {} has not created factory class'.format(model))

        return ui_main_views

    def list_url(self, site_name, menu_groups):
        return reverse('{}:list-{}'.format(site_name, '-'.join(menu_groups)))

    def add_url(self, site_name, menu_groups):
        return reverse('{}:add-{}'.format(site_name, '-'.join(menu_groups)))

    def detail_url(self, site_name, menu_groups, obj):
        return reverse('{}:detail-{}'.format(site_name, '-'.join(menu_groups)), args=(obj.pk,))

    def view_name(self, model_view):
        return '{}-{}'.format(model_view.site_name, '-'.join(model_view.get_menu_groups()))


@login_all
class TestSiteAvailability(ModelUITestCaseMiddleware, ClientTestCase):

    def get_ui_main_views(self):
        return self.ui_main_views

    @data_provider(get_ui_main_views)
    def test_should_return_right_list_page_for_all_model_views(self, model_view, model):

        if 'list' in model_view.ui_patterns:
            url = self.list_url(model_view.site_name, model_view.get_menu_groups())
            if model_view.ui_patterns.get('list').has_permission('get',
                                                                 self.get_request_with_user(self.r_factory.get(url))):
                assert_http_ok(self.get(url), '{} should return 200'.format(url))

    @data_provider(get_ui_main_views)
    def test_should_return_right_add_page_for_all_model_view(self, model_view, model):

        if 'add' in model_view.ui_patterns:
            url = self.add_url(model_view.site_name, model_view.get_menu_groups())
            if model_view.ui_patterns.get('add').has_permission('get',
                                                                self.get_request_with_user(self.r_factory.get(url))):
                assert_http_ok(self.get(url), '{} should return 200'.format(url))

    @data_provider(get_ui_main_views)
    def test_should_return_right_edit_page_for_all_model_view(self, model_view, model):

        if 'detail' in model_view.ui_patterns:
            inst = self.new_instance(model)

            url = self.detail_url(model_view.site_name, model_view.get_menu_groups(), inst)
            request = self.get_request_with_user(self.r_factory.get(url))
            if model_view.ui_patterns.get('detail').has_permission('get', request, obj=inst):
                assert_http_ok(self.get(url), '{} should return 200'.format(url))
