from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from attendance.models import Attendance


class Reservations(models.Model):
    COMMUNICATION_CHOICES = (
        ('phone', 'Телефон'),
        ('whatsapp', 'Ватсап')
    )
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, verbose_name='Услуга')
    name = models.CharField(max_length=255, verbose_name='Имя клиента')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    communication = models.CharField(choices=COMMUNICATION_CHOICES, max_length=10, verbose_name='Предпочтительный способ связи')
    time = models.DateTimeField(verbose_name='Время приема')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания заявки')
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена')
    ], verbose_name='Статус')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-time']

    def __str__(self):
        return f"{self.attendance} - {self.name} - {self.time.strftime('%d.%m.%Y %H:%M')}"

    def clean(self):
        # Проверка на пересечение времени
        if self.time < timezone.now():
            raise ValidationError('Нельзя создавать запись в прошлом')

        overlapping = Reservations.objects.filter(
            time__lt=self.time + self.attendance.duration,
            time__gte=self.time,
            status__in=['pending', 'confirmed']
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError('Это время уже занято')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.send_creation_notification()

    def send_creation_notification(self):
        """
        Отправляет уведомление о создании новой заявки
        """
        try:
            from .telegram_utils import send_telegram_notification
            send_telegram_notification(self)
        except Exception as e:
            # Логируем ошибку, но не прерываем сохранение
            print(f"Failed to send Telegram notification: {e}")


class WorkSchedule(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Время начала работы')
    end_time = models.TimeField(verbose_name='Время окончания работы')
    is_working = models.BooleanField(default=True, verbose_name='Рабочий день')

    class Meta:
        verbose_name = 'Рабочий график'
        verbose_name_plural = 'Рабочий график'
        ordering = ['day_of_week']

    def __str__(self):
        return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"
