from django.conf import settings

def site(request):
  return {
    'site_name': settings.SITE_NAME
  }
