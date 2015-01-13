from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from models import History

class LatestView(TemplateView):
    template_name = "djangohistory/latest.html"
    
    def get(self, request):
        c = {}
        c['history'] = History.objects.all().order_by('-created')[:100]
        c['header_name'] = 'latest'
        return self.render_to_response(c)

class ByView(TemplateView):
    template_name = "djangohistory/latest.html"
    
    def get(self, request, ct_id=None, id=None, user_id=None):
        c = {}
        if ct_id:
            ct = ContentType.objects.get(pk=ct_id)
        instance = u''
        if id:
            instance = get_object_or_404(ct.model_class(), pk=id)
            history = History.objects.by_instance(instance).order_by('-created')[:100]
            c['header_name'] = u'for {0} (#{1}) {2}'.format(unicode(ct), unicode(instance.pk), unicode(instance))
        elif user_id:
            instance = get_object_or_404(get_user_model(), pk=user_id)
            history = History.objects.by_user(instance).order_by('-created')[:100]
            c['header_name'] = u'by {0}'.format(unicode(instance))
        else:
            history = History.objects.by_content_type(ct_id).order_by('-created')[:100]
            c['header_name'] = u'for {0}'.format(unicode(ct))

        c['history'] = history
        return self.render_to_response(c)
