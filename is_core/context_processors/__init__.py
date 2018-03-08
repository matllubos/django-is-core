from django.conf import settings


def is_js_dev(req):
    return {'JS_DEV': settings.JS_DEV}
