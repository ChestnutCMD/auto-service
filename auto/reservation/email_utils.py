from django.core.mail import send_mail

from auto import settings


def send_email_notification(reservation):
    """
    Отправляет уведомление о новой заявке на email
    """
    notification_email = getattr(settings, 'NOTIFICATION_EMAIL', None)

    if not notification_email:
        print("Notification email not configured")
        return False

    try:
        subject = f"Новая заявка на {reservation.attendance.tittle}"

        html_message = format_reservation_email_html(reservation)
        plain_message = format_reservation_email_text(reservation)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[notification_email],
            html_message=html_message,
            fail_silently=False,
        )

        print(f"Email notification sent to {notification_email}")
        return True

    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False


def format_reservation_email_text(reservation):
    """
    Форматирует текстовую версию сообщения для email
    (аналогично Telegram, но без HTML-тегов)
    """

    time_str = reservation.time.strftime('%d.%m.%Y в %H:%M')
    created_at_str = reservation.created_at.strftime('%d.%m.%Y в %H:%M')

    communication_map = {
        'phone': 'Телефон',
        'whatsapp': 'WhatsApp'
    }
    communication = communication_map.get(reservation.communication, reservation.communication)

    message = (
        "🆕 НОВАЯ ЗАЯВКА\n\n"
        f"Услуга: {reservation.attendance.tittle}\n"
        f"Клиент: {reservation.name}\n"
        f"Телефон: {reservation.phone}\n"
        f"Способ связи: {communication}\n"
        f"Время: {time_str}\n"
        f"Дата создания: {created_at_str}\n"
    )

    return message


def format_reservation_email_html(reservation):
    """
    Форматирует HTML-версию сообщения для email
    (стилизованная версия, похожая на Telegram)
    """

    time_str = reservation.time.strftime('%d.%m.%Y в %H:%M')
    created_at_str = reservation.created_at.strftime('%d.%m.%Y в %H:%M')

    communication_map = {
        'phone': '📞 Телефон',
        'whatsapp': '💚 WhatsApp'
    }
    communication = communication_map.get(reservation.communication, reservation.communication)

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 10px;
            }}
            .header {{
                background-color: #26a69a;
                color: white;
                padding: 15px;
                border-radius: 10px 10px 0 0;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 0 0 10px 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .field {{
                margin-bottom: 12px;
                padding: 8px;
                border-bottom: 1px solid #eee;
            }}
            .label {{
                font-weight: bold;
                color: #26a69a;
                display: inline-block;
                width: 120px;
            }}
            .value {{
                display: inline-block;
                margin-left: 10px;
            }}
            .phone {{
                font-family: monospace;
                font-size: 16px;
                background-color: #f5f5f5;
                padding: 3px 8px;
                border-radius: 4px;
            }}
            .footer {{
                margin-top: 20px;
                padding-top: 10px;
                text-align: center;
                font-size: 12px;
                color: #999;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🆕 НОВАЯ ЗАЯВКА</h2>
            </div>
            <div class="content">
                <div class="field">
                    <span class="label">📋 Услуга:</span>
                    <span class="value">{reservation.attendance.tittle}</span>
                </div>
                <div class="field">
                    <span class="label">👤 Клиент:</span>
                    <span class="value">{reservation.name}</span>
                </div>
                <div class="field">
                    <span class="label">📞 Телефон:</span>
                    <span class="value phone">{reservation.phone}</span>
                </div>
                <div class="field">
                    <span class="label">💬 Способ связи:</span>
                    <span class="value">{communication}</span>
                </div>
                <div class="field">
                    <span class="label">⏰ Время:</span>
                    <span class="value">{time_str}</span>
                </div>
                <div class="field">
                    <span class="label">📅 Дата создания:</span>
                    <span class="value">{created_at_str}</span>
                </div>
            </div>
            <div class="footer">
                Это автоматическое уведомление с сайта
            </div>
        </div>
    </body>
    </html>
    """

    return html_message


def send_email_alert(subject, message):
    """
    Отправляет простое текстовое сообщение на email (аналог send_telegram_alert)
    """
    notification_email = getattr(settings, 'NOTIFICATION_EMAIL', None)

    if not notification_email:
        print("Notification email not configured")
        return False

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[notification_email],
            fail_silently=False,
        )
        print(f"Email alert sent to {notification_email}")
        return True

    except Exception as e:
        print(f"Error sending email alert: {e}")
        return False
