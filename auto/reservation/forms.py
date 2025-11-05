from django import forms
from django.utils import timezone
from .models import Reservations, WorkSchedule
from django.core.exceptions import ValidationError


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservations
        fields = ['attendance', 'name', 'phone', 'communication', 'time']
        widgets = {
            'time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'attendance': forms.HiddenInput(),
        }

    def clean_time(self):
        time = self.cleaned_data['time']

        # Проверка на прошедшее время
        if time < timezone.now():
            raise ValidationError('Нельзя создавать запись в прошлом')

        # Проверка рабочего времени (если attendance выбран)
        if 'attendance' in self.cleaned_data and self.cleaned_data['attendance']:
            attendance = self.cleaned_data['attendance']

            # Проверяем рабочее время
            if not WorkSchedule.is_working_time(time, attendance.duration):
                raise ValidationError('Выбранное время вне рабочего графика')

            # Проверяем доступность времени
            if WorkSchedule.is_slot_occupied(time, attendance.duration):
                raise ValidationError('Это время уже занято')

        return time