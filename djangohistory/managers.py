from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from djangohistory.helpers import get_setting, get_relation, match_field
from djangohistory.middleware import get_current_request
from djangohistory.controllers import ACTIONS

import copy
import six

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

    def add(self, action, changes, model, user=None, object_id=None, commit=True):
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
                for k,v in six.iteritems(copy.deepcopy(changes)):
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
                value = six.text_type(model.objects.get(pk=pk))
            except Exception as e:
                if settings.DEBUG: print(e)
            return value
        
        def verbose_name(field):
            try:
                vn = field.verbose_name
            except AttributeError:
                vn = field.name
            return six.text_type(vn)

        for k,v in six.iteritems(changes):
            field = match_field(model, k)
            v['verbose_name'] = verbose_name(field)
            if isinstance(field, models.ForeignKey):
                parent_model = get_relation(field)
                if v['new']:
                    v['new_to_string'] = get_item(parent_model, v['new'])
                    if isinstance(v['new'], models.Model):
                        v['new'] = v['new'].pk
                if v['old']:
                    v['old_to_string'] = get_item(parent_model, v['old'])
                    if isinstance(v['old'], models.Model):
                        v['old'] = v['old'].pk
            if isinstance(field, models.ManyToManyField):
                pass
        if 'delete' in action:# M2M copied on delete
            for field in model._meta.local_many_to_many:
                pk_set = getattr(model, field.name).all()
                if not pk_set:
                    continue
                row = {
                    'changed': list([k.pk for k in pk_set]),
                    'changed_to_string': u", ".join([six.text_type(k) for k in pk_set]),
                    'verbose_name': verbose_name(field),
                }
                changes[field.name] = row
        changeset = {
        'fields': changes,
        'model': {
                'to_string': six.text_type(model),
                'verbose_name': verbose_name(model._meta),
                'content_type': {
                    'id': model_ct.pk,
                    'app_label': model_ct.app_label,
                    'model': model_ct.model,
                }
            },
        'user': {
                'to_string': six.text_type(user) if user else "",
            }
        }

        history = self.model(
            action=ACTIONS.for_constant(action).value,
            changes=changeset,
            model=model_id,
            user=user_id,
            object_id=object_id,)
        if commit:
            history.save(force_insert=True)
        return history
