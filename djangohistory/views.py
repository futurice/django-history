from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.http.response import Http404

from djangohistory.models import History
import importlib
import six

def get_view_permission(request):
    return True

class ProjectBaseView(TemplateView):
    def permitted_to_view(self, request):
        perm = getattr(settings, 'DJANGO_HISTORY_VIEW_PERMISSION', ('djangohistory.views', 'get_view_permission'))
        permission_fn = getattr(importlib.import_module(perm[0]), perm[1])
        return permission_fn(request)

class LatestView(ProjectBaseView):
    template_name = "djangohistory/latest.html"

    def get(self, request):
        if not self.permitted_to_view(request):
            raise Http404
        c = {}
        c['history'] = History.objects.all().order_by('-created')[:100]
        c['header_name'] = 'latest'
        return self.render_to_response(c)

class ByView(ProjectBaseView):
    template_name = "djangohistory/latest.html"

    def get(self, request, ct_id=None, id=None, user_id=None):
        if not self.permitted_to_view(request):
            raise Http404
        c = {}
        if ct_id:
            ct = ContentType.objects.get(pk=ct_id)
        instance = u''
        if id:
            instance = get_object_or_404(ct.model_class(), pk=id)
            history = History.objects.by_instance(instance).order_by('-created')[:100]
            c['header_name'] = u'for {0} (#{1}) {2}'.format(six.text_type(ct), six.text_type(instance.pk), six.text_type(instance))
        elif user_id:
            instance = get_object_or_404(get_user_model(), pk=user_id)
            history = History.objects.by_user(instance).order_by('-created')[:100]
            c['header_name'] = u'by {0}'.format(six.text_type(instance))
        else:
            history = History.objects.by_content_type(ct_id).order_by('-created')[:100]
            c['header_name'] = u'for {0}'.format(six.text_type(ct))

        c['history'] = history
        return self.render_to_response(c)
