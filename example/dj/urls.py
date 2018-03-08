import django
from django.conf.urls import include, url
from django.conf import settings

from is_core.site import site


urlpatterns = [url(r'^', include(site.urls))]


if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
