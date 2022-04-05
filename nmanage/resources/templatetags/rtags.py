from django import template

from nmanage.resources.models import Permission


register = template.Library()

@register.filter
def actions(resource, user):
  p = Permission.objects.filter(resource=resource, user=user).first()
  if p:
    actions = []
    for a in p.actions:
      if a in Permission.ACTION_MAP:
        for v in Permission.ACTION_MAP[a]:
          actions.append(f"'{v}'")

    return "[{}]".format(",".join(actions))

  return '[]'


@register.filter
def can_schedule(user, resource):
  perm = Permission.objects.filter(resource=resource, user=user, actions__contains=['schedule']).first()
  if perm:
    return True

  return False
