from distutils.version import StrictVersion

import django
from django.conf.urls import include, url
from django.conf import settings

from is_core.site import site


if StrictVersion(django.get_version()) >= StrictVersion('1.9'):
    urlpatterns = [url(r'^', include(site.urls))]
else:
    from django.conf.urls import patterns

    urlpatterns = patterns('', url(r'^', include(site.urls)))

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
