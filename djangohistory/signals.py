import django
from django.conf import settings
from django.db.models.signals import pre_delete, post_delete, post_init, post_save, m2m_changed, pre_save
from django.db import models

from djangohistory.models import History
from djangohistory.helpers import get_relation

from djangodirtyfield.mixin import DirtyFieldMixin

import six
import logging

ACTION_MAP = {
'post_add': 'm2m.add',
'post_remove': 'm2m.remove',
'pre_clear': 'm2m.clear',
}

logger = logging.getLogger('djangohistory')
if settings.DEBUG:
    logging.basicConfig(level=logging.DEBUG)

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

def get_model_relation_by_instance(model, relation):
    return [k for k in m2m_relations(model) if \
            isinstance(relation, get_relation(k))].pop()

def get_m2m_reverse_instances(instance, relation):
    if relation.related_query_name:
        return getattr(instance, relation.related_query_name).all()
    else:
        return getattr(instance, '%s_set'%relation.name).all()

def is_df(instance):
    return isinstance(instance, DirtyFieldMixin)

def m2m_changed_handler(sender, *args, **kwargs):
    """
    A model's save() never gets called on ManyToManyField changes, m2m_changed-signal is sent.
    sender = dynamically generated model in m2m-table
    instance = parent
    related_instance = instance being m2m'ed
    """
    action = kwargs['action']
    instance = kwargs['instance']
    logger.debug("handle_m2m: %s (%s) {%s}"%(sender, args, kwargs))
    # TODO: bulk updates when >1
    if is_df(instance) and (action in ['post_add', 'post_remove']):
        pk_set = list(kwargs.get('pk_set') or [])
        relation_name = sender._meta.db_table.replace(sender._meta.app_label + '_' + instance.__class__.__name__.lower() + '_', '')
        relations = {k.name:k for k in m2m_relations(instance)}
        field = relations[relation_name]
        for pk in pk_set:
            related_instance = get_relation(relations[relation_name]).objects.get(pk=pk)
            changes = {field.name: {'changed': [pk],
                                    'changed_to_string': six.text_type(related_instance)}}
            # TODO: add meta information about relation
            # - parent, child

            # reflect change
            History.objects.add(
                    action=ACTION_MAP[action],
                    changes=changes,
                    model=instance,)
            # m2m to reflect on changes
            field = field.remote_field if django.VERSION[:2] > (1, 8) else field.related
            changes = {field.name: {'changed': [instance.pk],
                                            'changed_to_string': six.text_type(instance),
                                            'm2mpg': True,}}
            History.objects.add(
                    action='add' if 'post_add' else 'remove',
                    changes=changes,
                    model=related_instance,)
    if is_df(instance) and (action in ['pre_clear']):
        # "For the pre_clear and post_clear actions, this is None."
        # TODO: should defer this until post_clear is done to be sure it happened
        # TODO: background job, optional execution
        relations = instance._meta.get_all_related_many_to_many_objects()
        for relation in relations:
            instances = get_m2m_reverse_instances(instance, relation)
            field = get_model_relation_by_instance(kwargs['model'], instance)
            changes = {field.name: {'changed': [instance.pk],
                                    'changed_to_string': six.text_type(instance)}}
            for k in instances: 
                History.objects.add(
                        action=ACTION_MAP[action],
                        changes=changes,
                        model=k,)

def post_save_handler(sender, *args, **kwargs):
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

def pre_delete_handler(sender, *args, **kwargs):
    instance = kwargs['instance']
    if is_df(instance): # TODO: settings.TRACKED_APPS/MODELS?
        changes = instance.get_changes(dirty_fields=instance.dirtyfield.get_field_values())
        for k,v in six.iteritems(changes):
            v['new'] = ''
        History.objects.add(
                action='delete',
                changes=changes,
                model=instance)

        # TODO:m2m to reflect on changes

if getattr(settings, 'DJANGO_HISTORY_TRACK', True):
    m2m_changed.connect(m2m_changed_handler)
    post_save.connect(post_save_handler)
    pre_delete.connect(pre_delete_handler) # pre; to get relational data
