from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
import json, copy

from djangohistory.fields import JSONField
from djangohistory.managers import HistoryManager

import six

class History(models.Model):
    action = models.CharField(max_length=255)
    changes = JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    # FK (INT)
    object_id = models.IntegerField(blank=True, null=True, db_index=True)
    model = models.IntegerField(db_index=True)
    user = models.IntegerField(blank=True, null=True, db_index=True)

    objects = HistoryManager()

    def format(self, skip_fields=[]):
        diff = {}
        fields = []
        if not self.changes:
            return []
        for k,v in six.iteritems(self.changes['fields']):
            if k in skip_fields:
                continue
            old = v['old'] if v.get('old') else ''
            new = v['new'] if v.get('new') else ''
            row = v
            row['field'] = k
            row['old'] = old
            row['new']= new
            if (old and new) and hasattr(settings, 'DJANGOHISTORY_DIFF_ENABLED'):
                row['diff'] = pretty_diff(str(old), str(new))
            fields.append(row)
        diff['user'] = self.changes['user']
        diff['user']['ct'] = ContentType.objects.get_for_model(get_user_model()).pk
        diff['model'] = self.changes['model']
        diff['fields'] = fields
        return diff

