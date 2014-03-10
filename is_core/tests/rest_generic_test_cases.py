import types

from django.core.urlresolvers import reverse
from django.db.models.fields.files import FieldFile

from germanium.rest import RESTTestCase
from germanium.anotations import login_all, data_provider

from is_core.tests.data_generator_test_case import DataGeneratorTestCase
from is_core.rest.utils import model_handlers_to_dict
from is_core.tests.auth_test_cases import RestAuthMixin


def add_urls_to_handler(handler):
    def get_handler_list_url(self):
        return reverse('%s:api-%s' % (self.site_name, self.core.get_menu_group_pattern_name()))

    def get_handler_url(self, pk):
        return reverse('%s:api-resource-%s' % (self.site_name, self.core.get_menu_group_pattern_name()), args=(pk,))
    handler.url = types.MethodType(get_handler_url, handler)
    handler.list_url = types.MethodType(get_handler_list_url, handler)
    return handler


@login_all
class TestRestsAvailability(RestAuthMixin, DataGeneratorTestCase, RESTTestCase):

    iteration = 10

    @classmethod
    def setUpClass(cls):
        super(TestRestsAvailability, cls).setUpClass()
        cls.rest_handlers = cls.set_up_rest_handlers()

    @classmethod
    def set_up_rest_handlers(cls):
        # Must be here, because hanlers is not registered
        from is_core import site

        handlers_dict = model_handlers_to_dict()
        rest_handlers = []
        for handler_name, handler in handlers_dict.items():
            if cls.get_model_label(handler.model) in cls.factories:
                add_urls_to_handler(handler)
                rest_handlers.append((handler_name, handler, handler.model))
            else:
                cls.logger.warning('Model %s has not created factory class' % handler.model)

        return rest_handlers

    def get_rest_handlers(self):
        return self.rest_handlers

    def get_serialized_data(self, handler):
        inst = self.new_instance(handler.model)

        form = handler().get_form(inst=inst, initial={'_user': self.logged_user.user})

        data = {}

        for field in form:
            value = field.value()

            field.name
            if isinstance(value, FieldFile):
                value = None

            data[field.name] = value

        # Removed instance (must be created because FK)
        inst.delete()

        return self.serialize(data), inst

    @data_provider(get_rest_handlers)
    def test_should_return_data_from_resource_list(self, handler_name, handler, model):
        list_url = handler.list_url()

        if not handler.has_read_permission(self.get_request_with_user(self.r_factory.get(list_url))):
            return

            resp = self.get(list_url)
            started_total_count = int(resp['X-Total'])

            for i in range(self.iteration):
                self.new_instance(model)

                self.assert_valid_JSON_response(resp, 'REST get list of model: %s\n response: %s' % (model, resp))
                self.assertEqual(int(resp['X-Total']) - i, started_total_count + 1)

    @data_provider(get_rest_handlers)
    def test_should_return_data_from_resource(self, handler_name, handler, model):
        for _ in range(self.iteration):
            inst = self.new_instance(model)

            url = handler.url(inst.pk)

            if not handler.has_read_permission(self.get_request_with_user(self.r_factory.get(url)), pk=inst.pk):
                break

            resp = self.get(url)
            self.assert_valid_JSON_response(resp, 'REST get of model: %s\n response: %s' % (model, resp))

    @data_provider(get_rest_handlers)
    def test_should_delete_data_from_resource(self, handler_name, handler, model):
        for _ in range(self.iteration):
            inst = self.new_instance(model)

            url = handler.url(inst.pk)

            if not handler.has_delete_permission(self.get_request_with_user(self.r_factory.delete(url)), pk=inst.pk):
                break

            resp = self.delete(url)
            self.assert_http_accepted(resp, 'REST delete of model: %s\n response: %s' % (model, resp))
            resp = self.get(url)
            self.assert_http_not_found(self.get(url), 'REST get (should not found) of model: %s\n response: %s' %
                                       (model, resp))

    @data_provider(get_rest_handlers)
    def test_should_create_data_of_resource(self, handler_name, handler, model):
        for _ in range(self.iteration):
            list_url = handler.list_url()

            if not handler.has_create_permission(self.get_request_with_user(self.r_factory.post(list_url))):
                break

            data, inst = self.get_serialized_data(handler)

            count_before = model._default_manager.all().count()

            resp = self.post(list_url, data=data)

            count_after = model._default_manager.all().count()
            self.assert_valid_JSON_created_response(resp, 'REST create of model: %s\n response: %s' % (model, resp))
            self.assertEqual(count_before + 1, count_after)

    @data_provider(get_rest_handlers)
    def test_should_update_data_of_resource(self, handler_name, handler, model):
        for _ in range(self.iteration):
            inst_from = self.new_instance(model)

            url = handler.url(inst_from.pk)

            request = self.get_request_with_user(self.r_factory.put(url))

            if not handler.has_update_permission(request, pk=inst_from.pk):
                break

            data, inst_to = self.get_serialized_data(handler)

            resp = self.put(url, data=data)
            self.assert_valid_JSON_response(resp, 'REST update of model: %s\n response: %s' % (model, resp))
