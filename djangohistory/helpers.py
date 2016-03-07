import django
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
import json
import six

def to_json(data):
    kw = {}
    if six.PY2:
        kw['encoding'] = 'utf-8'
    return json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(',',':'), **kw)

def pretty_diff(a, b):
    import diff_match_patch
    d = diff_match_patch.diff_match_patch()
    e = d.diff_main(a, b)
    return d.diff_prettyHtml(e)

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
    if django.VERSION[:2] >= (1, 8):
        instance = rel.remote_field.model
    else:
        instance = rel.related.parent_model
    return instance
