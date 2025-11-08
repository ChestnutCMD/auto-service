from django.db import models


class Attendance(models.Model):
    tittle = models.CharField(max_length=50, verbose_name='Название')
    description = models.TextField(max_length=1000, verbose_name='Описание')
    price = models.PositiveIntegerField(verbose_name='Цена')
    duration = models.DurationField(verbose_name='Длительность')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return self.tittle

    def get_duration_display(self):
        """Красивое отображение длительности"""
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes} мин"


def upload_attendance_photo(instance, filename):
    return f'media/images/attendance_photo/{instance.attendance.id}/{filename}'


class PhotoAttendance(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='photos', verbose_name='Услуга')
    photo = models.ImageField(upload_to=upload_attendance_photo, verbose_name='Фото')

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'

    def __str__(self):
        return f"Фото для {self.attendance.tittle}"
