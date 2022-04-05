import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    tzname = request.session.get('django_timezone', 'America/Chicago')
    request.timezone = None

    if tzname:
      tz = zoneinfo.ZoneInfo(tzname)
      timezone.activate(tz)
      request.timezone = tz

    else:
      timezone.deactivate()

    return self.get_response(request)
