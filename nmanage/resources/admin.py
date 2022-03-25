from django.contrib import admin


from nmanage.resources.models import Resource, Permission


class PermissionInline(admin.TabularInline):
  model = Permission
  raw_id_fields = ('user',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
  list_display = ('name', 'rid', 'rtype', '_permissions', 'modified')
  list_filter = ('rtype', 'created', 'modified')
  date_hierarchy = 'modified'
  search_fields = ('name', 'rid')

  inlines = (PermissionInline,)

  def _permissions(self, obj):
    return obj.permission_set.all().count()
