import io
import os
import shutil
import tempfile
import uuid
import zipfile
from django.utils import timezone
import pytz
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from .models import Report
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import AddCaseForm, ReportForm
from .models import Patient, CaseFile, Report

User = get_user_model()


def is_assigner(user):
    return user.is_authenticated and user.role == 'assigner'


# ── ASSIGNER PORTAL ────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_assigner)
def assigner_dashboard(request):
    form = AddCaseForm()
    qs = Patient.objects.all()

    # —Fuzzy search on name or patient_id—
    q = request.GET.get('q', '').strip()
    if q:
        matched = [
            p.id
            for p in qs
            if Q(patient_name__icontains=q).evaluate(p) or Q(patient_id__icontains=q).evaluate(p)
        ]
        qs = qs.filter(id__in=matched)

    # —Filters—
    status   = request.GET.get('status', '')
    modality = request.GET.get('modality', '')
    sex      = request.GET.get('sex', '')
    age_min  = request.GET.get('age_min', '')
    age_max  = request.GET.get('age_max', '')

    if status:
        qs = qs.filter(status=status)
    if modality:
        qs = qs.filter(modality=modality)
    if sex:
        qs = qs.filter(sex=sex)
    if age_min:
        qs = qs.filter(age__gte=age_min)
    if age_max:
        qs = qs.filter(age__lte=age_max)

    # —Sorting—
    ALLOWED = ['patient_id', 'receiving_date', 'age', 'modality']
    sort     = request.GET.get('sort', 'patient_id')
    if sort not in ALLOWED:
        sort = 'patient_id'
    direction = request.GET.get('dir', 'desc')
    order     = sort if direction == 'asc' else f'-{sort}'
    qs = qs.order_by(order)

    doctors = User.objects.filter(role='doctor')

    return render(request, 'portals/assigner_dashboard.html', {
        'patients':       qs,
        'add_case_form':  form,
        'doctors':        doctors,
        'filters':        {'q': q, 'status': status, 'modality': modality, 'sex': sex, 'age_min': age_min, 'age_max': age_max},
        'sort':           sort,
        'dir':            direction,
    })


@login_required
@user_passes_test(is_assigner)
def add_case(request):
    if request.method != 'POST':
        return redirect('assigner_dashboard')

    form = AddCaseForm(request.POST)
    if not form.is_valid():
        return redirect('assigner_dashboard')

    # 1️⃣ Create Patient
    patient = form.save(commit=False)
    patient.patient_id = str(uuid.uuid4())
    patient.save()

    # 2️⃣ Save all uploaded DICOMs into a temp dir
    tmpdir = tempfile.mkdtemp()
    file_count = 0
    try:
        for uploaded in request.FILES.getlist('folder_upload'):
            target = os.path.join(tmpdir, uploaded.name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as f:
                for chunk in uploaded.chunks():
                    f.write(chunk)
        # count
        for _, _, files in os.walk(tmpdir):
            file_count += len(files)
        # move into MEDIA_ROOT/cases/<patient_id>/
        dest_root = os.path.join(settings.MEDIA_ROOT, 'cases', patient.patient_id)
        os.makedirs(dest_root, exist_ok=True)
        for root, _, files in os.walk(tmpdir):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, tmpdir)
                dst = os.path.join(dest_root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                CaseFile.objects.create(patient=patient, file=os.path.join('cases', patient.patient_id, rel))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 3️⃣ Update image count
    patient.number_of_images = file_count
    patient.save(update_fields=['number_of_images'])

    return redirect('assigner_dashboard')


@login_required
@user_passes_test(is_assigner)
def assign_physician(request, patient_id):
    if request.method == 'POST':
        doctor_id = request.POST.get('assigned_doctor')
        patient   = get_object_or_404(Patient, id=patient_id)
        doctor    = get_object_or_404(User, id=doctor_id, role='doctor')

        patient.preferred_physician = doctor
        patient.status = 'assigned'
        patient.save(update_fields=['preferred_physician', 'status'])

    return redirect('assigner_dashboard')


@login_required
# @user_passes_test(is_assigner)
def download_case_files(request, patient_id):
    patient  = get_object_or_404(Patient, patient_id=patient_id)
    files_qs = CaseFile.objects.filter(patient=patient)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for cf in files_qs:
            zf.write(cf.file.path, os.path.basename(cf.file.path))
    buf.seek(0)

    resp = HttpResponse(buf.read(), content_type='application/zip')
    resp['Content-Disposition'] = f'attachment; filename="{patient_id}.zip"'
    return resp


# ── DOCTOR PORTAL ──────────────────────────────────────────────────────────────

@login_required
def doctor_dashboard(request):
    # Debug to verify view is called
    print(f"[DEBUG] doctor_dashboard for {request.user.username}")

    # only show assigned cases
    qs = Patient.objects.filter(preferred_physician=request.user)
    print(f"[DEBUG] initial count: {qs.count()}")

    # Filters (same as assigner)
    q        = request.GET.get('q', '').strip()
    status   = request.GET.get('status', '')
    modality = request.GET.get('modality', '')
    sex      = request.GET.get('sex', '')
    age_min  = request.GET.get('age_min', '')
    age_max  = request.GET.get('age_max', '')

    if q:
        qs = qs.filter(Q(patient_name__icontains=q) | Q(patient_id__icontains=q))
    if status:   qs = qs.filter(status=status)
    if modality: qs = qs.filter(modality=modality)
    if sex:      qs = qs.filter(sex=sex)
    if age_min:  qs = qs.filter(age__gte=age_min)
    if age_max:  qs = qs.filter(age__lte=age_max)

    # Sorting
    ALLOWED = ['patient_id', 'receiving_date', 'age', 'modality']
    sort     = request.GET.get('sort', 'patient_id')
    if sort not in ALLOWED:
        sort = 'patient_id'
    direction = request.GET.get('dir', 'desc')
    order     = sort if direction == 'asc' else f'-{sort}'
    qs = qs.order_by(order)

    # build (patient, form) list
    patient_form_pairs = [(p, ReportForm()) for p in qs]
    print(f"[DEBUG] after filters & sort: {len(patient_form_pairs)} patients")
    reports = {r.patient_id: r for r in Report.objects.filter(patient__in=qs)}

    return render(request, 'portals/doctor_dashboard.html', {
        'patient_form_pairs': patient_form_pairs,
        'report_map': reports,
        'filters':            {'q': q, 'status': status, 'modality': modality, 'sex': sex, 'age_min': age_min, 'age_max': age_max},
        'sort':               sort,
        'dir':                direction,
    })


@login_required
def add_report(request, patient_id):
    if request.method == 'POST':
        patient = get_object_or_404(Patient, patient_id=patient_id)
        form    = ReportForm(request.POST)
        if form.is_valid():
            rep          = form.save(commit=False)
            rep.patient  = patient
            rep.author   = request.user
            rep.save()
            patient.status = 'reported'
            patient.save(update_fields=['status'])
    return redirect('doctor:doctor_dashboard')

@login_required
def edit_report(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    # either get existing or create a new Report instance
    report, created = Report.objects.get_or_create(patient=patient, defaults={
        'author': request.user,
        'created_at': timezone.now()
    })
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            rep = form.save(commit=False)
            rep.author = request.user
            rep.created_at = timezone.now()
            rep.save()
            # mark patient reported
            patient.status = 'reported'
            patient.report_time = rep.created_at
            patient.save(update_fields=['status','report_time'])
            return redirect('doctor:doctor_dashboard')
    else:
        form = ReportForm(instance=report)

    return render(request, 'portals/report_form.html', {
        'form': form,
        'patient': patient,
    })

@login_required
def download_report(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    report  = get_object_or_404(Report, patient=patient)

    text = report.report_text or ''
    filename = f"{patient.patient_id}_report.txt"
    resp = HttpResponse(text, content_type='text/plain; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp

def ist_now():
    return timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))

@login_required
def add_or_edit_report(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    report, created = Report.objects.get_or_create(
        patient=patient, author=request.user,
        defaults={'report_text': ''}
    )
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            patient.status = 'reported'
            patient.save(update_fields=['status'])
            return redirect('doctor:doctor_dashboard')
    else:
        form = ReportForm(instance=report)
    return render(request, 'portals/report_form.html', {'form': form, 'patient': patient})

@login_required
def download_report(request, patient_id):
    report = get_object_or_404(Report, patient__patient_id=patient_id)
    doc = report.as_doc()
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{report.filename()}"'
    doc.save(response)
    return response

@login_required
@user_passes_test(lambda u: u.role=='assigner')
def assigner_download_report(request, patient_id):
    # reuse same download logic
    report = get_object_or_404(Report, patient__patient_id=patient_id)
    return download_report(request, patient_id)