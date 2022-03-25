from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Resource(models.Model):
  class ResourceTypes(models.TextChoices):
    EC2 = 'EC2', 'EC2'

  name = models.CharField(max_length=75)
  rid = models.CharField('Resource ID', max_length=75)
  rtype = models.CharField('Resource Type', max_length=10, choices=ResourceTypes.choices)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name


class Permission(models.Model):
  class AvailableActions(models.TextChoices):
    POWER = 'power', 'Power On/Off'

  resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  actions = ArrayField(
    models.CharField('Action Type', max_length=10, choices=AvailableActions.choices)
  )
