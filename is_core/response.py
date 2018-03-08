import json

from django.http.response import HttpResponse


class JsonHttpResponse(HttpResponse):
    status_code = 200

    def __init__(self, content=None, *args, **kwargs):
        super(HttpResponse, self).__init__(content_type='application/json', *args, **kwargs)
        self.content = json.dumps(content)


class JsonCreatedHttpResponse(JsonHttpResponse):
    status_code = 201
