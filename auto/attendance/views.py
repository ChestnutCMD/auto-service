from django.shortcuts import render

from attendance.models import Attendance


def services_list(request):
    services = Attendance.objects.filter(is_active=True).prefetch_related('photos')

    context = {
        'services': services,
        'title': 'Услуги автосервиса'
    }
    return render(request, 'attendance/attendance_list.html', context)
