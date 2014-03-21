from __future__ import unicode_literals

import json

from django.http.response import HttpResponse


class JsonCreatedHttpResponse(HttpResponse):
    status_code = 201

    def __init__(self, content=None, *args, **kwargs):
        super(HttpResponse, self).__init__(content_type='application/json', *args, **kwargs)
        self.content = json.dumps(content)
