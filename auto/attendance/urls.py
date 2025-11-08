from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='services_list'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
]
