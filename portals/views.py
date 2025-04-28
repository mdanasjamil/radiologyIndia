import os
import uuid
import zipfile
import tempfile
import shutil
import io
import os
import zipfile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Patient
from .forms import AddCaseForm, AssignPhysicianForm
import os, zipfile, uuid, tempfile, shutil
from django.shortcuts   import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf       import settings

from .models import Patient
from .forms  import AddCaseForm
from .models import Patient, CaseFile


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
    qs = Patient.objects.all()

    # — Filters —
    filters = {
        'status': request.GET.get('status', ''),
        'modality': request.GET.get('modality', ''),
        'sex': request.GET.get('sex', ''),
        'age_min': request.GET.get('age_min', ''),
        'age_max': request.GET.get('age_max', ''),
    }

    # Apply filters to the queryset
    if filters['status']:
        qs = qs.filter(status=filters['status'])
    if filters['modality']:
        qs = qs.filter(modality=filters['modality'])
    if filters['sex']:
        qs = qs.filter(sex=filters['sex'])
    if filters['age_min']:
        qs = qs.filter(age__gte=filters['age_min'])
    if filters['age_max']:
        qs = qs.filter(age__lte=filters['age_max'])

    # — Sorting —
    ALLOWED = ['patient_id', 'receiving_date', 'age', 'modality']
    sort = request.GET.get('sort', 'patient_id')  # Default to patient_id
    if sort not in ALLOWED:
        sort = 'patient_id'
    direction = request.GET.get('dir', 'desc')  # Default direction is 'desc' (newest first)
    order = sort if direction == 'asc' else f'-{sort}'
    qs = qs.order_by(order)

    patients = qs
    doctors = User.objects.filter(role='doctor')

    return render(request, 'portals/assigner_dashboard.html', {
        'patients': patients,
        'add_case_form': form,
        'doctors': doctors,
        'filters': filters,
        'sort': sort,
        'dir': direction,
    })

@login_required
@user_passes_test(is_assigner)
def add_case(request):
    if request.method != 'POST':
        return redirect('assigner_dashboard')

    form = AddCaseForm(request.POST)
    if not form.is_valid():
        return redirect('assigner_dashboard')

    # 1️⃣ Create the Patient record
    patient = form.save(commit=False)
    patient.patient_id = str(uuid.uuid4())
    patient.save()

    # 2️⃣ Make a temp folder
    tmpdir = tempfile.mkdtemp()
    file_count = 0

    try:
        # 3️⃣ Write each uploaded file into tmpdir, preserving folder structure
        for uploaded in request.FILES.getlist('folder_upload'):
            # uploaded.name is something like 'subdir1/subdir2/file.ext'
            target = os.path.join(tmpdir, uploaded.name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as dest:
                for chunk in uploaded.chunks():
                    dest.write(chunk)

        # 4️⃣ Count every file in that folder
        for root, dirs, files in os.walk(tmpdir):
            for fname in files:
                file_count += 1

        # 5️⃣ Move files into MEDIA_ROOT/cases/<patient_id>/...
        dest_root = os.path.join(settings.MEDIA_ROOT, 'cases', patient.patient_id)
        os.makedirs(dest_root, exist_ok=True)

        for root, dirs, files in os.walk(tmpdir):
            for fname in files:
                src_path = os.path.join(root, fname)
                rel_path = os.path.relpath(src_path, tmpdir)
                dst_path = os.path.join(dest_root, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.move(src_path, dst_path)

                # 6️⃣ Save each file record in DB
                CaseFile.objects.create(
                    patient=patient,
                    file=os.path.join('cases', patient.patient_id, rel_path)
                )

    finally:
        # 7️⃣ Clean up the temp folder
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 8️⃣ Update the count on the Patient
    patient.number_of_images = file_count
    patient.save()

    return redirect('assigner_dashboard')

@login_required
@user_passes_test(is_assigner)
def assign_physician(request, patient_id):
    if request.method == 'POST':
        doctor_id = request.POST.get('assigned_doctor')
        patient = get_object_or_404(Patient, id=patient_id)
        doctor = get_object_or_404(User, id=doctor_id, role='doctor')

        # 🔥 Assign the doctor
        patient.preferred_physician = doctor
        patient.status = 'assigned'  # Optional but nice
        patient.save()

        return redirect('assigner_dashboard')
    else:
        return redirect('assigner_dashboard')

@login_required
@user_passes_test(is_assigner)
def download_case_files(request, patient_id):
    # 🔍 find the patient by its unique ID
    patient = get_object_or_404(Patient, patient_id=patient_id)
    files_qs = CaseFile.objects.filter(patient=patient)

    # build a ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for cf in files_qs:
            abs_path = cf.file.path
            # store it at the top level of the zip:
            arcname = os.path.basename(abs_path)
            zf.write(abs_path, arcname)

    # rewind to start
    buf.seek(0)
    # return as a download
    response = HttpResponse(buf.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{patient_id}.zip"'
    return response