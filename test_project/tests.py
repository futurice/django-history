from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, TransactionTestCase
from django.test.client import Client
from django.utils.timezone import now

from djangohistory.controllers import action_id
from djangohistory.helpers import get_setting
from djangohistory.middleware import get_current_request
from djangohistory.models import History, ACTIONS
from djangohistory.views import LatestView

from .models import Publication, Article, Publisher

from collections import Counter
import copy
import six
import logging

logging.basicConfig(level=logging.DEBUG)

history_count = lambda: History.objects.all().count()

class BaseSuite(TransactionTestCase):
    pass



