django-history
==============
* [Django-history](https://github.com/futurice/django-history) [![Build Status](https://travis-ci.org/futurice/django-history.svg?branch=master)](https://travis-ci.org/futurice/django-history)

**django-history** helps you track all data changes for registered models.

Features
--------
* Tracks ForeignKeys and ManyToManyFields

Add to models you want to track history for, eg.
```
from djangodirtyfield.mixin import DirtyFieldMixin
class BaseModel(models.Model, DirtyFieldMixin):
 ...
```

Add to available apps for templates to work:
```
INSTALLED_APPS += (
    'djangohistory',)
```

To enable storing request.user information:
```
MIDDLEWARE_CLASSES += (
    'djangocurrentrequest.middleware.RequestMiddleware',)
```
If you already a similar setup, configure:
```
DJANGO_HISTORY_SETTINGS['GET_CURRENT_REQUEST'] = ('my.middleware', 'current_request_function')
```

View changesets by enabling routing:

```
urlpatterns = [
    url(r'^history/', include('djangohistory.urls')),
]
```

Diffs for changes:
```DJANGOHISTORY_DIFF_ENABLED = True```

Toggle history storage on/off:
```DJANGO_HISTORY_TRACK = False```

By default all history public. Provide your own function to secure views:
```DJANGO_HISTORY_VIEW_PERMISSION = ('djangohistory.views','get_permission')```
