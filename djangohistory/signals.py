from django.conf import settings
from django.db.models.signals import pre_delete, post_delete, post_init, post_save, m2m_changed, pre_save
from django.db import models

from models import History

ACTION_MAP = {
'post_add': 'm2m.add',
'post_remove': 'm2m.remove',
}

def handle_m2m(sender, *args, **kwargs):
    """
    A model's save() never gets called on ManyToManyField changes, m2m_changed-signal is sent.
    sender = dynamically generated model in m2m-table
    instance = parent
    related_instance = instance being m2m'ed
    """
    action = kwargs['action']
    instance = kwargs['instance']
    if hasattr(instance, 'get_changes') and (action == 'post_add' or action == 'post_remove'):
        pk_set = list(kwargs['pk_set'])
        relation_name = sender._meta.db_table.split('_')[-1]
        for pk in pk_set:
            relations = {k.name:k for k in instance.get_m2m_relations()}
            related_instance = relations[relation_name].related.parent_model.objects.get(pk=pk)
            field = relations[relation_name]
            changes = {field.name: {'changed': [pk], 'changed_to_string': unicode(related_instance)}}
            # TODO: add meta information about relation
            # - parent, child
            History.objects.add(
                    action=ACTION_MAP[action],
                    changes=changes,
                    model=instance,)

def handle_model(sender, *args, **kwargs):
    instance = kwargs['instance']
    if hasattr(instance, 'get_changes'):
        changes = instance.get_changes()
        if changes.get('id') and changes['id']['old'] is None:
            changes = instance.get_field_values()
            default_values = {}
            for k,v in changes.iteritems():
                default_values[k] = {}
            changes = instance.get_changes(dirty_fields=default_values)
        History.objects.add(
                action='save',
                changes=changes,
                model=instance)

def handle_delete(sender, *args, **kwargs):
    instance = kwargs['instance']
    if hasattr(instance, 'get_changes'): # TODO: settings.TRACKED_APPS/MODELS?
        changes = instance.get_changes(dirty_fields=instance.get_field_values())
        for k,v in changes.iteritems():
            v['new'] = ''
        History.objects.add(
                action='delete',
                changes=changes,
                model=instance)

if getattr(settings, 'DJANGO_HISTORY_TRACK', True):
    m2m_changed.connect(handle_m2m)
    post_save.connect(handle_model)
    pre_delete.connect(handle_delete) # pre; to get relational data
