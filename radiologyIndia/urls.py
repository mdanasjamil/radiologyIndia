from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',      include('accounts.urls')),   # landing, signup, login, logout
    path('', include('portals.urls')),   # now serves /doctor/dashboard & /assigner/dashboard
]
