# portals/admin.py

from django.contrib import admin
from .models import Patient, DicomFile, Report

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display  = (
        'patient_id',
        'patient_name',
        'status',
        'number_of_images',
        'receiving_date',
    )
    list_filter   = (
        'status',
        'receiving_date',
    )
    search_fields = (
        'patient_id',
        'patient_name',
    )

@admin.register(DicomFile)
class DicomFileAdmin(admin.ModelAdmin):
    list_display = (
        'patient',
        'file',
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display  = (
        'patient',
        'author',
        'created_at',
    )
    list_filter   = (
        'created_at',
    )
    search_fields = (
        'patient__patient_id',
        'author__username',
    )
