import time

from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404

from social_core.backends.utils import user_backends_data, get_backend
from social_django.utils import Storage

from nmanage.resources.models import Resource, Permission


BACKEND_DISPLAY_NAMES = {
  'azuread-oauth2': 'Azure Login'
}


def home(request):
  return http.HttpResponseRedirect('/resources/list/')


def login_view(request):
  backends = user_backends_data(request.user, settings.AUTHENTICATION_BACKENDS, Storage)['backends']
  bclasses = []
  for b in backends:
    bclass = get_backend(settings.AUTHENTICATION_BACKENDS, b)
    bclass.display_name = BACKEND_DISPLAY_NAMES.get(bclass.name, f"{bclass.name} Login")
    bclasses.append(bclass)

  n = request.GET.get('next', '/')
  context = {'bclasses': bclasses, 'next': n}
  return TemplateResponse(request, 'resources/login.html', context)


@login_required
def my_resources(request):
  resources = Resource.objects.filter(permission__user=request.user).exclude(region__isnull=True)
  resources = resources.order_by('-created')
  paginator = Paginator(resources, 10)

  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  regions = {}
  for r in page_obj:
    if r.region.id not in regions:
      regions[r.region.id] = {
        'region': r.region,
        'resources': [],
      }

    regions[r.region.id]['resources'].append(r.rid)

  for region_id, data in regions.items():
    ec2_states = data['region'].get_ec2_infos(data['resources'])

    for r in page_obj:
      if r.rid in ec2_states:
        r.api_data = ec2_states[r.rid]

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
  resource = Resource.objects.filter(id=rid, permission__user=request.user).exclude(region__isnull=True).first()

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
