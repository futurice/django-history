from django.conf import settings
from django.db import models

import json, copy

from djangohistory.controllers import HistoryMixin
from djangohistory.fields import JSONField
from djangohistory.managers import HistoryManager

class History(models.Model, HistoryMixin):
    action = models.CharField(max_length=255)
    changes = JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    # FK (INT)
    object_id = models.IntegerField(blank=True, null=True, db_index=True)
    model = models.IntegerField(db_index=True)
    user = models.IntegerField(blank=True, null=True, db_index=True)

    objects = HistoryManager()

