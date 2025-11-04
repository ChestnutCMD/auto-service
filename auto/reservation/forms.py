from django import forms
from django.utils import timezone
from .models import Reservations, Attendance
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
        if time < timezone.now():
            raise ValidationError('Нельзя создавать запись в прошлом')
        return time