from django import template

from nmanage.resources.models import Permission


register = template.Library()

@register.filter
def actions(resource, user):
  p = Permission.objects.filter(resource=resource, user=user).first()
  if p:
    actions = []
    for a in p.actions:
      if a == 'power':
        actions.append("'start'")
        actions.append("'stop'")

    return "[{}]".format(",".join(actions))

  return '[]'
