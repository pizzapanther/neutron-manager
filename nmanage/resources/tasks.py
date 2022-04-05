from django.utils import timezone

from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from nmanage.resources.models import PowerSchedule


@db_task()
def execute_event(eid):
  event = PowerSchedule.objects.filter(id=eid).first()
  if event:
    print('Executing:', event.event_type, event.resource)
    if event.event_type == 'ON':
      event.resource.execute('start')
      for r in range(0, 60 * 5):
        if event.resource.is_done('start'):
          break

    else:
      event.resource.execute('stop')

    event.last_executed = timezone.now()
    event.save()


@db_periodic_task(crontab(minute='*/5'))
def schedule_check():
  now = timezone.now()

  scheduled_resources = {}

  events = PowerSchedule.objects.filter(event_ts__lte=now).order_by('-event_ts')
  for event in events:
    event.reschedule()
    event.save()

    if event.resource.id in scheduled_resources:
      pass

    elif event.resource.disable_power_schedule:
      pass

    else:
      execute_event(event.id)
      scheduled_resources[event.resource.id] = event.event_type
