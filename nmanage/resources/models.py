import datetime

from django.core import validators
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

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

  @property
  def client_kwargs(self):
    return {
      'aws_access_key_id': self.key_id,
      'aws_secret_access_key': self.key_secret,
    }


class HostedZone(models.Model):
  name = models.CharField(max_length=75)
  base_domain = models.CharField(max_length=255)
  zone_id = models.CharField(max_length=255)

  account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name

  def update_record(self, name, ip):
    client = boto3.client('route53', **self.account.client_kwargs)
    response = client.change_resource_record_sets(
      ChangeBatch={
        'Changes': [
            {
              'Action': 'UPSERT',
              'ResourceRecordSet': {
                'Name': f'{name}.{self.base_domain}',
                'ResourceRecords': [{'Value': ip}],
                'TTL': 300,
                'Type': 'A',
              },
            },
        ]
      },
      HostedZoneId=self.zone_id
    )


class Region(models.Model):
  name = models.CharField(max_length=75)
  region = models.CharField(max_length=25, blank=True, null=True, validators=[validators.validate_slug])
  endpoint = models.CharField(max_length=128, blank=True, null=True)
  account = models.ForeignKey(AwsAccount, on_delete=models.CASCADE)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name

  @property
  def client_kwargs(self):
    ret = self.account.client_kwargs

    if self.endpoint:
      ret['endpoint_url'] = self.endpoint

    if self.region:
      ret['region_name'] = self.region

    return ret

  def client(self, rtype):
    return boto3.client(rtype, **self.client_kwargs)

  def get_ec2_infos(self, rids):
    response = self.client('ec2').describe_instances(InstanceIds=rids)
    ret = {}
    for rserv in response['Reservations']:
      for instance in rserv['Instances']:
        ret[instance['InstanceId']] = instance

    return ret

class Resource(models.Model):
  class ResourceTypes(models.TextChoices):
    EC2 = 'EC2', 'EC2'

  class ZoneUpdateTypes(models.TextChoices):
    PUBLIC = 'PUBLIC', 'Public'
    PRIVATE = 'PRIVATE', 'Private'

  name = models.CharField(max_length=75, validators=[validators.validate_slug])
  rid = models.CharField('Resource ID', max_length=75)
  rtype = models.CharField('Resource Type', max_length=10, choices=ResourceTypes.choices)

  region = models.ForeignKey(Region, on_delete=models.SET_NULL, blank=True, null=True)
  zone = models.ForeignKey(HostedZone, on_delete=models.SET_NULL, blank=True, null=True)
  zone_update = models.CharField(max_length=10, choices=ZoneUpdateTypes.choices)
  last_zone_ip = models.CharField(max_length=75, blank=True, null=True)

  disable_power_schedule = models.BooleanField(default=False)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  def __str__(self):
    return self.name

  @property
  def dns(self):
    if self.zone:
      return f'{self.name}.{self.zone.base_domain}'

  @property
  def account(self):
    if self.region:
      return self.region.account

  @property
  def endpoint(self):
    if self.region:
      return self.region.endpoint

  @property
  def region_code(self):
    if self.region:
      return self.region.region

  @property
  def client(self):
    return self.region.client(self.rtype.lower())

  def execute(self, action):
    method = f"{self.rtype.lower()}_{action}"
    return getattr(self, method)()

  def get_info(self):
    response = self.client.describe_instances(InstanceIds=[self.rid])
    return response['Reservations'][0]['Instances'][0]

  def is_done(self, action):
    response = self.client.describe_instances(InstanceIds=[self.rid])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']

    if action in ['stop', 'force_stop']:
      return state == 'stopped'

    if action in ['start', 'reboot']:
      if state == 'running':
        if self.zone:
          self.update_zone_record(response['Reservations'][0]['Instances'][0])

      return state == 'running'

    return False

  def update_zone_record(self, info):
    if self.zone_update == 'PUBLIC':
      ip = info['PublicIpAddress']

    else:
      ip = info['PrivateIpAddress']

    if self.last_zone_ip != ip:
      self.zone.update_record(self.name, ip)
      self.last_zone_ip = ip
      self.save()

  def ec2_start(self):
    self.client.start_instances(InstanceIds=[self.rid])
    return True

  def ec2_stop(self):
    self.client.stop_instances(InstanceIds=[self.rid])
    return True

  def ec2_force_stop(self):
    self.client.stop_instances(InstanceIds=[self.rid], Force=True)
    return True

  def ec2_reboot(self):
    self.client.reboot_instances(InstanceIds=[self.rid])


class Permission(models.Model):
  class AvailableActions(models.TextChoices):
    POWER = 'power', 'Power On/Off'
    SCHEDULE = 'schedule', 'Edit Schedule'

  ACTION_MAP = {
    AvailableActions.POWER.value: ['start', 'stop', 'reboot', 'force_stop']
  }

  resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  actions = ArrayField(
    models.CharField('Action Type', max_length=10, choices=AvailableActions.choices)
  )


class PowerSchedule(models.Model):
  class EventTypes(models.TextChoices):
    ON = 'ON'
    OFF = 'OFF'

  resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

  event_ts = models.DateTimeField(db_index=True)
  event_type = models.CharField(max_length=3, choices=EventTypes.choices)

  last_executed = models.DateTimeField(blank=True, null=True)

  created = models.DateTimeField(auto_now_add=True, db_index=True)
  modified = models.DateTimeField(auto_now=True, db_index=True)

  class Meta:
    ordering =('event_ts',)

  def __str__(self):
    return '{} {}'.format(self.resource.name, self.event_type)

  def reschedule(self):
    new_event = self.event_ts + datetime.timedelta(days=7)
    new_event = new_event.replace(hour=self.event_ts.hour)
    self.event_ts = new_event


def rebuild_schedule(tz, resource, schedule_data):
  PowerSchedule.objects.filter(resource=resource).delete()

  days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
  for i, day in enumerate(days, start=1):
    for t in ['on', 'off']:
      key = f'{day}_{t}'
      if schedule_data[key]:
        value = schedule_data[key]
        now = timezone.now()
        ts = timezone.now()
        if tz:
          ts = ts.astimezone(tz)

        ts = ts.replace(hour=value.hour, minute=value.minute, second=0)
        if ts > now:
          pass

        else:
          ts = ts + datetime.timedelta(days=1)

        while 1:
          if ts.isoweekday() == i:
            break

          else:
            ts = ts + datetime.timedelta(days=1)

        ps = PowerSchedule(resource=resource, event_type=t.upper(), event_ts=ts)
        ps.save()
