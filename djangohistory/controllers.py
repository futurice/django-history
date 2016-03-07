from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models

from djangohistory.helpers import pretty_diff
from djangohistory.managers import match_field

from collections import OrderedDict

import six

def get_ct_by_id(pk):
    return ContentType.objects.get(pk=pk)

def get_ct(model):
    return ContentType.objects.get_for_model(model)

class HistoryMixin(object):
    def link_instance(self):
        return reverse("history-by-id", kwargs=dict(ct_id=self.model, id=self.object_id))

    def link_field(self, model, name, values):
        rel = model._meta.get_field(name).related_model
        ct_id = 0
        oid = 0
        if rel and values.get('changed'):
            ct_id = get_ct(rel).id
            oid = values['changed'][0]
        return reverse("history-by-id", kwargs=dict(ct_id=ct_id, id=oid))

    def format(self, skip_fields=[]):
        diff = {}
        fields = []
        if not self.changes:
            return []
        model_ct = get_ct_by_id(self.model)
        model = model_ct.model_class()

        is_propagated = False
        for k,v in six.iteritems(self.changes['fields']):
            row = v
            if k in skip_fields:
                continue
            field = match_field(model, k)
            if isinstance(field, models.ForeignKey):
                row['is_fk'] = True
            if isinstance(field, models.ManyToManyField):
                row['is_m2m'] = True

            old = v['old'] if v.get('old') else ''
            new = v['new'] if v.get('new') else ''
            row['field'] = k
            row['old'] = old
            row['new']= new
            if (old and new) and hasattr(settings, 'DJANGOHISTORY_DIFF_ENABLED'):
                row['diff'] = pretty_diff(str(old), str(new))

            # CSS
            if 'm2m.add' in self.action:
                row['m2m_css_class'] = 'new_change'
            else:
                row['m2m_css_class'] = 'old_change'

            # LINK
            row['link'] = self.link_field(model, k, v)

            # M2M add/remove propagated to M2M itself
            if row.get('m2mpg'):
                is_propagated = True
                if self.action == 'add':
                    row['new'] = v['changed_to_string']
                    row['old'] = ''
                else:
                    row['new'] = ''
                    row['old'] = v['changed_to_string']

            fields.append(row)
        diff['is_propagated'] = is_propagated
        diff['user'] = self.changes['user']
        diff['user']['ct'] = ContentType.objects.get_for_model(get_user_model()).pk
        diff['model'] = self.changes['model']
        diff['fields'] = fields
        return diff
