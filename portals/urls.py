from django.urls import path
from . import views

urlpatterns = [
    path('doctor/dashboard/',   views.doctor_dashboard,   name='doctor_dashboard'),
    path('assigner/dashboard/', views.assigner_dashboard, name='assigner_dashboard'),
]
