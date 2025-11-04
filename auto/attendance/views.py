from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect
import re

from contacts.contacts import COMPANY_INFO
from contacts.models import Contact
from reservation.forms import ReservationForm
from reservation.models import WorkSchedule
from .models import Attendance


def extract_phone_number(value):
    """Извлекает номер телефона из строки"""
    if not value:
        return None

    cleaned = re.sub(r'[^\d+]', '', value)
    phone_pattern = r'^(\+7|7|8)?(\d{3})(\d{3})(\d{2})(\d{2})$'
    match = re.match(phone_pattern, cleaned)

    if match:
        groups = match.groups()
        return f"+7 ({groups[1]}) {groups[2]}-{groups[3]}-{groups[4]}"

    return None


def home(request):
    services = Attendance.objects.filter(is_active=True).prefetch_related('photos')
    contacts = Contact.objects.filter(is_active=True)

    # Обработка формы бронирования
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            try:
                reservation = form.save(commit=False)

                # Проверяем рабочее время
                if not is_working_time(reservation.time, reservation.attendance.duration):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': 'Выбранное время вне рабочего графика'
                        })
                    else:
                        messages.error(request, 'Выбранное время вне рабочего графика')
                else:
                    reservation.save()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'Заявка на бронирование успешно создана! Мы свяжемся с вами для подтверждения.'
                        })
                    else:
                        messages.success(request,
                                         'Заявка на бронирование успешно создана! Мы свяжемся с вами для подтверждения.')
                        return redirect('home')
            except ValidationError as e:
                error_message = str(e)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message
                    })
                else:
                    messages.error(request, error_message)
        else:
            # Форма не валидна
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [{'message': error} for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Пожалуйста, исправьте ошибки в форме'
                })
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = ReservationForm()

    # Ищем основной телефон
    main_phone = None
    phone_contacts = contacts.filter(icon='fas fa-phone')

    for contact in phone_contacts:
        phone_number = extract_phone_number(contact.value)
        if phone_number:
            main_phone = contact
            main_phone.formatted_value = phone_number
            break

    if not main_phone:
        for contact in contacts:
            phone_number = extract_phone_number(contact.value)
            if phone_number:
                main_phone = contact
                main_phone.formatted_value = phone_number
                break

    context = {
        'services': services,
        'contacts': contacts,
        'main_phone': main_phone,
        'company_info': COMPANY_INFO,
        'title': f'{COMPANY_INFO["NAME"]} - Главная',
        'form': form,
    }
    return render(request, 'services/home.html', context)


def is_working_time(start_time, duration):
    """Проверяет, попадает ли время бронирования в рабочие часы"""
    end_time = start_time + duration
    day_of_week = start_time.weekday()

    try:
        schedule = WorkSchedule.objects.get(day_of_week=day_of_week)
        if not schedule.is_working:
            return False

        # Преобразуем время в time для сравнения
        start_time_only = start_time.time()
        end_time_only = end_time.time()

        return (start_time_only >= schedule.start_time and
                end_time_only <= schedule.end_time)
    except WorkSchedule.DoesNotExist:
        return False