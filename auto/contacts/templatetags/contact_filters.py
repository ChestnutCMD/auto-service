# contacts/templatetags/contact_filters.py
import re
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def phone_format(value):
    """Форматирует номер телефона в красивый вид"""
    if not value:
        return value

    # Убираем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', value)

    # Проверяем российский номер
    if len(cleaned) == 11 and cleaned[0] in ['7', '8']:
        # Формат: +7 (XXX) XXX-XX-XX
        return f"+7 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:9]}-{cleaned[9:11]}"
    elif len(cleaned) == 10:
        # Формат: +7 (XXX) XXX-XX-XX
        return f"+7 ({cleaned[0:3]}) {cleaned[3:6]}-{cleaned[6:8]}-{cleaned[8:10]}"
    elif len(cleaned) == 12 and cleaned.startswith('+7'):
        # Формат: +7 (XXX) XXX-XX-XX
        return f"+7 ({cleaned[2:5]}) {cleaned[5:8]}-{cleaned[8:10]}-{cleaned[10:12]}"

    # Если не удалось отформатировать, возвращаем как есть
    return value


@register.filter
def get_contact_by_icon(contacts, icon_name):
    """Возвращает контакт по иконке"""
    try:
        for contact in contacts:
            if contact.icon == icon_name:
                return contact
    except (AttributeError, TypeError):
        pass
    return None


@register.filter
def get_contact_value_by_icon(contacts, icon_name):
    """Возвращает значение контакта по иконке"""
    contact = get_contact_by_icon(contacts, icon_name)
    return contact.value if contact else ""


@register.filter
@stringfilter
def format_schedule(value):
    """Форматирует график работы с разными разделителями"""
    if not value:
        return value

    # Убираем лишние пробелы
    value = value.strip()

    # Если уже есть HTML теги, возвращаем как есть
    if '<br>' in value or '<p>' in value:
        return value

    # Разные варианты разделителей
    if ';' in value:
        # Обрабатываем "Пн-Пт: 9:00-20:00 ; Сб-Вс: 10:00-18:00"
        parts = [part.strip() for part in value.split(';') if part.strip()]
        return '<br>'.join(parts)

    elif ',' in value:
        # Обрабатываем запятые
        parts = [part.strip() for part in value.split(',') if part.strip()]
        return '<br>'.join(parts)

    elif '|' in value:
        # Обрабатываем вертикальную черту
        parts = [part.strip() for part in value.split('|') if part.strip()]
        return '<br>'.join(parts)

    # Если нет разделителей, пытаемся разбить по паттерну
    schedule_pattern = r'([А-Яа-яёЁ\-\d]+:\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})'
    matches = re.findall(schedule_pattern, value)
    if matches:
        return '<br>'.join(match.strip() for match in matches)

    # Если ничего не подошло, возвращаем как есть
    return value