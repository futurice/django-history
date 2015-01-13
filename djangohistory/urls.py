from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.template import add_to_builtins

from views import LatestView, ByView

urlpatterns = patterns('',
    url(r'^latest$', LatestView.as_view(), name='history-latest'),
    url(r'^by/user/(?P<user_id>\d+)$', ByView.as_view(), name='history-by-user'),
    url(r'^by/ct/(?P<ct_id>\d+)$', ByView.as_view(), name='history-by-ct'),
    url(r'^by/ct/(?P<ct_id>\d+)/id/(?P<id>\d+)$', ByView.as_view(), name='history-by-id'),
)
