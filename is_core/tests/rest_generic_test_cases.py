import types

from django.core.urlresolvers import reverse
from django.db.models.fields.files import FieldFile

from germanium.rest import RESTTestCase
from germanium.anotations import login_all, data_provider

from is_core.tests.data_generator_test_case import DataGeneratorTestCase
from is_core.tests.auth_test_cases import RESTAuthMixin
from is_core.forms.forms import SmartBoundField

from piston.utils import model_resources_to_dict


def add_urls_to_resource(resource):

    def get_resource_list_url(self):
        return reverse('%s:api-%s' % (self.core.site_name, self.core.get_menu_group_pattern_name()))

    def get_resource_url(self, pk):
        return reverse('%s:api-resource-%s' % (self.core.site_name, self.core.get_menu_group_pattern_name()), args=(pk,))

    resource._resource_url = types.MethodType(get_resource_url, resource)
    resource._resource_list_url = types.MethodType(get_resource_list_url, resource)
    return resource


@login_all
class TestRESTsAvailability(RESTAuthMixin, DataGeneratorTestCase, RESTTestCase):

    iteration = 5

    @classmethod
    def setUpClass(cls):
        super(TestRESTsAvailability, cls).setUpClass()
        cls.rest_resources = cls.set_up_rest_resources()

    @classmethod
    def set_up_rest_resources(cls):
        # Must be here, because hanlers is not registered
        import urls

        resources_dict = model_resources_to_dict()
        rest_resources = []
        for resource_name, resource in resources_dict.items():
            if cls.get_model_label(resource.model) in cls.factories:
                add_urls_to_resource(resource)
                rest_resources.append((resource_name, resource, resource.model))
            else:
                cls.logger.warning('Model %s has not created factory class' % resource.model)

        return rest_resources

    def get_rest_resources(self):
        return self.rest_resources

    def get_serialized_data(self, request, resource, update=False):
        inst = self.new_instance(resource.model)

        form_class = resource(request)._generate_form_class(inst=update and inst or None)
        form = form_class(initial={'_user': self.logged_user.user, '_request': None}, instance=inst)
        data = {}

        for field in form:
            if not isinstance(field, SmartBoundField) or not field.is_readonly:
                value = field.value()
                if isinstance(value, FieldFile):
                    value = None
                data[field.name] = value

        # Removed instance (must be created because FK)
        inst.delete()

        return self.serialize(data), inst

    @data_provider(get_rest_resources)
    def test_should_return_data_from_resource_list(self, resource_name, resource, model):
        list_url = resource._resource_list_url()

        if not resource(self.get_request_with_user(self.r_factory.get(list_url))).has_get_permission():
            return

        resp = self.get(list_url)
        started_total_count = int(resp['X-Total'])

        for i in range(self.iteration):
            self.new_instance(model)
            resp = self.get(list_url)
            self.assert_valid_JSON_response(resp, 'REST get list of model: %s\n response: %s' % (model, resp))
            self.assertEqual(int(resp['X-Total']) - i, started_total_count + 1)

    @data_provider(get_rest_resources)
    def test_should_return_data_from_resource(self, resource_name, resource, model):
        for _ in range(self.iteration):
            inst = self.new_instance(model)

            url = resource._resource_url(inst.pk)

            if not resource(self.get_request_with_user(self.r_factory.get(url))).has_get_permission(inst):
                break

            resp = self.get(url)
            self.assert_valid_JSON_response(resp, 'REST get of model: %s\n response: %s' % (model, resp))

    @data_provider(get_rest_resources)
    def test_should_delete_data_from_resource(self, resource_name, resource, model):
        for i in range(self.iteration):
            inst = self.new_instance(model)

            url = resource._resource_url(inst.pk)

            if not resource(self.get_request_with_user(self.r_factory.delete(url))).has_delete_permission(inst):
                break

            resp = self.delete(url)
            self.assert_http_accepted(resp, 'REST delete of model: %s\n response: %s' % (model, resp))
            resp = self.get(url)
            self.assert_http_not_found(resp, 'REST get (should not found) of model: %s\n response: %s' %
                                       (model, resp))

    @data_provider(get_rest_resources)
    def test_should_create_data_of_resource(self, resource_name, resource, model):
        for _ in range(self.iteration):
            list_url = resource._resource_list_url()

            request = self.get_request_with_user(self.r_factory.post(list_url))
            if not resource(request).has_post_permission():
                break

            data, inst = self.get_serialized_data(request, resource)

            count_before = model._default_manager.all().count()

            resp = self.post(list_url, data=data)

            count_after = model._default_manager.all().count()
            self.assert_valid_JSON_created_response(resp, 'REST create of model: %s\n response: %s' % (model, resp))
            self.assertEqual(count_before + 1, count_after)

    @data_provider(get_rest_resources)
    def test_should_update_data_of_resource(self, resource_name, resource, model):
        for _ in range(self.iteration):
            inst_from = self.new_instance(model)

            url = resource._resource_url(inst_from.pk)

            request = self.get_request_with_user(self.r_factory.put(url))

            if not resource(request).has_put_permission(inst_from):
                break

            data, _ = self.get_serialized_data(request, resource, True)

            resp = self.put(url, data=data)
            self.assert_valid_JSON_response(resp, 'REST update of model: %s\n response: %s' % (model, resp))
