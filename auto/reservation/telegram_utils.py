import requests
import json
from django.conf import settings
from django.utils import timezone


def send_telegram_notification(reservation):
    """
    Отправляет уведомление о новой заявке в Telegram
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)

    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID not configured")
        return False

    try:
        # Форматируем сообщение
        message = format_reservation_message(reservation)

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        return True

    except requests.exceptions.RequestException as e:
        print(f"Telegram API error: {e}")
        return False
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False


def format_reservation_message(reservation):
    """
    Форматирует сообщение о бронировании для Telegram
    """
    # Форматируем время
    time_str = reservation.time.strftime('%d.%m.%Y в %H:%M')
    created_at_str = reservation.created_at.strftime('%d.%m.%Y в %H:%M')

    # Форматируем способ связи
    communication_map = {
        'phone': '📞 Телефон',
        'whatsapp': '💚 WhatsApp'
    }
    communication = communication_map.get(reservation.communication, reservation.communication)

    message = (
        "🆕 <b>НОВАЯ ЗАЯВКА</b>\n\n"
        f"<b>Услуга:</b> {reservation.attendance.tittle}\n"
        f"<b>Клиент:</b> {reservation.name}\n"
        f"<b>Телефон:</b> <code>{reservation.phone}</code>\n"
        f"<b>Способ связи:</b> {communication}\n"
        f"<b>Заявка создана:</b> {created_at_str}\n"
        f"<b>Статус:</b> {reservation.get_status_display()}"
    )

    return message


def send_telegram_alert(message):
    """
    Отправляет простое текстовое сообщение в Telegram
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)

    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        return True

    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False