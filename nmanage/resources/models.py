from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

import boto3

from encrypted_model_fields.fields import EncryptedCharField


class AwsAccount(models.Model):
  name = models.CharField(max_length=75)

  key_id = models.CharField(max_length=128)
  key_secret = EncryptedCharField(max_length=255)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name


class Resource(models.Model):
  class ResourceTypes(models.TextChoices):
    EC2 = 'EC2', 'EC2'

  name = models.CharField(max_length=75)
  rid = models.CharField('Resource ID', max_length=75)
  rtype = models.CharField('Resource Type', max_length=10, choices=ResourceTypes.choices)
  region = models.CharField(max_length=25, blank=True, null=True)
  endpoint = models.CharField(max_length=128, blank=True, null=True)

  account = models.ForeignKey(AwsAccount, on_delete=models.SET_NULL, null=True, blank=True)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name

  @property
  def client_kwargs(self):
    ret = {
      'aws_access_key_id': self.account.key_id,
      'aws_secret_access_key': self.account.key_secret,
    }

    if self.endpoint:
      ret['endpoint_url'] = self.endpoint

    if self.region:
      ret['region_name'] = self.region

    return ret

  def execute(self, action):
    client = boto3.client(self.rtype.lower(), **self.client_kwargs)

    method = f"{self.rtype.lower()}_{action}"
    return getattr(self, method)(client)

  def is_done(self, action):
    return False

  def ec2_start(self, client):
    client.start_instances(InstanceIds=[self.rid])
    return True

  def ec2_stop(self, client):
    client.stop_instances(InstanceIds=[self.rid])
    return True

  def ec2_force_stop(self, client):
    client.stop_instances(InstanceIds=[self.rid], Force=True)
    return True

  def ec2_reboot(self, client):
    client.reboot_instances(InstanceIds=[self.rid])


class Permission(models.Model):
  class AvailableActions(models.TextChoices):
    POWER = 'power', 'Power On/Off'

  ACTION_MAP = {
    AvailableActions.POWER.value: ['start', 'stop', 'reboot', 'force_stop']
  }

  resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  actions = ArrayField(
    models.CharField('Action Type', max_length=10, choices=AvailableActions.choices)
  )
