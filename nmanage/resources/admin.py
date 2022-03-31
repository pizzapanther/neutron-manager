from django.contrib import admin


from nmanage.resources.models import Resource, Region, Permission, AwsAccount


@admin.register(AwsAccount)
class AwsAccountAdmin(admin.ModelAdmin):
  list_display = ('name', 'key_id', 'modified')
  list_filter = ('created', 'modified')
  date_hierarchy = 'modified'


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
  list_display = ('name', 'region', 'endpoint', 'modified')
  list_filter = ('created', 'modified')
  raw_id_fields = ('account',)
  date_hierarchy = 'modified'


class PermissionInline(admin.TabularInline):
  model = Permission
  raw_id_fields = ('user',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
  list_display = ('name', 'rid', 'rtype', 'region', '_permissions', 'modified')
  list_filter = ('rtype', 'region', 'created', 'modified')
  date_hierarchy = 'modified'
  search_fields = ('name', 'rid')
  raw_id_fields = ('region',)
  inlines = (PermissionInline,)

  def _permissions(self, obj):
    return obj.permission_set.all().count()
