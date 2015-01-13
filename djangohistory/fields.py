from django.db import models
import json

from helpers import to_json

class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        return super(JSONField, self).formfield(form_class=JSONFormField, **kwargs)

    def to_python(self, value):
        if isinstance(value, basestring):
            value = json.loads(value)
        return value

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
