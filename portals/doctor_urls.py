from django.urls import path

from . import views
from .views import doctor_dashboard, add_report, download_case_files

urlpatterns = [
    path('dashboard/',                  doctor_dashboard,    name='doctor_dashboard'),

    path('report/<str:patient_id>/submit/', views.add_report,    name='add_report'),

    # download the final report:
    path('report/<str:patient_id>/edit/', views.add_or_edit_report, name='edit_report'),
    path('report/<str:patient_id>/download/', views.download_report, name='download_report'),

    # download the DICOM .zip
    path('download-case/<str:patient_id>/', download_case_files, name='doctor_download'),
]
