import calendar
from datetime import datetime, timedelta, time

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from attendance.models import Attendance
from contacts.contacts import COMPANY_INFO
from reservation.models import WorkSchedule, Reservations


def privacy_policy(request):
    """
    Страница политики конфиденциальности
    """
    context = {
        'title': f'{COMPANY_INFO["NAME"]} - Политика конфиденциальности',
        'company_info': COMPANY_INFO,
    }
    return render(request, 'privacy/privacy.html', context)


@csrf_exempt
def get_available_time_slots(request):
    """API для получения доступных временных слотов с учетом занятых"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    date_str = request.GET.get('date')
    service_id = request.GET.get('service_id')

    if not date_str or not service_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        # Получаем услугу
        service = Attendance.objects.get(id=service_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        now = timezone.now()

        # Получаем ВСЕ бронирования на эту дату
        booked_reservations = Reservations.objects.filter(
            time__date=date_obj,
            status__in=['pending', 'confirmed']
        ).select_related('attendance')

        # Создаем множество ЗАБЛОКИРОВАННЫХ временных слотов
        blocked_slots = set()

        for reservation in booked_reservations:
            start_time = reservation.time
            end_time = reservation.time + reservation.attendance.duration

            # Блокируем все 30-минутные слоты в этом интервале
            current_slot = start_time
            while current_slot < end_time:
                slot_key = current_slot.strftime('%H:%M')
                blocked_slots.add(slot_key)
                current_slot += timedelta(minutes=30)

        all_slots = []
        base_date = datetime.combine(date_obj, time(0, 0))

        for hour in range(9, 18):
            for minute in [0, 30]:
                slot_time = timezone.make_aware(base_date.replace(hour=hour, minute=minute))
                all_slots.append(slot_time)

        # Фильтруем доступные слоты
        available_slots = []

        for slot_time in all_slots:
            slot_key = slot_time.strftime('%H:%M')

            # Проверяем что время в будущем
            if slot_time <= now:
                continue

            # Проверяем что слот не заблокирован
            if slot_key in blocked_slots:
                continue

            # Дополнительная проверка: убеждаемся что вся услуга помещается
            # без пересечения с другими бронированиями
            slot_end_time = slot_time + service.duration
            has_conflict = False

            for reservation in booked_reservations:
                res_start = reservation.time
                res_end = reservation.time + reservation.attendance.duration

                # Проверяем пересечение: (start1 < end2) and (start2 < end1)
                if (slot_time < res_end) and (res_start < slot_end_time):
                    has_conflict = True
                    break

            if not has_conflict:
                available_slots.append({
                    'datetime': slot_time.strftime('%Y-%m-%dT%H:%M'),
                    'display': slot_key
                })

        return JsonResponse({
            'date': date_str,
            'slots': available_slots,
            'debug': {
                'total_slots': len(all_slots),
                'booked_reservations': booked_reservations.count(),
                'blocked_slots_count': len(blocked_slots),
                'blocked_slots_list': list(blocked_slots),
                'available_slots': len(available_slots)
            }
        })

    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=400)

def get_available_dates(request):
    """API endpoint для получения доступных дат"""
    service_id = request.GET.get('service_id')

    if not service_id:
        return JsonResponse({'error': 'Missing service_id'}, status=400)

    try:
        service = Attendance.objects.get(id=service_id)
        available_dates = WorkSchedule.get_available_dates()

        dates_list = [date.strftime('%Y-%m-%d') for date in available_dates]

        return JsonResponse({
            'dates': dates_list,
            'service_duration_minutes': service.duration.total_seconds() // 60
        })

    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)


@csrf_exempt
def get_calendar_data(request):
    """API для получения данных календаря с доступными датами"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    service_id = request.GET.get('service_id')

    if not service_id:
        return JsonResponse({'error': 'Missing service_id'}, status=400)

    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid year or month'}, status=400)

    try:
        service = Attendance.objects.get(id=service_id)
        calendar_data = generate_calendar_data(year, month, service)
        return JsonResponse(calendar_data)

    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def generate_calendar_data(year, month, service):
    """Генерирует данные календаря с отметками доступных дат"""
    # Создаем объект календаря
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    # Получаем доступные даты
    available_dates = get_available_dates_simple(60)
    available_dates_set = set(available_dates)

    # Форматируем данные для календаря
    calendar_weeks = []

    for week in month_days:
        calendar_week = []
        for day in week:
            if day == 0:
                calendar_week.append({'day': '', 'available': False, 'current_month': False})
            else:
                date = datetime(year, month, day).date()
                # Используем timezone-aware сравнение
                today = timezone.now().date()
                is_available = date in available_dates_set and date >= today
                calendar_week.append({
                    'day': day,
                    'available': is_available,
                    'current_month': True,
                    'date': date.strftime('%Y-%m-%d')
                })
        calendar_weeks.append(calendar_week)

    # Получаем доступные временные слоты
    time_slots = get_sample_time_slots()

    return {
        'year': year,
        'month': month,
        'month_name': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                       'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month - 1],
        'weeks': calendar_weeks,
        'time_slots': time_slots,
        'today': timezone.now().date().strftime('%Y-%m-%d')
    }


def get_available_dates_simple(days_ahead=60):
    """Упрощенная функция для получения доступных дат с учетом рабочего графика"""
    available_dates = []
    today = timezone.now().date()

    working_days = WorkSchedule.objects.filter(is_working=True).values_list('day_of_week', flat=True)
    working_days_set = set(working_days)

    for i in range(days_ahead):
        date = today + timedelta(days=i)
        day_of_week = date.weekday()

        if day_of_week in working_days_set:
            available_dates.append(date)

    return available_dates

def get_sample_time_slots():
    """Возвращает примерные временные слоты"""
    slots = []
    # Используем timezone-aware datetime
    base_time = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)

    for i in range(10):
        slot_time = base_time + timedelta(hours=i)
        # Правильное сравнение timezone-aware объектов
        if slot_time > timezone.now():
            slots.append({
                'datetime': slot_time.strftime('%Y-%m-%dT%H:%M'),
                'display': slot_time.strftime('%H:%M')
            })

    return slots


@csrf_exempt
def get_available_time_slots(request):
    """API для получения доступных временных слотов с учетом занятых и рабочего графика"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    date_str = request.GET.get('date')
    service_id = request.GET.get('service_id')

    if not date_str or not service_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        # Получаем услугу
        service = Attendance.objects.get(id=service_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        now = timezone.now()

        # Получаем рабочий график на этот день
        try:
            work_schedule = WorkSchedule.objects.get(
                day_of_week=date_obj.weekday(),
                is_working=True
            )
            work_start = work_schedule.start_time
            work_end = work_schedule.end_time
        except WorkSchedule.DoesNotExist:
            return JsonResponse({
                'date': date_str,
                'slots': [],
                'error': 'В этот день сервис не работает'
            })

        # Получаем ВСЕ бронирования на эту дату
        booked_reservations = Reservations.objects.filter(
            time__date=date_obj,
            status__in=['pending', 'confirmed']
        ).select_related('attendance')

        # Создаем список занятых интервалов
        booked_intervals = []
        for reservation in booked_reservations:
            start_time = reservation.time
            end_time = reservation.time + reservation.attendance.duration
            booked_intervals.append({
                'start': start_time,
                'end': end_time
            })

        # Генерируем слоты каждые 30 минут в рабочее время
        available_slots = []
        current_time = timezone.make_aware(
            datetime.combine(date_obj, work_start)
        )
        work_end_time = timezone.make_aware(
            datetime.combine(date_obj, work_end)
        )

        slot_duration = timedelta(minutes=30)

        while current_time + service.duration <= work_end_time:
            slot_end_time = current_time + service.duration

            # Проверяем что время в будущем
            if current_time <= now:
                current_time += slot_duration
                continue

            # Проверяем что слот не пересекается с занятыми интервалами
            is_available = True
            for interval in booked_intervals:
                # Проверяем пересечение: (start1 < end2) and (start2 < end1)
                if (current_time < interval['end']) and (interval['start'] < slot_end_time):
                    is_available = False
                    break

            if is_available:
                available_slots.append({
                    'datetime': current_time.strftime('%Y-%m-%dT%H:%M'),
                    'display': current_time.strftime('%H:%M')
                })

            current_time += slot_duration

        return JsonResponse({
            'date': date_str,
            'slots': available_slots,
            'work_schedule': {
                'start': work_start.strftime('%H:%M'),
                'end': work_end.strftime('%H:%M')
            }
        })

    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def test_api(request):
    """Тестовый endpoint для проверки API"""
    return JsonResponse({
        'status': 'ok',
        'message': 'API is working',
        'timestamp': timezone.now().isoformat()
    })


@csrf_exempt
def get_simple_calendar(request):
    """Упрощенный API календаря без зависимостей от моделей"""
    try:
        year = int(request.GET.get('year', timezone.now().year))
        month = int(request.GET.get('month', timezone.now().month))

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        today = timezone.now().date()

        calendar_weeks = []
        for week in month_days:
            calendar_week = []
            for day in week:
                if day == 0:
                    calendar_week.append({'day': '', 'available': False, 'current_month': False})
                else:
                    date = datetime(year, month, day).date()
                    # Все будущие дни доступны для упрощения
                    is_available = date >= today
                    calendar_week.append({
                        'day': day,
                        'available': is_available,
                        'current_month': True,
                        'date': date.strftime('%Y-%m-%d')
                    })
            calendar_weeks.append(calendar_week)

        # Примерные временные слоты
        time_slots = []
        for hour in range(9, 18):
            time_slots.append({
                'datetime': f'2025-11-06T{hour:02d}:00',
                'display': f'{hour:02d}:00'
            })

        return JsonResponse({
            'year': year,
            'month': month,
            'month_name': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                           'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month - 1],
            'weeks': calendar_weeks,
            'time_slots': time_slots,
            'today': today.strftime('%Y-%m-%d')
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_booked_slots(request):
    """API для получения занятых временных слотов"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Получаем все подтвержденные и ожидающие бронирования
        booked_reservations = Reservations.objects.filter(
            status__in=['pending', 'confirmed']
        ).select_related('attendance')

        booked_slots = []

        for reservation in booked_reservations:
            end_time = reservation.time + reservation.attendance.duration
            booked_slots.append({
                'start': reservation.time.isoformat(),
                'end': end_time.isoformat(),
                'service_id': reservation.attendance.id
            })

        return JsonResponse({
            'booked_slots': booked_slots
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)