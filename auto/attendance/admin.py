from django.contrib import admin
from django.utils.html import format_html
from attendance.models import Attendance, PhotoAttendance
from reservation.admin import admin_site


class PhotoAttendanceInline(admin.TabularInline):
    model = PhotoAttendance
    extra = 3
    max_num = 10
    fields = ['photo', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" height="100" style="border-radius: 5px; border: 1px solid #ddd;" />',
                               obj.photo.url)
        return "📷 Фото не загружено"

    image_preview.short_description = 'Предпросмотр'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['tittle', 'price', 'duration_display', 'is_active', 'photos_count']
    list_filter = ['is_active']
    search_fields = ['tittle', 'description']
    list_editable = ['is_active']
    inlines = [PhotoAttendanceInline]  # Добавляем inline

    fieldsets = (
        ('Основная информация', {
            'fields': ('tittle', 'description', 'price', 'duration', 'is_active'),
            'classes': ('wide',)
        }),
    )

    def duration_display(self, obj):
        hours = obj.duration.seconds // 3600
        minutes = (obj.duration.seconds % 3600) // 60
        return f"{hours}ч {minutes}м" if hours > 0 else f"{minutes} минут"

    duration_display.short_description = 'Длительность'

    def photos_count(self, obj):
        count = obj.photos.count()
        return f"📷 {count}" if count > 0 else "❌ Нет фото"

    photos_count.short_description = 'Фото'


admin_site.register(Attendance, AttendanceAdmin)
