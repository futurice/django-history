from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

from .views import LatestView, ByView

urlpatterns = [
    url(r'^latest$', LatestView.as_view(), name='history-latest'),
    url(r'^by/user/(?P<user_id>\d+)$', ByView.as_view(), name='history-by-user'),
    url(r'^by/ct/(?P<ct_id>\d+)$', ByView.as_view(), name='history-by-ct'),
    url(r'^by/ct/(?P<ct_id>\d+)/id/(?P<id>\d+)$', ByView.as_view(), name='history-by-id'),
]
