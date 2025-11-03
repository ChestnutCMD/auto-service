from django.contrib import admin
from django.urls import path

from reservation.models import Reservations, WorkSchedule


@admin.register(Reservations)
class ReservationsAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'attendance', 'time', 'status', 'communication']
    list_filter = ['status', 'attendance', 'time', 'communication']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']
    date_hierarchy = 'time'
    list_editable = ['status']

    fieldsets = (
        ('Основная информация', {
            'fields': ('attendance', 'name', 'phone', 'communication')
        }),
        ('Время и статус', {
            'fields': ('time', 'status', 'created_at')
        }),
    )


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['day_of_week', 'start_time', 'end_time', 'is_working']
    list_editable = ['start_time', 'end_time', 'is_working']


class CustomAdminSite(admin.AdminSite):
    site_header = "Панель управления автосервисом"
    site_title = "Автосервис"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('schedule/', self.admin_view(self.schedule_view), name='schedule'),
        ]
        return custom_urls + urls

    def schedule_view(self, request):
        from django.shortcuts import render
        from datetime import datetime, timedelta

        # Генерация данных для графика на неделю
        today = datetime.now().date()
        week_dates = [today + timedelta(days=i) for i in range(7)]

        schedule_data = []
        for date in week_dates:
            day_reservations = Reservations.objects.filter(
                time__date=date,
                status__in=['pending', 'confirmed']
            ).select_related('attendance')

            schedule_data.append({
                'date': date,
                'reservations': day_reservations,
                'is_weekend': date.weekday() >= 5
            })

        context = {
            **self.each_context(request),
            'title': 'График записей',
            'schedule_data': schedule_data,
            'opts': Reservations._meta,
        }

        return render(request, 'admin/schedule_view.html', context)


admin_site = CustomAdminSite(name='custom_admin')
# Регистрируем модели в кастомной админке
admin_site.register(Reservations, ReservationsAdmin)
admin_site.register(WorkSchedule, WorkScheduleAdmin)
