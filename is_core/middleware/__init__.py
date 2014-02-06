from django.core.urlresolvers import resolve


class RequestKwargsMiddleware(object):
    def process_request(self, request):
        request.kwargs = resolve(request.path).kwargs
