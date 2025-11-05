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

        # Получаем занятые слоты на эту дату
        booked_slots = Reservations.objects.filter(
            time__date=date_obj,
            status__in=['pending', 'confirmed']
        ).select_related('attendance')

        # Создаем множество занятых времен
        booked_times = set()
        for reservation in booked_slots:
            # Добавляем все время от начала до конца услуги
            current_time = reservation.time
            end_time = reservation.time + reservation.attendance.duration

            while current_time < end_time:
                booked_times.add(current_time.strftime('%Y-%m-%dT%H:%M'))
                current_time += timedelta(minutes=30)  # 30-минутные интервалы

        # Генерируем доступные слоты
        slots = []
        for hour in range(9, 18):
            for minute in [0, 30]:  # Слоты каждые 30 минут
                slot_time_str = f"{date_str}T{hour:02d}:{minute:02d}"

                # Проверяем что время не занято
                if slot_time_str not in booked_times:
                    # Создаем datetime для проверки что время в будущем
                    slot_datetime = datetime.strptime(slot_time_str, '%Y-%m-%dT%H:%M')
                    slot_datetime_aware = timezone.make_aware(slot_datetime)

                    if slot_datetime_aware > now:
                        slots.append({
                            'datetime': slot_time_str,
                            'display': f"{hour:02d}:{minute:02d}"
                        })

        return JsonResponse({
            'date': date_str,
            'slots': slots
        })

    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)
    except Exception as e:
        print(f"Error in get_available_time_slots: {str(e)}")
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
        print(f"Error in get_calendar_data: {str(e)}")  # Для отладки
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


def get_available_dates_simple(days_ahead=30):
    """Упрощенная функция для получения доступных дат"""
    available_dates = []
    today = timezone.now().date()

    for i in range(days_ahead):
        date = today + timedelta(days=i)
        # Простая логика: рабочие дни - с понедельника по пятницу
        if date.weekday() < 5:  # 0-4 = понедельник-пятница
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
    """API для получения временных слотов"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    date_str = request.GET.get('date')
    service_id = request.GET.get('service_id')

    if not date_str or not service_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        # Создаем date объект
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        now = timezone.now()

        slots = []
        for hour in range(9, 18):
            # Создаем timezone-aware datetime для слота
            slot_time = timezone.make_aware(
                datetime.combine(date_obj, time(hour, 0))
            )

            # Правильное сравнение
            if slot_time > now:
                slots.append({
                    'datetime': slot_time.strftime('%Y-%m-%dT%H:%M'),
                    'display': slot_time.strftime('%H:%M')
                })

        return JsonResponse({
            'date': date_str,
            'slots': slots
        })

    except Exception as e:
        print(f"Error in get_available_time_slots: {str(e)}")
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
        print(f"Error in get_booked_slots: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)