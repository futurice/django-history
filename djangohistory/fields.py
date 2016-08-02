import django
from django.conf import settings
from django.db import models
import json
import six

from djangohistory.helpers import to_json

if django.VERSION[:2]>=(1, 9) and (getattr(settings, 'USING_POSTGRES', False) or 'postgres' in settings.DATABASES['default']):
    from django.contrib.postgres.fields import JSONField
else:
    class JSONField(models.TextField):

        def formfield(self, **kwargs):
            return super(JSONField, self).formfield(form_class=JSONFormField, **kwargs)

        def from_db_value(self, value, expression, connection, context):
            return json.loads(value)

        def get_db_prep_save(self, value, connection, prepared=False):
            if value is None: return
            return to_json(value)

        def value_to_string(self, obj):
            value = self._get_val_from_obj(obj)
            return self.get_prep_value(value)

    try:
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], ['^djangohistory\.fields\.JSONField'])
    except ImportError:
        pass
