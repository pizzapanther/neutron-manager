import time

from django import http
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404

from nmanage.resources.models import Resource, Permission


def home(request):
  return http.HttpResponseRedirect('/resources/list/')


@login_required
def my_resources(request):
  resources = Resource.objects.filter(permission__user=request.user).exclude(account__isnull=True)
  resources = resources.order_by('-created')
  paginator = Paginator(resources, 50)

  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  context = {
    'page_obj': page_obj,
  }
  return TemplateResponse(request, 'resources/list.html', context)


def get_perm(user, action, rid):
  p = None
  for key, actions in Permission.ACTION_MAP.items():
    for a in actions:
      if a == action:
        p = key

  if p is None:
    raise http.Http404

  return get_object_or_404(
    Permission,
    user=user,
    actions__contains=[p],
    resource__id=rid,
  )


@login_required
def execute_action(request, action, rid):
  permission = get_perm(request.user, action, rid)
  wait = permission.resource.execute(action)
  if wait:
    now = int(time.time() * 1000)
    return http.HttpResponseRedirect(f'/resources/wait/{action}/{rid}/?ts={now}')

  return http.HttpResponseRedirect('/resources/list/')


@login_required
def wait_action(request, action, rid):
  permission = get_perm(request.user, action, rid)

  if permission.resource.is_done(action):
    return http.HttpResponseRedirect('/resources/list/')

  context = {
    'permission': permission,
    'action': action,
    'rid': rid,
  }
  return TemplateResponse(request, 'resources/wait.html', context)


@login_required
def view_info(request, rid):
  resource = Resource.objects.filter(id=rid, permission__user=request.user).exclude(account__isnull=True).first()

  if not resource:
    raise http.Http404

  info = {}
  for key, value in resource.get_info().items():
    if key in ['InstanceId', 'InstanceType', 'PrivateIpAddress', 'PublicIpAddress', 'State']:
      if key in ['State']:
        info[key] = value['Name']

      else:
        info[key] = value

  context = {
    'resource': resource,
    'info': info,
  }
  return TemplateResponse(request, 'resources/info.html', context)
