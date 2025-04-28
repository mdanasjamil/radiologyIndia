from django.urls import path
from .views import assigner_dashboard, add_case, assign_physician

from django.urls import path
from .views import assigner_dashboard, add_case, assign_physician

urlpatterns = [
    path('assigner/dashboard/',       assigner_dashboard, name='assigner_dashboard'),
    path('assigner/add-case/',        add_case,          name='add_case'),
    path('assigner/assign-physician/<int:pk>/', assign_physician, name='assign_physician'),
]