from datetime import timedelta, datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from attendance.models import Attendance
from .email_utils import send_email_notification
from .telegram_utils import send_telegram_notification

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
        # Проверяем что time установлен
        if not self.time:
            raise ValidationError('Время не указано')

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
            send_telegram_notification(self)
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
        try:
            send_email_notification(self)
        except Exception as e:
            print(f"Failed to send Email notification: {e}")

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

    @classmethod
    def get_working_datetime_slots(cls, date, service_duration):
        """Возвращает список доступных временных слотов для даты"""
        try:
            schedule = cls.objects.get(day_of_week=date.weekday(), is_working=True)
        except cls.DoesNotExist:
            return []

        slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)

        slot_duration = timedelta(minutes=30)

        while current_time + service_duration <= end_time:
            if not cls.is_slot_occupied(current_time, service_duration):
                slots.append(current_time)
            current_time += slot_duration

        return slots

    @classmethod
    def get_available_dates(cls, days_ahead=30):
        """Возвращает список дат, когда есть рабочие дни"""
        available_dates = []
        today = timezone.now().date()

        for i in range(days_ahead):
            date = today + timedelta(days=i)
            try:
                schedule = cls.objects.get(day_of_week=date.weekday(), is_working=True)
                available_dates.append(date)
            except cls.DoesNotExist:
                continue
        return available_dates

    @classmethod
    def get_available_dates_simple(cls, days_ahead=30):
        """Упрощенная версия получения доступных дат"""
        available_dates = []
        today = timezone.now().date()

        for i in range(days_ahead):
            date = today + timedelta(days=i)
            try:
                schedule = cls.objects.get(day_of_week=date.weekday(), is_working=True)
                available_dates.append(date)
            except cls.DoesNotExist:
                continue

        return available_dates

    @classmethod
    def is_working_time_simple(cls, start_time, duration):
        """Упрощенная проверка рабочего времени"""
        try:
            schedule = cls.objects.get(day_of_week=start_time.weekday(), is_working=True)
            end_time = start_time + duration

            start_time_only = start_time.time()
            end_time_only = end_time.time()

            return (start_time_only >= schedule.start_time and
                    end_time_only <= schedule.end_time)
        except cls.DoesNotExist:
            return False

    @classmethod
    def is_working_time(cls, start_time, duration):
        """Проверяет, попадает ли время бронирования в рабочие часы"""
        try:
            # Получаем расписание для дня недели
            schedule = cls.objects.get(day_of_week=start_time.weekday(), is_working=True)

            # Вычисляем время окончания услуги
            end_time = start_time + duration

            # Преобразуем в time для сравнения
            start_time_only = start_time.time()
            end_time_only = end_time.time()

            # Проверяем, что время попадает в рабочие часы
            return (start_time_only >= schedule.start_time and
                    end_time_only <= schedule.end_time)

        except cls.DoesNotExist:
            # Если расписание не найдено для этого дня, день не рабочий
            return False

    @classmethod
    def is_slot_occupied(cls, start_time, duration):
        """Проверяет, занят ли временной слот"""
        from .models import Reservations

        end_time = start_time + duration

        # Ищем пересекающиеся бронирования
        overlapping = Reservations.objects.filter(
            time__lt=end_time,
            time__gte=start_time,
            status__in=['pending', 'confirmed']
        ).exists()

        return overlapping