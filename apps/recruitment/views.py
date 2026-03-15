import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from apps.core.utils import get_company_qs, get_employee_related_qs
from apps.core.addon_decorators import addon_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import hr_required, manager_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import (
    ManpowerRequest, Candidate, OfferingLetter,
    OfferingTemplate, CompanySetting,
)
from apps.core.models import Department, Position
from apps.core.addon_decorators import check_addon

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  MANPOWER REQUEST
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('recruitment')
def mprf_list(request):
    mprfs = ManpowerRequest.objects.select_related('department', 'jabatan').order_by('-created_at')
    return render(request, 'recruitment/manpower_list.html', {'mprfs': mprfs})


@login_required
@addon_required('recruitment')
def mprf_form(request, pk=None):
    instance = get_object_or_404(ManpowerRequest, pk=pk) if pk else None
    if request.method == 'POST':
        data = {
            'department_id': request.POST.get('department'),
            'jabatan_id': request.POST.get('jabatan') or None,
            'nama_jabatan': request.POST.get('nama_jabatan'),
            'tipe': request.POST.get('tipe', 'New Hire'),
            'jumlah_kebutuhan': int(request.POST.get('jumlah_kebutuhan', 1) or 1),
            'alasan': request.POST.get('alasan', ''),
            'kualifikasi': request.POST.get('kualifikasi', ''),
            'target_date': request.POST.get('target_date'),
            'status': request.POST.get('status', 'Draft'),
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
        else:
            import uuid
            data['created_by']  = request.user.get_full_name() or request.user.username
            data['company']     = getattr(request, 'company', None)
            data['nomor_mprf']  = f"MPRF-{uuid.uuid4().hex[:8].upper()}"
            ManpowerRequest.objects.create(**data)
        messages.success(request, 'Manpower Request berhasil disimpan.')
        return redirect('mprf_list')
    return render(request, 'recruitment/manpower_form.html', {
        'instance': instance,
        'departments': Department.objects.filter(aktif=True),
        'positions': Position.objects.all(),
    })


@login_required
@manager_required
def mprf_approve(request, pk):
    mprf = get_object_or_404(ManpowerRequest, pk=pk)
    mprf.status = 'Approved'
    mprf.approved_by = request.user.get_full_name() or request.user.username
    from django.utils import timezone
    mprf.approved_date = timezone.now().date()
    mprf.save()
    messages.success(request, f'MPRF {mprf.nomor_mprf} disetujui.')
    return redirect('mprf_list')


# ══════════════════════════════════════════════════════════════════════════════
#  CANDIDATE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('recruitment')
def candidate_list(request):
    candidates = Candidate.objects.select_related('mprf').order_by('-tanggal_melamar')
    return render(request, 'recruitment/candidate_list.html', {'candidates': candidates})


@login_required
@addon_required('recruitment')
def candidate_form(request, pk=None):
    instance = get_object_or_404(Candidate, pk=pk) if pk else None
    if request.method == 'POST':
        data = {
            'mprf_id': request.POST.get('mprf') or None,
            'nama': request.POST.get('nama'),
            'email': request.POST.get('email', ''),
            'no_hp': request.POST.get('no_hp', ''),
            'jabatan_dilamar': request.POST.get('jabatan_dilamar'),
            'sumber': request.POST.get('sumber', ''),
            'status': request.POST.get('status', 'Screening'),
            'pendidikan': request.POST.get('pendidikan', ''),
            'pengalaman_tahun': int(request.POST.get('pengalaman_tahun', 0) or 0),
            'ekspektasi_gaji': int(request.POST.get('ekspektasi_gaji', 0) or 0) or None,
            'catatan': request.POST.get('catatan', ''),
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            if 'cv_file' in request.FILES:
                instance.cv_file = request.FILES['cv_file']
            instance.save()
        else:
            candidate = Candidate(**data)
            if 'cv_file' in request.FILES:
                candidate.cv_file = request.FILES['cv_file']
            candidate.save()
        messages.success(request, 'Data kandidat berhasil disimpan.')
        return redirect('candidate_list')
    return render(request, 'recruitment/candidate_form.html', {
        'instance': instance,
        'mprfs': ManpowerRequest.objects.exclude(status='Cancelled').order_by('-created_at'),
    })


@login_required
@addon_required('recruitment')
def candidate_detail(request, pk):
    from apps.psychotest.models import (
        PsikotesSession, MedicalCheckUp, InterviewSession,
        Rekomendasi, OnboardingChecklist,
    )
    from utils.psychotest_seed import DISC_DESKRIPSI

    candidate = get_object_or_404(Candidate, pk=pk)

    # ── Psikotes ──────────────────────────────────────────────────────────────
    psy_session = (
        PsikotesSession.objects
        .filter(candidate=candidate)
        .order_by('-created_at')
        .first()
    )
    psy_result = None
    try:
        psy_result = candidate.psychotest_result
    except Exception:
        pass

    psy_link = ''
    if psy_session:
        psy_link = request.build_absolute_uri(psy_session.link)

    disc_info = None
    if psy_result and psy_result.disc_profil:
        disc_info = DISC_DESKRIPSI.get(psy_result.disc_dominant)

    # ── Pipeline data ─────────────────────────────────────────────────────────
    mcu = None
    try:
        mcu = candidate.medical_checkup
    except Exception:
        pass

    interviews      = InterviewSession.objects.filter(candidate=candidate).order_by('-tanggal')
    rekomendasi_obj = None
    try:
        rekomendasi_obj = candidate.rekomendasi
    except Exception:
        pass

    offering_letters = candidate.offering_letters.select_related('template').order_by('-tanggal_surat')

    onboarding = None
    try:
        onboarding = candidate.onboarding
    except Exception:
        pass

    # ── ATS detail ────────────────────────────────────────────────────────────
    ats_detail   = candidate.ats_detail or {}
    skill_match  = ats_detail.get('skill_match', [])
    skill_gap    = ats_detail.get('skill_wajib_gap', [])
    detail_score = ats_detail.get('detail_score', {})

    # ── Add-On lisensi ────────────────────────────────────────────────────────
    addon_advanced_psychotest = check_addon(request, 'advanced_psychotest')

    # ── Pipeline step labels ──────────────────────────────────────────────────
    pipeline_steps = [
        (1, 'ATS CV'),
        (2, 'Psikotes'),
        (3, 'MCU'),
        (4, 'Interview'),
        (5, 'Rekomendasi'),
        (6, 'Offering'),
        (7, 'Onboarding'),
        (8, 'Close'),
    ]

    return render(request, 'recruitment/candidate_detail.html', {
        'candidate':                candidate,
        'pipeline_steps':           pipeline_steps,
        # psikotes
        'psy_session':              psy_session,
        'psy_result':               psy_result,
        'psy_link':                 psy_link,
        'disc_info':                disc_info,
        # pipeline
        'mcu':                      mcu,
        'interviews':               interviews,
        'rekomendasi_obj':          rekomendasi_obj,
        'offering_letters':         offering_letters,
        'onboarding':               onboarding,
        # ats
        'ats_detail':               ats_detail,
        'skill_match':              skill_match,
        'skill_gap':                skill_gap,
        'detail_score':             detail_score,
        # addon
        'addon_advanced_psychotest': addon_advanced_psychotest,
    })


@login_required
def candidate_print(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, 'recruitment/candidate_print.html', {'candidate': candidate})


@login_required
@require_POST
def candidate_update_status(request, pk):
    """Update status kandidat saja — tanpa menimpa field lain."""
    candidate = get_object_or_404(Candidate, pk=pk)
    status = request.POST.get('status', '').strip()
    valid_statuses = dict(Candidate.STATUS_CHOICES)
    if status and status in valid_statuses:
        candidate.status = status
        candidate.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Status kandidat diubah ke: {valid_statuses[status]}')
    else:
        messages.error(request, 'Status tidak valid.')
    return redirect('candidate_detail', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
#  OFFERING LETTER
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('recruitment')
def offering_list(request):
    offerings = OfferingLetter.objects.select_related('candidate', 'template').order_by('-tanggal_surat')
    return render(request, 'recruitment/offering_list.html', {'offerings': offerings})


@login_required
@hr_required
def offering_form(request, pk=None):
    instance = get_object_or_404(OfferingLetter, pk=pk) if pk else None
    setting = CompanySetting.get()
    templates = OfferingTemplate.objects.all()
    default_tpl = templates.filter(is_default=True).first()

    if request.method == 'POST':
        tpl_id = request.POST.get('template') or None
        data = {
            'candidate_id':        request.POST.get('candidate'),
            'template_id':         tpl_id,
            'jabatan':             request.POST.get('jabatan', ''),
            'department_id':       request.POST.get('department') or None,
            'tanggal_surat':       request.POST.get('tanggal_surat'),
            'tanggal_mulai_kerja': request.POST.get('tanggal_mulai_kerja'),
            'site_lokasi':         request.POST.get('site_lokasi', ''),
            'lokasi_kerja':        request.POST.get('lokasi_kerja', ''),
            'point_of_hire':       request.POST.get('point_of_hire', ''),
            'join_date_text':      request.POST.get('join_date_text', 'As Soon As Possible'),
            'gaji_pokok':          int(request.POST.get('gaji_pokok', 0) or 0),
            'fixed_allowance':     int(request.POST.get('fixed_allowance', 0) or 0),
            'tunjangan_total':     int(request.POST.get('tunjangan_total', 0) or 0),
            'masa_probasi':        int(request.POST.get('masa_probasi', 3) or 3),
            'no_arsip':            request.POST.get('no_arsip', ''),
            'status':              request.POST.get('status', 'Draft'),
            'keterangan':          request.POST.get('keterangan', ''),
        }
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Offering Letter berhasil diperbarui.')
        else:
            instance = OfferingLetter.objects.create(**data)
            messages.success(request, f'Offering Letter {instance.nomor} berhasil dibuat.')
        return redirect('offering_list')

    # GET — auto-fill dari kandidat jika ada query param
    prefill_candidate = None
    candidate_id = request.GET.get('candidate')
    if candidate_id:
        prefill_candidate = Candidate.objects.filter(pk=candidate_id).first()

    return render(request, 'recruitment/offering_form.html', {
        'instance':          instance,
        'setting':           setting,
        'templates':         templates,
        'default_tpl':       default_tpl,
        'candidates':        Candidate.objects.exclude(status__in=['Hired', 'Rejected', 'Withdrawn']),
        'departments':       Department.objects.filter(aktif=True),
        'prefill_candidate': prefill_candidate,
    })


@login_required
def offering_print(request, pk):
    """Render halaman print/preview offering letter."""
    ol = get_object_or_404(
        OfferingLetter.objects.select_related('candidate', 'template', 'department'),
        pk=pk
    )
    setting = CompanySetting.get()
    tpl = ol.template or OfferingTemplate.objects.filter(is_default=True).first()

    # Jika tidak ada template sama sekali, buat objek default sementara
    if not tpl:
        tpl = OfferingTemplate()

    return render(request, 'recruitment/offering_print.html', {
        'ol':      ol,
        'tpl':     tpl,
        'setting': setting,
    })


@login_required
@require_POST
def offering_update_status(request, pk):
    """Update status offering letter (Accepted/Rejected/Sent)."""
    ol = get_object_or_404(OfferingLetter, pk=pk)
    new_status = request.POST.get('status', '').strip()
    valid = [s[0] for s in OfferingLetter.STATUS_CHOICES]
    if new_status in valid:
        ol.status = new_status
        ol.save(update_fields=['status'])
        # Jika Accepted → update status kandidat ke Hired
        if new_status == 'Accepted' and ol.candidate:
            ol.candidate.status = 'Hired'
            ol.candidate.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Offering {ol.nomor} diterima. Kandidat {ol.candidate.nama} ditandai Hired.')
        elif new_status == 'Rejected':
            messages.warning(request, f'Offering {ol.nomor} ditolak.')
        else:
            messages.success(request, f'Status Offering {ol.nomor} diubah ke {new_status}.')
    else:
        messages.error(request, 'Status tidak valid.')
    return redirect('offering_list')


@login_required
def offering_get_template(request):
    """AJAX — kembalikan field-field template sebagai JSON."""
    tpl_id = request.GET.get('id')
    if not tpl_id:
        return JsonResponse({'error': 'no id'}, status=400)
    tpl = get_object_or_404(OfferingTemplate, pk=tpl_id)
    return JsonResponse({
        'working_day_text':         tpl.working_day_text,
        'employment_status_text':   tpl.employment_status_text,
        'meal_allowance_text':      tpl.meal_allowance_text,
        'residence_allowance_text': tpl.residence_allowance_text,
        'roster_leave_text':        tpl.roster_leave_text,
        'annual_leave_text':        tpl.annual_leave_text,
        'overtime_text':            tpl.overtime_text,
        'bpjs_kes_text':            tpl.bpjs_kes_text,
        'bpjs_tk_text':             tpl.bpjs_tk_text,
        'bpjs_potongan_text':       tpl.bpjs_potongan_text,
        'pph21_text':               tpl.pph21_text,
        'footer_text':              tpl.footer_text,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  OFFERING TEMPLATE CRUD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def template_list(request):
    templates = OfferingTemplate.objects.all()
    return render(request, 'recruitment/template_list.html', {'templates': templates})


@login_required
@hr_required
def template_form(request, pk=None):
    instance = get_object_or_404(OfferingTemplate, pk=pk) if pk else None
    FIELDS = [
        'nama', 'deskripsi', 'is_default',
        'working_day_text', 'employment_status_text',
        'meal_allowance_text', 'residence_allowance_text',
        'roster_leave_text', 'annual_leave_text', 'overtime_text',
        'bpjs_kes_text', 'bpjs_tk_text', 'bpjs_potongan_text',
        'pph21_text', 'footer_text',
    ]
    if request.method == 'POST':
        data = {f: request.POST.get(f, '') for f in FIELDS}
        data['is_default'] = bool(request.POST.get('is_default'))
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Template berhasil diperbarui.')
        else:
            instance = OfferingTemplate.objects.create(**data)
            messages.success(request, f'Template "{instance.nama}" berhasil dibuat.')
        return redirect('template_list')
    return render(request, 'recruitment/template_form.html', {'instance': instance})


@login_required
@hr_required
def template_delete(request, pk):
    tpl = get_object_or_404(OfferingTemplate, pk=pk)
    if request.method == 'POST':
        nama = tpl.nama
        tpl.delete()
        messages.success(request, f'Template "{nama}" dihapus.')
    return redirect('template_list')


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY SETTING
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def company_setting(request):
    setting = CompanySetting.get()
    if request.method == 'POST':
        setting.nama_perusahaan = request.POST.get('nama_perusahaan', setting.nama_perusahaan)
        setting.hrd_manager     = request.POST.get('hrd_manager', setting.hrd_manager)
        setting.format_nomor_ol = request.POST.get('format_nomor_ol', setting.format_nomor_ol)
        if 'logo' in request.FILES:
            setting.logo = request.FILES['logo']
        elif request.POST.get('hapus_logo'):
            setting.logo = None
        setting.save()
        messages.success(request, 'Pengaturan perusahaan berhasil disimpan.')
        return redirect('company_setting')
    return render(request, 'recruitment/company_setting.html', {'setting': setting})


# ══════════════════════════════════════════════════════════════════════════════
#  ATS
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def ats_scan(request):
    if request.method == 'POST' and request.FILES.get('cv_file'):
        cv_file  = request.FILES['cv_file']
        filename = cv_file.name.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.docx')):
            messages.error(request, 'Format tidak didukung. Harap upload PDF atau DOCX.')
            return redirect('ats_scan')

        from django.conf import settings
        import tempfile, os
        suffix = '.pdf' if filename.endswith('.pdf') else '.docx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix,
                                         dir=settings.MEDIA_ROOT) as tmp:
            for chunk in cv_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        request.session['ats_cv_path']     = tmp_path
        request.session['ats_cv_filename'] = cv_file.name
        return redirect('ats_analyze')
    return render(request, 'recruitment/ats_scan.html', {
        'positions': Position.objects.all(),
    })


@login_required
def ats_analyze(request):
    cv_path = request.session.get('ats_cv_path')
    if not cv_path:
        return redirect('ats_scan')
    return render(request, 'recruitment/ats_analyze.html', {
        'cv_filename': request.session.get('ats_cv_filename', ''),
        'positions':   Position.objects.all(),
    })


@login_required
@hr_required
def ats_save_candidate(request):
    if request.method != 'POST':
        return redirect('ats_scan')
    # simpan kandidat dari hasil ATS
    data = {
        'nama':             request.POST.get('nama', ''),
        'jabatan_dilamar':  request.POST.get('jabatan_dilamar', ''),
        'email':            request.POST.get('email', ''),
        'no_hp':            request.POST.get('no_hp', ''),
        'pendidikan':       request.POST.get('pendidikan', ''),
        'pengalaman_tahun': int(request.POST.get('pengalaman_tahun', 0) or 0),
        'ats_score':        int(request.POST.get('ats_score', 0) or 0),
        'ats_grade':        request.POST.get('ats_grade', ''),
        'ats_rekomendasi':  request.POST.get('ats_rekomendasi', ''),
        'status':           'Screening',
    }
    ats_detail_raw = request.POST.get('ats_detail', '')
    try:
        data['ats_detail'] = json.loads(ats_detail_raw)
    except Exception:
        data['ats_detail'] = {}
    candidate = Candidate.objects.create(**data)
    messages.success(request, f'Kandidat {candidate.nama} berhasil disimpan dari ATS.')
    return redirect('candidate_detail', pk=candidate.pk)
