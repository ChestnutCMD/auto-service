import json
import re

from django.shortcuts import render

from attendance.models import Attendance
from contacts.models import Contact


def extract_phone_number(value):
    """Извлекает номер телефона из строки"""
    if not value:
        return None

    # Убираем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', value)

    # Проверяем формат российского номера
    phone_pattern = r'^(\+7|7|8)?(\d{3})(\d{3})(\d{2})(\d{2})$'
    match = re.match(phone_pattern, cleaned)

    if match:
        # Форматируем в красивый вид: +7 (999) 123-45-67
        groups = match.groups()
        return f"+7 ({groups[1]}) {groups[2]}-{groups[3]}-{groups[4]}"

    return None


def home(request):
    services = Attendance.objects.filter(is_active=True).prefetch_related('photos')
    contacts = Contact.objects.filter(is_active=True)

    # Ищем основной телефон
    main_phone = None

    # Сначала ищем контакт с иконкой телефона
    phone_contacts = contacts.filter(icon='fas fa-phone')
    for contact in phone_contacts:
        phone_number = extract_phone_number(contact.value)
        if phone_number:
            main_phone = contact
            main_phone.formatted_value = phone_number
            break

    # Если не нашли, ищем любой контакт с номером телефона
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
        'title': 'Автосервис - Главная'
    }
    return render(request, 'services/home.html', context)
