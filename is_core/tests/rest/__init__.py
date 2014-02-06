import json

from django.test.testcases import LiveServerTestCase
from django.test.client import Client
from django.utils.encoding import force_text


class RESTTestCase(LiveServerTestCase):

    def setUp(self):
        self.c = Client()
        super(RESTTestCase, self).setUp()
        self.serializer = json

    def get(self, url):
        resp = self.c.get(url)
        return resp

    def put(self, url, data={}, content_type='application/json'):
        if content_type:
            return self.c.put(url, data=data, content_type=content_type)
        else:
            return self.c.put(url, data)

    def post(self, url, data, content_type='application/json'):
        if content_type:
            return self.c.post(url, data=data, content_type=content_type)
        else:
            return self.c.post(url, data)

    def delete(self, url):
        resp = self.c.delete(url)
        return resp

    def assert_http_ok(self, resp):
        return self.assertEqual(resp.status_code, 200)

    def assert_http_created(self, resp):
        return self.assertEqual(resp.status_code, 201)

    def assert_http_accepted(self, resp):
        return self.assertIn(resp.status_code, [202, 204])

    def assert_http_multiple_choices(self, resp):
        return self.assertEqual(resp.status_code, 300)

    def assert_http_see_other(self, resp):
        """
        Ensures the response is returning a HTTP 303.
        """
        return self.assertEqual(resp.status_code, 303)

    def assert_http_not_modified(self, resp):
        """
        Ensures the response is returning a HTTP 304.
        """
        return self.assertEqual(resp.status_code, 304)

    def assert_http_bad_request(self, resp):
        """
        Ensures the response is returning a HTTP 400.
        """
        return self.assertEqual(resp.status_code, 400)

    def assert_http_unauthorized(self, resp):
        """
        Ensures the response is returning a HTTP 401.
        """
        return self.assertEqual(resp.status_code, 401)

    def assert_http_forbidden(self, resp):
        """
        Ensures the response is returning a HTTP 403.
        """
        return self.assertEqual(resp.status_code, 403)

    def assert_http_not_found(self, resp):
        """
        Ensures the response is returning a HTTP 404.
        """
        return self.assertEqual(resp.status_code, 404)

    def assert_http_method_not_allowed(self, resp):
        """
        Ensures the response is returning a HTTP 405.
        """
        return self.assertEqual(resp.status_code, 405)

    def assert_http_conflict(self, resp):
        """
        Ensures the response is returning a HTTP 409.
        """
        return self.assertEqual(resp.status_code, 409)

    def assert_http_gone(self, resp):
        """
        Ensures the response is returning a HTTP 410.
        """
        return self.assertEqual(resp.status_code, 410)

    def assert_http_unprocessable_entity(self, resp):
        """
        Ensures the response is returning a HTTP 422.
        """
        return self.assertEqual(resp.status_code, 422)

    def assert_http_too_many_requests(self, resp):
        """
        Ensures the response is returning a HTTP 429.
        """
        return self.assertEqual(resp.status_code, 429)

    def assert_http_application_error(self, resp):
        """
        Ensures the response is returning a HTTP 500.
        """
        return self.assertEqual(resp.status_code, 500)

    def assert_http_not_implemented(self, resp):
        """
        Ensures the response is returning a HTTP 501.
        """
        return self.assertEqual(resp.status_code, 501)

    def assert_valid_JSON(self, data):
        """
        Given the provided ``data`` as a string, ensures that it is valid JSON &
        can be loaded properly.
        """
        try:
            self.serializer.loads(data)
        except:
            self.fail('Json is not valid')

    def assert_alid_JSON_response(self, resp):
        """
        Given a ``HttpResponse`` coming back from using the ``client``, assert that
        you get back:

        * An HTTP 200
        * The correct content-type (``application/json``)
        * The content is valid JSON
        """
        self.assert_http_ok(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assert_valid_JSON(force_text(resp.content))

    def assert_valid_JSON_created_response(self, resp):
        """
        Given a ``HttpResponse`` coming back from using the ``client``, assert that
        you get back:

        * An HTTP 201
        * The correct content-type (``application/json``)
        * The content is valid JSON
        """
        self.assert_http_created(resp)
        self.assertTrue(resp['Content-Type'].startswith('application/json'))
        self.assert_valid_JSON(force_text(resp.content))

    def deserialize(self, resp):
        """
        Given a ``HttpResponse`` coming back from using the ``client``, this method
        return dict of deserialized json string
        """
        return self.serializer.loads(resp.content)

    def serialize(self, data):
        """
        Given a Python datastructure (typically a ``dict``) & a desired  json,
        this method will return a serialized string of that data.
        """
        return self.serializer.dumps(data)

    def assert_keys(self, data, expected):
        """
        This method ensures that the keys of the ``data`` match up to the keys of
        ``expected``.

        It covers the (extremely) common case where you want to make sure the keys of
        a response match up to what is expected. This is typically less fragile than
        testing the full structure, which can be prone to data changes.
        """
        self.assertEqual(sorted(data.keys()), sorted(expected))
