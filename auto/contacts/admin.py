from django.contrib import admin

from contacts.models import Contact #, SiteSettings


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'value', 'icon', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'value']

#
# @admin.register(SiteSettings)
# class SiteSettingsAdmin(admin.ModelAdmin):
#     list_display = ['site_name', 'company_name', 'phone', 'email']
#     fieldsets = (
#         ('Основные настройки', {
#             'fields': ('site_name', 'site_description', 'company_name')
#         }),
#         ('Контактная информация', {
#             'fields': ('company_address', 'working_hours', 'phone', 'email')
#         }),
#     )
#
#     def has_add_permission(self, request):
#         # Разрешаем создавать только одну запись
#         return not SiteSettings.objects.exists()
