:authors: Jussi Vaihia
:organization: Futurice
:copyright: 2014 Futurice

django-history
==============

**django-history** helps you track all data changes for registered models.

Features
--------
- Tracks ForeignKeys and ManyToManyFields

::
    For Django 1.5+, Python 2.7+.

    Add to models you want to track history for, eg.

    from djangodirtyfield.mixins import DirtyFieldMixin
    class BaseModel(models.Model, DirtyFieldMixin):
     ...

    Add to available apps for templates to work:

    INSTALLED_APPS += (
        'djangohistory',)

    To enable storing request.user information:

    MIDDLEWARE_CLASSES += (
        'djangohistory.middleware.ThreadLocals',)

        Or, if already a similar setup, configure:
        DJANGO_HISTORY_SETTINGS['GET_CURRENT_REQUEST'] = ('my.middleware', 'current_request_function')

    View changesets by enabling routing:

    urlpatterns = patterns('',
        url(r'^history/', include('djangohistory.urls')),
        )

        All changes:
        /history/latest

        Changes by Content Type:
        /history/by/?ct_id=

        Changes by specific Model instance:
        /history/by/?ct_id=&id=


    Diffs for changes can be enabled optionally:

    DJANGOHISTORY_DIFF_ENABLED = True
    pip install diff-match-patch==20121119
