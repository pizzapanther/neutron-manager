import re
import time

from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404

from social_core.backends.utils import user_backends_data, get_backend
from social_django.utils import Storage

from nmanage.resources.models import Resource, Permission, SuperPermission, PowerSchedule, rebuild_schedule
from nmanage.resources.forms import ScheduleForm
from nmanage.resources.templatetags.rtags import tdelta


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
  search = request.GET.get('search', '')

  if request.user.is_superuser:
    resources = Resource.objects.exclude(region__isnull=True)

  else:
    resources = Resource.objects.filter(permission__user=request.user).exclude(region__isnull=True)

  if search:
    resources = resources.filter(Q(name__icontains=search) | Q(region__region=search))

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
    'search': search,
  }
  return TemplateResponse(request, 'resources/list.html', context)


def get_perm(user, action, rid):
  p = action
  for key, actions in Permission.ACTION_MAP.items():
    for a in actions:
      if a == action:
        p = key

  if p is None:
    raise http.Http404

  if user.is_superuser:
    return SuperPermission(user, p, rid)

  else:
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
  if request.user.is_superuser:
    resource = Resource.objects.filter(id=rid).exclude(region__isnull=True).first()

  else:
    resource = Resource.objects.filter(id=rid, permission__user=request.user).exclude(region__isnull=True).first()

  if not resource:
    raise http.Http404

  info = {}
  data = resource.get_info()
  for key, value in data.items():
    if key in ['InstanceId', 'InstanceType', 'PrivateIpAddress', 'PublicIpAddress', 'State']:
      if key == 'State':
        launch_time = None
        if data['State']['Name'] == 'running':
          launch_time = data['LaunchTime']

        info['Uptime'] = tdelta(resource.uptime(launch_time))
        info[key] = value['Name']

      else:
        info[key] = value

  context = {
    'resource': resource,
    'info': info,
  }
  return TemplateResponse(request, 'resources/info.html', context)


def get_event(request, resource, dow, etype):
  event = PowerSchedule.objects.filter(resource=resource, event_type=etype, event_ts__iso_week_day=dow).first()
  if event:
    if request.timezone:
      return event.event_ts.astimezone(request.timezone).time()

    return event.event_ts.time()


@login_required
def edit_schedule(request, rid):
  permission = get_perm(request.user, 'schedule', rid)
  resource = permission.resource

  init = {
    'disabled': resource.disable_power_schedule,
    'monday_on': get_event(request, resource, 1, 'ON'),
    'monday_off': get_event(request, resource, 1, 'OFF'),

    'tuesday_on': get_event(request, resource, 2, 'ON'),
    'tuesday_off': get_event(request, resource, 2, 'OFF'),

    'wednesday_on': get_event(request, resource, 3, 'ON'),
    'wednesday_off': get_event(request, resource, 3, 'OFF'),

    'thursday_on': get_event(request, resource, 4, 'ON'),
    'thursday_off': get_event(request, resource, 4, 'OFF'),

    'friday_on': get_event(request, resource, 5, 'ON'),
    'friday_off': get_event(request, resource, 5, 'OFF'),

    'saturday_on': get_event(request, resource, 6, 'ON'),
    'saturday_off': get_event(request, resource, 6, 'OFF'),

    'sunday_on': get_event(request, resource, 7, 'ON'),
    'sunday_off': get_event(request, resource, 7, 'OFF'),
  }

  if request.method == 'POST':
    form = ScheduleForm(request.POST)

    if form.is_valid():
      resource.disable_power_schedule = form.cleaned_data['disabled']
      resource.save()
      rebuild_schedule(request.timezone, resource, form.cleaned_data)
      return http.HttpResponseRedirect('../')

  else:
    form = ScheduleForm(init)

  render = form.as_ul()
  lines = ''
  label = ''
  for line in render.split("\n"):
    regex = re.search('<label.*>(.*):</label>', line)
    if regex:
      label = regex.group(1)

    elif '<input type="checkbox"' in line:
      lines += line.replace('<input type="checkbox"', f'<v-checkbox v-model="disabled" value="ON" label="{label}"')
      lines += '</v-checkbox>\n'

    elif '<input type="text"' in line:
      lines += line.replace('<input type="text"', f'<v-text-field outlined clearable label="{label}" type="time"')
      lines += '</v-text-field>\n'

    else:
      lines += line + "\n"

  context = {
    'resource': resource,
    'form': form,
    'form_render': lines,
  }
  return TemplateResponse(request, 'resources/edit_schedule.html', context)
