from django.urls import path

from . import views
from .views import (
    assigner_dashboard,
    add_case,
    assign_physician,
    download_case_files,
)

urlpatterns = [
    path('dashboard/',                  assigner_dashboard,   name='assigner_dashboard'),
    path('add-case/',                   add_case,            name='add_case'),
    path('assign-physician/<int:patient_id>/', assign_physician, name='assign_physician'),
    path('download-case/<str:patient_id>/',      download_case_files, name='download_case_files'),
    path('report/<str:patient_id>/download/', views.assigner_download_report, name='download_report'),

]
