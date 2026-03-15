# ==================================================
# FILE: apps/od/views_training.py
# Tambahkan import ke apps/od/views.py:
#   from .views_training import *
# ==================================================
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from apps.core.addon_decorators import addon_required

from .models import TrainingProgram, TrainingPlan, TrainingRealization


def _get_company(request):
    from apps.core.models import Company
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        company = Company.objects.first()
    return company


# ── MASTER PROGRAM ─────────────────────────────────────────────────────────────

@login_required
@addon_required('od')
def training_program_list(request):
    company = _get_company(request)
    programs = TrainingProgram.objects.filter(company=company)
    return render(request, 'od/training_program_list.html', {
        'programs': programs,
    })


@login_required
@addon_required('od')
def training_program_create(request):
    company = _get_company(request)
    from .models import Competency
    kompetensi_all = Competency.objects.filter(company=company, aktif=True)

    if request.method == 'POST':
        p = request.POST
        program = TrainingProgram.objects.create(
            company      = company,
            nama         = p.get('nama', '').strip(),
            kategori     = p.get('kategori', 'technical'),
            metode       = p.get('metode', 'offline'),
            penyelenggara= p.get('penyelenggara', '').strip(),
            deskripsi    = p.get('deskripsi', '').strip(),
            durasi_jam   = p.get('durasi_jam') or 8,
            biaya_est    = p.get('biaya_est') or 0,
        )
        komp_ids = request.POST.getlist('kompetensi_terkait')
        if komp_ids:
            program.kompetensi_terkait.set(komp_ids)
        messages.success(request, f'Program "{program.nama}" berhasil ditambahkan.')
        return redirect('od:training_program_list')

    return render(request, 'od/training_program_form.html', {
        'title': 'Tambah Program Training',
        'kompetensi_all': kompetensi_all,
        'kategori_choices': TrainingProgram.KATEGORI_CHOICES,
        'metode_choices': TrainingProgram.METODE_CHOICES,
    })


@login_required
@addon_required('od')
def training_program_edit(request, pk):
    company = _get_company(request)
    program = get_object_or_404(TrainingProgram, pk=pk, company=company)
    from .models import Competency
    kompetensi_all = Competency.objects.filter(company=company, aktif=True)

    if request.method == 'POST':
        p = request.POST
        program.nama          = p.get('nama', '').strip()
        program.kategori      = p.get('kategori', 'technical')
        program.metode        = p.get('metode', 'offline')
        program.penyelenggara = p.get('penyelenggara', '').strip()
        program.deskripsi     = p.get('deskripsi', '').strip()
        program.durasi_jam    = p.get('durasi_jam') or 8
        program.biaya_est     = p.get('biaya_est') or 0
        program.aktif         = 'aktif' in p
        program.save()
        komp_ids = request.POST.getlist('kompetensi_terkait')
        program.kompetensi_terkait.set(komp_ids)
        messages.success(request, f'Program "{program.nama}" diperbarui.')
        return redirect('od:training_program_list')

    return render(request, 'od/training_program_form.html', {
        'title': 'Edit Program Training',
        'program': program,
        'kompetensi_all': kompetensi_all,
        'kompetensi_selected': list(program.kompetensi_terkait.values_list('id', flat=True)),
        'kategori_choices': TrainingProgram.KATEGORI_CHOICES,
        'metode_choices': TrainingProgram.METODE_CHOICES,
    })


@login_required
@addon_required('od')
def training_program_delete(request, pk):
    company = _get_company(request)
    program = get_object_or_404(TrainingProgram, pk=pk, company=company)
    if request.method == 'POST':
        nama = program.nama
        program.delete()
        messages.success(request, f'Program "{nama}" dihapus.')
    return redirect('od:training_program_list')


# ── RENCANA TRAINING ───────────────────────────────────────────────────────────

@login_required
@addon_required('od')
def training_plan_list(request):
    company  = _get_company(request)
    periode  = request.GET.get('periode', str(timezone.now().year))
    status   = request.GET.get('status', '')

    plans = TrainingPlan.objects.filter(company=company, periode=periode)\
                                .select_related('employee', 'program', 'diusulkan_oleh')
    if status:
        plans = plans.filter(status=status)

    periode_list = TrainingPlan.objects.filter(company=company)\
                                       .values_list('periode', flat=True)\
                                       .distinct().order_by('-periode')
    return render(request, 'od/training_plan_list.html', {
        'plans': plans,
        'periode': periode,
        'periode_list': periode_list,
        'status_filter': status,
        'status_choices': TrainingPlan.STATUS_CHOICES,
    })


@login_required
@addon_required('od')
def training_plan_create(request):
    company = _get_company(request)
    from apps.employees.models import Employee
    employees = Employee.objects.filter(company=company, status='Aktif').order_by('nama')
    programs  = TrainingProgram.objects.filter(company=company, aktif=True)

    if request.method == 'POST':
        p = request.POST
        plan = TrainingPlan.objects.create(
            company         = company,
            employee_id     = p.get('employee'),
            program_id      = p.get('program'),
            periode         = p.get('periode', str(timezone.now().year)),
            tanggal_rencana = p.get('tanggal_rencana') or None,
            status          = p.get('status', 'rencana'),
            prioritas       = p.get('prioritas', 2),
            alasan          = p.get('alasan', '').strip(),
            diusulkan_oleh  = request.user.employee if hasattr(request.user, 'employee') else None,
        )
        messages.success(request, f'Rencana training untuk {plan.employee.nama} ditambahkan.')
        return redirect('od:training_plan_list')

    return render(request, 'od/training_plan_form.html', {
        'title': 'Tambah Rencana Training',
        'employees': employees,
        'programs': programs,
        'status_choices': TrainingPlan.STATUS_CHOICES,
        'tahun_ini': str(timezone.now().year),
    })


@login_required
@addon_required('od')
def training_plan_edit(request, pk):
    company = _get_company(request)
    plan    = get_object_or_404(TrainingPlan, pk=pk, company=company)
    from apps.employees.models import Employee
    employees = Employee.objects.filter(company=company, status='Aktif').order_by('nama')
    programs  = TrainingProgram.objects.filter(company=company, aktif=True)

    if request.method == 'POST':
        p = request.POST
        plan.employee_id     = p.get('employee')
        plan.program_id      = p.get('program')
        plan.periode         = p.get('periode', plan.periode)
        plan.tanggal_rencana = p.get('tanggal_rencana') or None
        plan.prioritas       = p.get('prioritas', plan.prioritas)
        plan.alasan          = p.get('alasan', '').strip()

        old_status = plan.status
        plan.status = p.get('status', plan.status)
        if plan.status == 'disetujui' and old_status != 'disetujui':
            plan.tanggal_disetujui = timezone.now().date()
            plan.disetujui_oleh = request.user.employee if hasattr(request.user, 'employee') else None
        plan.save()
        messages.success(request, 'Rencana training diperbarui.')
        return redirect('od:training_plan_list')

    return render(request, 'od/training_plan_form.html', {
        'title': 'Edit Rencana Training',
        'plan': plan,
        'employees': employees,
        'programs': programs,
        'status_choices': TrainingPlan.STATUS_CHOICES,
        'tahun_ini': str(timezone.now().year),
    })


@login_required
@addon_required('od')
def training_plan_delete(request, pk):
    company = _get_company(request)
    plan = get_object_or_404(TrainingPlan, pk=pk, company=company)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Rencana training dihapus.')
    return redirect('od:training_plan_list')


# ── REALISASI TRAINING ─────────────────────────────────────────────────────────

@login_required
@addon_required('od')
def training_realization_create(request, plan_pk):
    company = _get_company(request)
    plan    = get_object_or_404(TrainingPlan, pk=plan_pk, company=company)

    if hasattr(plan, 'realization'):
        messages.warning(request, 'Realisasi untuk rencana ini sudah ada.')
        return redirect('od:training_plan_list')

    if request.method == 'POST':
        p = request.POST
        TrainingRealization.objects.create(
            plan             = plan,
            tanggal_mulai    = p.get('tanggal_mulai'),
            tanggal_selesai  = p.get('tanggal_selesai'),
            lokasi           = p.get('lokasi', '').strip(),
            instruktur       = p.get('instruktur', '').strip(),
            biaya_aktual     = p.get('biaya_aktual') or 0,
            hasil            = p.get('hasil', 'ikut'),
            nilai            = p.get('nilai') or None,
            nomor_sertifikat = p.get('nomor_sertifikat', '').strip(),
            berlaku_sampai   = p.get('berlaku_sampai') or None,
            catatan          = p.get('catatan', '').strip(),
        )
        plan.status = 'selesai'
        plan.save(update_fields=['status'])
        messages.success(request, f'Realisasi training {plan.employee.nama} dicatat.')
        return redirect('od:training_plan_list')

    return render(request, 'od/training_realization_form.html', {
        'plan': plan,
        'hasil_choices': TrainingRealization.HASIL_CHOICES,
    })


@login_required
@addon_required('od')
def training_dashboard(request):
    """Ringkasan training per periode."""
    company  = _get_company(request)
    periode  = request.GET.get('periode', str(timezone.now().year))

    plans = TrainingPlan.objects.filter(company=company, periode=periode)\
                                .select_related('employee', 'program')

    total       = plans.count()
    selesai     = plans.filter(status='selesai').count()
    disetujui   = plans.filter(status='disetujui').count()
    rencana     = plans.filter(status='rencana').count()
    batal       = plans.filter(status='batal').count()

    # Ringkasan per kategori
    from django.db.models import Count
    per_kategori = plans.values('program__kategori')\
                        .annotate(total=Count('id'))\
                        .order_by('-total')

    periode_list = TrainingPlan.objects.filter(company=company)\
                                       .values_list('periode', flat=True)\
                                       .distinct().order_by('-periode')

    return render(request, 'od/training_dashboard.html', {
        'periode': periode,
        'periode_list': periode_list,
        'total': total,
        'selesai': selesai,
        'disetujui': disetujui,
        'rencana': rencana,
        'batal': batal,
        'per_kategori': per_kategori,
        'plans_terbaru': plans.filter(status='selesai').order_by('-realization__tanggal_selesai')[:10],
    })
