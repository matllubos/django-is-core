from django.conf import settings
from django.middleware import csrf

from pyston.serializer import serialize


def is_js_dev(req):
    return {'JS_DEV': settings.JS_DEV}


def initial_data(request):
    return {
        'initial_data': serialize({
            'net': {
                'csrf-token': csrf.get_token(request),
            },
        }),
    }
