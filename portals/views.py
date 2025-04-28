import os, zipfile, uuid, tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from .models import Patient
from .forms import AddCaseForm, AssignPhysicianForm
from django.contrib.auth import get_user_model

User = get_user_model()

import os, zipfile, uuid, tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from .models import Patient
from .forms import AddCaseForm, AssignPhysicianForm
from django.contrib.auth import get_user_model

User = get_user_model()

def is_assigner(user):
    return user.is_authenticated and user.role == 'assigner'

@login_required
@user_passes_test(is_assigner)
def assigner_dashboard(request):
    form = AddCaseForm()
    assign_form = AssignPhysicianForm()
    # list all patients or filter by status
    status = request.GET.get('status')
    qs = Patient.objects.all()
    if status:
        qs = qs.filter(status=status)
    patients = qs.order_by('-receiving_date')

    return render(request, 'portals/assigner_dashboard.html', {
        'patients': patients,
        'add_case_form': form,
        'assign_form': assign_form,
    })

@login_required
@user_passes_test(is_assigner)
def add_case(request):
    if request.method == 'POST':
        form = AddCaseForm(request.POST, request.FILES)
        if form.is_valid():
            # save patient without committing to set patient_id
            patient = form.save(commit=False)
            patient.patient_id = str(uuid.uuid4())
            # save before counting images
            patient.save()
            # handle zip
            zipf = request.FILES['zip_file']
            tmpdir = tempfile.mkdtemp()
            path = os.path.join(tmpdir, zipf.name)
            with open(path, 'wb') as f:
                for chunk in zipf.chunks(): f.write(chunk)
            extract_dir = os.path.join(settings.MEDIA_ROOT, 'cases', patient.patient_id)
            os.makedirs(extract_dir, exist_ok=True)
            count = 0
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                for root, _, files in os.walk(extract_dir):
                    for fn in files:
                        if fn.lower().endswith('.dcm'):
                            count += 1
            patient.number_of_images = count
            patient.save()
        return redirect('assigner_dashboard')
    return redirect('assigner_dashboard')

@login_required
@user_passes_test(is_assigner)
def assign_physician(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = AssignPhysicianForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['physician']
            patient.preferred_physician = doctor
            patient.status = 'assigned'
            patient.save()
    return redirect('assigner_dashboard')