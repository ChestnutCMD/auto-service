import re


def format_phone_number(value):
    """Форматирует номер телефона в единый формат"""
    if not value:
        return None

    # Убираем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', value)

    # Проверяем формат российского номера
    phone_pattern = r'^(\+7|7|8)?(\d{3})(\d{3})(\d{2})(\d{2})$'
    match = re.match(phone_pattern, cleaned)

    if match:
        groups = match.groups()
        return f"+7 ({groups[1]}) {groups[2]}-{groups[3]}-{groups[4]}"

    return value


def is_phone_number(value):
    """Проверяет, является ли строка номером телефона"""
    if not value:
        return False

    cleaned = re.sub(r'[^\d+]', '', value)
    phone_pattern = r'^(\+7|7|8)?(\d{3})(\d{3})(\d{2})(\d{2})$'
    return bool(re.match(phone_pattern, cleaned))