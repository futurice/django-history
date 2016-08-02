import django
from django.conf import settings
from django.db.models.signals import pre_delete, post_delete, post_init, post_save, m2m_changed, pre_save
from django.db import models

from djangohistory.models import History
from djangohistory.helpers import get_relation

from djangodirtyfield.mixin import DirtyFieldMixin

import six
import logging

logger = logging.getLogger('djangohistory')
if settings.DEBUG:
    logging.basicConfig(level=logging.DEBUG)

def get_field(relation):
    if isinstance(relation, models.ManyToManyField):
        field = relation.remote_field if django.VERSION[:2] > (1, 8) else relation.related
    else:
        field = relation.field
    return field

def m2m_relations(instance):
    return [f for f in instance._meta.get_fields() \
            if f.is_relation and f.many_to_many]

def get_model_relation_by_instance(model, relation):
    return [k for k in m2m_relations(model) if \
            isinstance(relation, get_relation(k))].pop()

def get_m2m_reverse_instances(instance, relation):
    if relation.related_query_name and relation.related_query_name():
        return getattr(instance, relation.related_query_name()).all()
    else:
        return get_m2m_instances(instance, relation)

def get_m2m_instances(instance, relation):
    if hasattr(instance, '%s_set'%relation.name):
        return getattr(instance, '%s_set'%relation.name).all()
    return getattr(instance, relation.name).all()

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
    logger.debug("m2m_changed: %s (%s) {%s}"%(sender, args, kwargs))

    bulk = []
    if is_df(instance) and (action in ['post_add', 'post_remove']):
        pk_set = list(kwargs.get('pk_set') or [])
        relation_name = sender._meta.db_table.replace(sender._meta.app_label + '_' + instance.__class__.__name__.lower() + '_', '')
        relations = {k.name:k for k in m2m_relations(instance)}
        field = relations[relation_name]
        for pk in pk_set:
            related_instance = get_relation(relations[relation_name]).objects.get(pk=pk)
            changes = {field.name: {'changed': [pk],
                                    'changed_to_string': six.text_type(related_instance)}}
            # reflect change
            bulk.append(History.objects.add(
                    action=action,
                    changes=changes,
                    model=instance,
                    commit=False,))
            # m2m to reflect on changes
            field = get_field(field)
            changes = {field.name: {'changed': [instance.pk],
                                    'changed_to_string': six.text_type(instance),
                                    'm2mpg': True,}}
            bulk.append(History.objects.add(
                    action='add' if action in ['post_add'] else 'rem',
                    changes=changes,
                    model=related_instance,
                    commit=False,))
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
                bulk.append(History.objects.add(
                        action=action,
                        changes=changes,
                        model=k,
                        commit=False,))

    if bulk:
        History.objects.bulk_create(bulk)

def post_save_handler(sender, *args, **kwargs):
    logger.debug("post_save: %s (%s) {%s}"%(sender, args, kwargs))
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
    logger.debug("pre_delete: %s (%s) {%s}"%(sender, args, kwargs))
    instance = kwargs['instance']
    bulk = []
    if is_df(instance):
        changes = instance.get_changes(dirty_fields=instance.dirtyfield.get_field_values())
        for k,v in six.iteritems(changes):
            v['new'] = ''
        bulk.append(History.objects.add(
                action='delete',
                changes=changes,
                model=instance,
                commit=False,))
        # m2m to propagation
        for relation in m2m_relations(instance):
            field = get_field(relation)
            changes = {field.name: {'changed': [instance.pk],
                                    'changed_to_string': six.text_type(instance),
                                    'm2mpg': True,}}
            instances = get_m2m_instances(instance, relation)
            for k in instances:
                bulk.append(History.objects.add(
                        action='rem',
                        changes=changes,
                        model=k,
                        commit=False,))
    if bulk:
        History.objects.bulk_create(bulk)

if getattr(settings, 'DJANGO_HISTORY_TRACK', True):
    m2m_changed.connect(m2m_changed_handler)
    post_save.connect(post_save_handler)
    pre_delete.connect(pre_delete_handler)
