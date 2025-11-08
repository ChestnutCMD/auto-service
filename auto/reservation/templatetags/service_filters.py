from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def format_service_description(value):
    """
    Форматирует описание услуги:
    - Сохраняет переносы строк
    - Форматирует списки
    - Добавляет жирный текст между **
    """
    if not value:
        return ""

    # Заменяем **текст** на <strong>текст</strong>
    value = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', value)

    # Заменяем переносы строк на <br>
    value = value.replace('\n', '<br>')

    # Форматируем списки (строки начинающиеся с - или *)
    lines = value.split('<br>')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if line.startswith('- ') or line.startswith('* '):
            formatted_lines.append(f'• {line[2:]}')
        else:
            formatted_lines.append(line)

    return mark_safe('<br>'.join(formatted_lines))


@register.filter
def safe_linebreaks(value):
    """Безопасное преобразование переносов строк"""
    if not value:
        return ""
    return mark_safe(value.replace('\n', '<br>'))