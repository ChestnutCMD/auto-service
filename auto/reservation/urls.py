from django.urls import path
from . import views

urlpatterns = [
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('api/calendar-data/', views.get_calendar_data, name='calendar_data'),
    path('api/simple-calendar/', views.get_simple_calendar, name='simple_calendar'),
    path('api/available-time/', views.get_available_time_slots, name='available_time'),
    path('api/booked-slots/', views.get_booked_slots, name='booked_slots'),
    path('api/test/', views.test_api, name='test_api'),
]
