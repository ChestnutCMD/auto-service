from django import forms
from datetime import timedelta

from attendance.models import Attendance


class AttendanceAdminForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(
        min_value=1,
        label='Длительность (минуты)',
        help_text='Введите длительность в минутах'
    )

    class Meta:
        model = Attendance
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['duration_minutes'] = int(self.instance.duration.total_seconds() // 60)
        else:
            self.initial['duration_minutes'] = 60

    def save(self, commit=True):
        attendance = super().save(commit=False)
        minutes = self.cleaned_data['duration_minutes']
        attendance.duration = timedelta(minutes=minutes)

        if commit:
            attendance.save()
        return attendance