from six.moves.urllib.parse import urlencode

from germanium.rest import RESTTestCase

from is_core.tests.auth_test_cases import RESTAuthMixin

from germanium.anotations import login

from .test_case import HelperTestCase, AsSuperuserTestCase


class RESTOrderingAndFilteringTestCase(AsSuperuserTestCase, RESTAuthMixin, HelperTestCase, RESTTestCase):
    USER_API_URL = '/api/user/'

    @login(is_superuser=True)
    def test_user_headers_ordering_by_id(self):
        [self.get_user_obj() for _ in range(10)]

        headers = {'HTTP_X_ORDER': 'id'}
        resp = self.get(self.USER_API_URL, headers=headers)
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        pk_list = [obj.get('id') for obj in output]
        self.assert_true(all(pk_list[i] < pk_list[i + 1] for i in range(len(pk_list) - 1)))

        headers = {'HTTP_X_ORDER': '-id'}
        resp = self.get(self.USER_API_URL, headers=headers)
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        pk_list = [obj.get('id') for obj in output]
        self.assert_true(all(pk_list[i] > pk_list[i + 1] for i in range(len(pk_list) - 1)))

    @login(is_superuser=True)
    def test_user_querystring_ordering_by_id(self):
        [self.get_user_obj() for _ in range(10)]

        querystring = {'_order': 'id'}
        resp = self.get('%s?%s' % (self.USER_API_URL, urlencode(querystring)))
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        pk_list = [obj.get('id') for obj in output]
        self.assert_true(all(pk_list[i] < pk_list[i + 1] for i in range(len(pk_list) - 1)))

        querystring = {'_order': '-id'}
        resp = self.get('%s?%s' % (self.USER_API_URL, urlencode(querystring)))
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        pk_list = [obj.get('id') for obj in output]
        self.assert_true(all(pk_list[i] > pk_list[i + 1] for i in range(len(pk_list) - 1)))

    @login(is_superuser=True)
    def test_user_filtering_by_id(self):
        users = [self.get_user_obj() for _ in range(10)]

        resp = self.get('%s?id=%s' % (self.USER_API_URL, users[0].pk))
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_true(len(output), 1)
        self.assert_true(output[0]['id'], 1)

        resp = self.get('%s?id__lt=%s' % (self.USER_API_URL, users[2].pk))
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_true(len(output), 2)

        resp = self.get('%s?id__lte=%s' % (self.USER_API_URL, users[2].pk))
        self.assert_valid_JSON_response(resp)
        output = self.deserialize(resp)
        self.assert_true(len(output), 3)
