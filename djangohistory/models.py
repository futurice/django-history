from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
import json, copy

from fields import JSONField
from middleware import get_current_request
from helpers import pretty_diff, get_setting
from pprint import pprint as pp

class HistoryManager(models.Manager):
    def int_or_instance_id(self, pk):
        if not(isinstance(pk, int) or isinstance(pk, long) or isinstance(pk, basestring)):
            pk = pk.pk
        return pk

    def by_instance(self, instance):
        return self.filter(object_id=instance.pk,
                model=ContentType.objects.get_for_model(instance).pk,)

    def by_content_type(self, ct_id):
        return self.filter(model=ct_id,)

    def by_created(self, direction='-'):
        return self.all().order_by('{0}created'.format(direction))

    def by_user(self, instance):
        return self.filter(user=instance.pk)

    def add(self, action, changes, model, user=None, object_id=None):
        if not getattr(settings, 'DJANGO_HISTORY_TRACK', True):
            return
        request = get_current_request()
        if not user:
            if request:
                user = request.user
        user_id = user.pk if user else None
        model_ct = ContentType.objects.get_for_model(model)
        model_id = model_ct.pk
        object_id = object_id or model.pk

        # exclusion / none -checks
        excludes = get_setting('EXCLUDE_CHANGES')
        if excludes:
            excludes_for_model = excludes.get("{0}.{1}".format(model_ct.app_label, model_ct.model))
            if excludes_for_model:
                for k,v in copy.deepcopy(changes).iteritems():
                    if k in excludes_for_model.get('fields', []):
                        del changes[k]
        if not changes:
            return

        # for FKs, get old/new information
        fields = model._meta.local_fields
        def get_item(model, pk):
            value = None
            if isinstance(pk, models.Model):
                pk = copy.deepcopy(pk.pk)
            try:
                value = unicode(model.objects.get(pk=pk))
            except Exception, e:
                if settings.DEBUG: print e
            return value

        def match_field(model, changed_field):
            try:
                field = model._meta.get_field(k)
            except:
                field = model._meta.get_field(k.replace('_id', ''))
            return field

        for k,v in changes.iteritems():
            field = match_field(model, k)
            v['verbose_name'] = unicode(field.verbose_name)
            if isinstance(field, models.ForeignKey):
                parent_model = field.related.parent_model
                if v['new']:
                    v['new_to_string'] = get_item(parent_model, v['new'])
                    if isinstance(v['new'], models.Model):
                        v['new'] = v['new'].pk
                if v['old']:
                    v['old_to_string'] = get_item(parent_model, v['old'])
                    if isinstance(v['old'], models.Model):
                        v['old'] = v['old'].pk
                v['is_fk'] = True
            if isinstance(field, models.ManyToManyField):
                v['is_m2m'] = True
                v['m2m_css_class'] = 'old_change'
                if 'm2m.add' in action:
                    v['m2m_css_class'] = 'new_change'
        if 'delete' in action:# M2M copied on delete
            for field in model._meta.local_many_to_many:
                pk_set = getattr(model, field.name).all()
                row = {
                    'changed': list([k.pk for k in pk_set]),
                    'is_m2m': True,
                    'm2m_css_class': 'old_change',
                    'changed_to_string': u", ".join([unicode(k) for k in pk_set]),
                    'verbose_name': unicode(field.verbose_name),
                }
                changes[field.name] = row
        changeset = {
        'fields': changes,
        'model': {
                'to_string': unicode(model),
                'verbose_name': unicode(model._meta.verbose_name),
                'content_type': {
                    'id': model_ct.pk,
                    'app_label': model_ct.app_label,
                    'model': model_ct.model,
                }
            },
        'user': {
                'to_string': unicode(user),
            }
        }

        history = self.model(
            action=action,
            changes=changeset,
            model=model_id,
            user=user_id,
            object_id=object_id,)
        history.save(force_insert=True)

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
        for k,v in self.changes['fields'].iteritems():
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

