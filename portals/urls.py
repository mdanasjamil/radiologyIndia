from django.urls import path

from . import views
from .views import (
    assigner_dashboard,
    add_case,
    assign_physician,
    download_case_files,
    doctor_dashboard,
    add_report,
)

urlpatterns = [
    path('dashboard/',       assigner_dashboard, name='dashboard'),
    path('add-case/',        add_case,            name='add_case'),
    path('assign-physician/<int:patient_id>/', assign_physician, name='assign_physician'),
    path('download-case/<str:patient_id>/', download_case_files, name='download_case_files'),
    path('report/<str:patient_id>/',  views.edit_report,    name='edit_report'),
    path('report/download/<str:patient_id>/', views.download_report, name='download_report'),

    # doctor
    path('dashboard/', doctor_dashboard, name='doctor_dashboard'),
    path('create-report/<int:patient_id>/', add_report, name='add_report'),
]