from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views
from rest_framework.urlpatterns import format_suffix_patterns


app_name = 'home'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^populate/$', views.populate_db, name='populate'),
    url(r'^admin/', admin.site.urls),
    url(r'^auctions/', include('auctions.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
