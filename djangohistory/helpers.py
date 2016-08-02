from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
import django

import json
import six

def to_json(data):
    kw = {}
    if six.PY2:
        kw['encoding'] = 'utf-8'
    return json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(',',':'), **kw)

def get_setting(name):
    """ Looks for settings under DJANGO_HISTORY_SETTINGS, supporting dot notation for nested lookups,
    eg. get_setting('EXCLUDE_CHANGES.fields') """
    dh = getattr(settings, 'DJANGO_HISTORY_SETTINGS', {})
    result = None
    for k in name.split('.'):
        if dh is None:
            continue
        result = dh.get(k, None)
        dh = result
    return result

def get_relation(rel):
    if django.VERSION[:2] >= (1, 9):
        instance = rel.remote_field.model
    elif django.VERSION[:2] >= (1, 8):
        instance = rel.related.model
    else:
        instance = rel.related.parent_model
    return instance

def models_listing():
    c = []
    for m in apps.get_models():
        ct = get_ct(m)
        url = reverse("history-by-ct", kwargs=dict(ct_id=ct.id))
        c.append(dict(url=url, name=m._meta.object_name, model=m))
    return c

def models_schemas(models=None):
    models = models or models_listing()
    d = {}
    for model in models:
        d.setdefault(model['name'], {})
        f = []
        for field in model['model']._meta.get_fields(include_hidden=True):
            f.append(dict(cls=field.__class__.__name__,
                          name=field.name,
                          hidden=field.hidden),)
        d[model['name']].setdefault('fields', f)
    return d

def get_ct_by_id(pk):
    return ContentType.objects.get(pk=pk)

def get_ct(model):
    return ContentType.objects.get_for_model(model)

def match_field(model, changed_field):
    try:
        field = model._meta.get_field(changed_field)
    except:
        field = model._meta.get_field(changed_field.replace('_id', ''))
    return field
