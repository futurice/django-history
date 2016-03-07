# encoding=utf8
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
from django.utils.encoding import python_2_unicode_compatible

from djangodirtyfield.mixin import DirtyFieldMixin

class BaseModel(models.Model, DirtyFieldMixin):
    created = models.DateTimeField(default=now, db_index=True)

    class Meta:
        abstract = True

@python_2_unicode_compatible
class Publisher(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Publication(BaseModel):
    title = models.CharField(max_length=255)
    publisher = models.ForeignKey(Publisher, null=True, blank=True)

    def __str__(self):
        return self.title

@python_2_unicode_compatible
class Article(BaseModel):
    headline = models.CharField(max_length=255)
    publications = models.ManyToManyField(Publication)

    def __str__(self):
        return self.headline

class User(AbstractUser, DirtyFieldMixin):
    pass
