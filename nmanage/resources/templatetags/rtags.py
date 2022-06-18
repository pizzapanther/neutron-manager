from django import template

from nmanage.resources.models import Permission


register = template.Library()

@register.filter
def actions(resource, user):
  actions = []
  if user.is_superuser:
    for perm, verbs in Permission.ACTION_MAP.items():
      for v in verbs:
        actions.append(f"'{v}'")

  else:
    p = Permission.objects.filter(resource=resource, user=user).first()
    if p:
      for a in p.actions:
        if a in Permission.ACTION_MAP:
          for v in Permission.ACTION_MAP[a]:
            actions.append(f"'{v}'")

  return "[{}]".format(",".join(actions))


@register.filter
def can_schedule(user, resource):
  perm = Permission.objects.filter(resource=resource, user=user, actions__contains=['schedule']).first()
  if perm:
    return True

  return False


def dd(num):
  if num < 10:
    return f'0{num}'

  return str(num)


@register.filter
def tdelta(td):
  if td:
    ts = td.total_seconds()
    day_sec = 24 * 60 * 60
    hour_sec = 60 * 60
    min_sec = 60

    days = int(ts / day_sec)
    ts = ts - days * day_sec

    hrs = int(ts / hour_sec)
    ts = ts - hrs * hour_sec

    mins = int(ts / min_sec)
    secs = int(ts - mins * min_sec)

    return f'{days} days {dd(hrs)}:{dd(mins)}:{dd(secs)}'

  return td
