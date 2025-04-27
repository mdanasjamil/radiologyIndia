from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def doctor_dashboard(request):
    return render(request, 'portals/doctor_dashboard.html')

@login_required
def assigner_dashboard(request):
    return render(request, 'portals/assigner_dashboard.html')
