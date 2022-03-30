from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.template.response import TemplateResponse

from nmanage.resources.models import Resource


@login_required
def my_resources(request):
  resources = Resource.objects.filter(permission__user=request.user).exclude(account__isnull=True)
  resources = resources.order_by('-created')
  paginator = Paginator(resources, 50)

  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)
  context = {
      'page_obj': page_obj
  }
  return TemplateResponse(request, 'resources/list.html', context)
