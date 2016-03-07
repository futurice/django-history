import django
from django.conf import settings
from django.db.models.signals import pre_delete, post_delete, post_init, post_save, m2m_changed, pre_save
from django.db import models

from djangohistory.models import History
from djangohistory.helpers import get_relation

from djangodirtyfield.mixin import DirtyFieldMixin

import six

ACTION_MAP = {
'post_add': 'm2m.add',
'post_remove': 'm2m.remove',
}

def m2m_relations(instance):
    fields = []
    if django.VERSION[:2]>=(1, 9):
        fields = [f for f in instance._meta.get_fields()
                if f.is_relation and f.many_to_many]
    else:
        for field, model in instance._meta.get_m2m_with_model():
            if isinstance(field, models.ManyToManyField):
                fields.append(field)
    return fields

def is_df(instance):
    return isinstance(instance, DirtyFieldMixin)

def handle_m2m(sender, *args, **kwargs):
    """
    A model's save() never gets called on ManyToManyField changes, m2m_changed-signal is sent.
    sender = dynamically generated model in m2m-table
    instance = parent
    related_instance = instance being m2m'ed
    """
    action = kwargs['action']
    instance = kwargs['instance']
    if is_df(instance) and (action == 'post_add' or action == 'post_remove'):
        pk_set = list(kwargs['pk_set'])
        relation_name = sender._meta.db_table.replace(sender._meta.app_label + '_' + instance.__class__.__name__.lower() + '_', '')
        for pk in pk_set:
            relations = {k.name:k for k in m2m_relations(instance)}
            related_instance = get_relation(relations[relation_name]).objects.get(pk=pk)
            field = relations[relation_name]
            changes = {field.name: {'changed': [pk], 'changed_to_string': six.text_type(related_instance)}}
            # TODO: add meta information about relation
            # - parent, child
            History.objects.add(
                    action=ACTION_MAP[action],
                    changes=changes,
                    model=instance,)

def handle_model(sender, *args, **kwargs):
    instance = kwargs['instance']
    if is_df(instance):
        changes = instance.get_changes()
        if changes.get('id') and changes['id']['old'] is None:
            changes = instance.dirtyfield.get_field_values()
            default_values = {}
            for k,v in six.iteritems(changes):
                default_values[k] = {}
            changes = instance.get_changes(dirty_fields=default_values)
        History.objects.add(
                action='save',
                changes=changes,
                model=instance)

def handle_delete(sender, *args, **kwargs):
    instance = kwargs['instance']
    if is_df(instance): # TODO: settings.TRACKED_APPS/MODELS?
        changes = instance.get_changes(dirty_fields=instance.dirtyfield.get_field_values())
        for k,v in six.iteritems(changes):
            v['new'] = ''
        History.objects.add(
                action='delete',
                changes=changes,
                model=instance)

if getattr(settings, 'DJANGO_HISTORY_TRACK', True):
    m2m_changed.connect(handle_m2m)
    post_save.connect(handle_model)
    pre_delete.connect(handle_delete) # pre; to get relational data
