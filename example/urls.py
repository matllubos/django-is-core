from django.conf.urls import patterns, include, url
from django.conf import settings

from is_core.site import site


urlpatterns = patterns('',
    url(r'^', include(site.urls)),
)

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
