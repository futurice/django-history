from django.conf import settings
from django.middleware.csrf import get_token
from djangohistory.helpers import get_setting

import importlib

if get_setting('GET_CURRENT_REQUEST'):
    request_module, request_function = get_setting('GET_CURRENT_REQUEST')
    get_current_request = getattr(importlib.import_module(request_module), request_function)
else:
    from djangocurrentrequest.middleware import get_current_request
