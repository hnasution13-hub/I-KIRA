from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
import json

from apps.core.addon_decorators import addon_required
from apps.core.models import Department, Position
from apps.employees.models import Employee
from .models import WorkloadStandard, FTEStandard, FTEPlanningResult


def _company(request):
    return getattr(request, 'company', None)


def _emp_qs(request):
    company = _get_company(request)
    qs = Employee.objects.filter(company=company, status='Aktif') if company else Employee.objects.filter(status='Aktif')
    c = _company(request)
    if c:
        qs = qs.filter(company=c)
    return qs


# ══════════════════════════════════════════════════════════════════════════════
#  OD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def od_dashboard(request):
    company = _company(request)
    employees = _emp_qs(request).select_related('department', 'jabatan')

    total_karyawan = employees.count()

    # Distribusi per departemen
    dist_dept = (
        employees.values('department__nama')
        .annotate(jumlah=Count('id'))
        .order_by('-jumlah')
    )
    chart_dept_labels = [d['department__nama'] or 'Tanpa Dept' for d in dist_dept]
    chart_dept_data   = [d['jumlah'] for d in dist_dept]

    # Distribusi per jabatan level
    dist_level = (
        employees.values('jabatan__level')
        .annotate(jumlah=Count('id'))
        .order_by('-jumlah')
    )
    chart_level_labels = [d['jabatan__level'] or 'Tanpa Level' for d in dist_level]
    chart_level_data   = [d['jumlah'] for d in dist_level]

    # FTE Gap summary
    company = _get_company(request)
    fte_qs = FTEPlanningResult.objects.filter(company=company) if company else FTEPlanningResult.objects.all()
    if company:
        fte_qs = fte_qs.filter(company=company)

    fte_over  = fte_qs.filter(status='over').count()
    fte_ideal = fte_qs.filter(status='ideal').count()
    fte_under = fte_qs.filter(status='under').count()

    # Performance summary (jika modul performance ada)
    perf_summary = None
    try:
        from apps.performance.models import PenilaianKaryawan, PeriodePenilaian
        periode_aktif = PeriodePenilaian.objects.filter(status='aktif')
        if company:
            periode_aktif = periode_aktif.filter(company=company)
        periode_aktif = periode_aktif.first()

        if periode_aktif:
            perf_qs = PenilaianKaryawan.objects.filter(status='approved', periode=periode_aktif)
            if company:
                perf_qs = perf_qs.filter(company=company)
            perf_summary = {
                'periode'       : periode_aktif,
                'total'         : perf_qs.count(),
                'rata_skor'     : perf_qs.aggregate(avg=Avg('skor_akhir'))['avg'] or 0,
                'istimewa'      : perf_qs.filter(predikat='Istimewa').count(),
                'perlu_perbaikan': perf_qs.filter(predikat='Perlu Perbaikan').count(),
            }
    except Exception:
        pass

    # Headcount per dept untuk tabel
    dept_headcount = []
    company = _get_company(request)
    depts = Department.objects.filter(company=company) if company else Department.objects.all()
    if company:
        depts = depts.filter(company=company)
    for dept in depts:
        hc = employees.filter(department=dept).count()
        fte_std = FTEStandard.objects.filter(department=dept, jabatan=None)
        if company:
            fte_std = fte_std.filter(company=company)
        fte_std = fte_std.order_by('-tahun').first()
        dept_headcount.append({
            'dept'     : dept,
            'headcount': hc,
            'fte_ideal': float(fte_std.fte_ideal) if fte_std else None,
            'gap'      : round(hc - float(fte_std.fte_ideal), 1) if fte_std else None,
        })

    ctx = {
        'total_karyawan'     : total_karyawan,
        'fte_over'           : fte_over,
        'fte_ideal'          : fte_ideal,
        'fte_under'          : fte_under,
        'perf_summary'       : perf_summary,
        'dept_headcount'     : dept_headcount,
        'chart_dept_labels'  : json.dumps(chart_dept_labels),
        'chart_dept_data'    : json.dumps(chart_dept_data),
        'chart_level_labels' : json.dumps(chart_level_labels),
        'chart_level_data'   : json.dumps(chart_level_data),
    }
    return render(request, 'od/dashboard.html', ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  WORKLOAD ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def workload_list(request):
    company = _company(request)
    dept_id = request.GET.get('dept')
    qs = WorkloadStandard.objects.select_related('jabatan', 'department').filter(aktif=True)
    if company:
        qs = qs.filter(company=company)
    if dept_id:
        qs = qs.filter(department_id=dept_id)

    company = _get_company(request)
    depts = Department.objects.filter(company=company) if company else Department.objects.all()
    if company:
        depts = depts.filter(company=company)

    ctx = {
        'workloads'      : qs,
        'depts'          : depts,
        'selected_dept'  : dept_id,
    }
    return render(request, 'od/workload_list.html', ctx)


@login_required
@addon_required('od')
def workload_create(request):
    company = _company(request)
    if request.method == 'POST':
        dept_id   = request.POST.get('department_id') or None
        jabatan_id = request.POST['jabatan_id']
        WorkloadStandard.objects.create(
            company        = company,
            jabatan_id     = jabatan_id,
            department_id  = dept_id,
            nama_aktivitas = request.POST['nama_aktivitas'],
            standar_output = request.POST['standar_output'],
            satuan         = request.POST['satuan'],
            deskripsi      = request.POST.get('deskripsi', ''),
        )
        messages.success(request, 'Standar workload berhasil ditambahkan.')
        return redirect('od:workload_list')

    company = _get_company(request)
    depts    = Department.objects.filter(company=company) if company else Department.objects.all()
    jabatans = Position.objects.filter(company=company, aktif=True) if company else Position.objects.filter(aktif=True)

    return render(request, 'od/workload_form.html', {
        'depts': depts, 'jabatans': jabatans, 'action': 'Tambah'
    })


@login_required
@addon_required('od')
def workload_edit(request, pk):
    obj = get_object_or_404(WorkloadStandard, pk=pk)
    company = _company(request)
    if request.method == 'POST':
        obj.jabatan_id     = request.POST['jabatan_id']
        obj.department_id  = request.POST.get('department_id') or None
        obj.nama_aktivitas = request.POST['nama_aktivitas']
        obj.standar_output = request.POST['standar_output']
        obj.satuan         = request.POST['satuan']
        obj.deskripsi      = request.POST.get('deskripsi', '')
        obj.aktif          = 'aktif' in request.POST
        obj.save()
        messages.success(request, 'Standar workload diperbarui.')
        return redirect('od:workload_list')

    company = _get_company(request)
    depts    = Department.objects.filter(company=company) if company else Department.objects.all()
    jabatans = Position.objects.filter(company=company, aktif=True) if company else Position.objects.filter(aktif=True)

    return render(request, 'od/workload_form.html', {
        'obj': obj, 'depts': depts, 'jabatans': jabatans, 'action': 'Edit'
    })


@login_required
@addon_required('od')
def workload_delete(request, pk):
    obj = get_object_or_404(WorkloadStandard, pk=pk)
    obj.delete()
    messages.success(request, 'Data workload dihapus.')
    return redirect('od:workload_list')


# ══════════════════════════════════════════════════════════════════════════════
#  FTE STANDARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def fte_standard_list(request):
    company = _company(request)
    qs = FTEStandard.objects.select_related('department', 'jabatan')
    if company:
        qs = qs.filter(company=company)

    ctx = {'fte_standards': qs}
    return render(request, 'od/fte_standard_list.html', ctx)


@login_required
@addon_required('od')
def fte_standard_create(request):
    company = _company(request)
    if request.method == 'POST':
        FTEStandard.objects.create(
            company           = company,
            department_id     = request.POST['department_id'],
            jabatan_id        = request.POST.get('jabatan_id') or None,
            fte_ideal         = request.POST['fte_ideal'],
            fte_minimum       = request.POST.get('fte_minimum', 1),
            dasar_perhitungan = request.POST.get('dasar_perhitungan', ''),
            tahun             = request.POST['tahun'],
        )
        messages.success(request, 'FTE Standard berhasil ditambahkan.')
        return redirect('od:fte_standard_list')

    company = _get_company(request)
    depts    = Department.objects.filter(company=company) if company else Department.objects.all()
    jabatans = Position.objects.filter(company=company, aktif=True) if company else Position.objects.filter(aktif=True)

    return render(request, 'od/fte_standard_form.html', {
        'depts': depts, 'jabatans': jabatans, 'action': 'Tambah',
        'tahun_default': timezone.now().year,
    })


@login_required
@addon_required('od')
def fte_standard_edit(request, pk):
    obj = get_object_or_404(FTEStandard, pk=pk)
    company = _company(request)
    if request.method == 'POST':
        obj.department_id     = request.POST['department_id']
        obj.jabatan_id        = request.POST.get('jabatan_id') or None
        obj.fte_ideal         = request.POST['fte_ideal']
        obj.fte_minimum       = request.POST.get('fte_minimum', 1)
        obj.dasar_perhitungan = request.POST.get('dasar_perhitungan', '')
        obj.tahun             = request.POST['tahun']
        obj.save()
        messages.success(request, 'FTE Standard diperbarui.')
        return redirect('od:fte_standard_list')

    company = _get_company(request)
    depts    = Department.objects.filter(company=company) if company else Department.objects.all()
    jabatans = Position.objects.filter(company=company, aktif=True) if company else Position.objects.filter(aktif=True)

    return render(request, 'od/fte_standard_form.html', {
        'obj': obj, 'depts': depts, 'jabatans': jabatans, 'action': 'Edit'
    })


@login_required
@addon_required('od')
def fte_standard_delete(request, pk):
    get_object_or_404(FTEStandard, pk=pk).delete()
    messages.success(request, 'FTE Standard dihapus.')
    return redirect('od:fte_standard_list')


# ══════════════════════════════════════════════════════════════════════════════
#  FTE PLANNING — Analisis Gap Headcount vs Ideal
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def fte_planning(request):
    company = _company(request)

    # Hitung headcount aktual per dept + jabatan, compare ke FTE Standard
    company = _get_company(request)
    depts = Department.objects.filter(company=company) if company else Department.objects.all()
    if company:
        depts = depts.filter(company=company)

    employees = _emp_qs(request).select_related('department', 'jabatan')

    analysis = []
    for dept in depts:
        dept_emps = employees.filter(department=dept)
        dept_hc   = dept_emps.count()

        # FTE standard level dept (tanpa jabatan spesifik)
        fte_dept = FTEStandard.objects.filter(department=dept, jabatan=None)
        if company:
            fte_dept = fte_dept.filter(company=company)
        fte_dept = fte_dept.order_by('-tahun').first()

        jabatan_rows = []
        jabatans_in_dept = Position.objects.filter(
            id__in=dept_emps.values_list('jabatan_id', flat=True).distinct()
        )
        for jab in jabatans_in_dept:
            hc = dept_emps.filter(jabatan=jab).count()
            fte_jab = FTEStandard.objects.filter(department=dept, jabatan=jab)
            if company:
                fte_jab = fte_jab.filter(company=company)
            fte_jab = fte_jab.order_by('-tahun').first()

            gap    = round(hc - float(fte_jab.fte_ideal), 1) if fte_jab else None
            status = None
            if gap is not None:
                status = 'over' if gap > 0.5 else ('under' if gap < -0.5 else 'ideal')

            jabatan_rows.append({
                'jabatan'  : jab,
                'headcount': hc,
                'fte_ideal': float(fte_jab.fte_ideal) if fte_jab else None,
                'gap'      : gap,
                'status'   : status,
            })

        dept_gap    = round(dept_hc - float(fte_dept.fte_ideal), 1) if fte_dept else None
        dept_status = None
        if dept_gap is not None:
            dept_status = 'over' if dept_gap > 0.5 else ('under' if dept_gap < -0.5 else 'ideal')

        analysis.append({
            'dept'         : dept,
            'headcount'    : dept_hc,
            'fte_ideal'    : float(fte_dept.fte_ideal) if fte_dept else None,
            'gap'          : dept_gap,
            'status'       : dept_status,
            'jabatan_rows' : jabatan_rows,
        })

    # Summary counts
    total_over  = sum(1 for a in analysis if a['status'] == 'over')
    total_under = sum(1 for a in analysis if a['status'] == 'under')
    total_ideal = sum(1 for a in analysis if a['status'] == 'ideal')
    total_no_std = sum(1 for a in analysis if a['status'] is None)

    # Run simpan snapshot jika POST
    if request.method == 'POST' and request.POST.get('action') == 'save_snapshot':
        saved = 0
        for a in analysis:
            if a['fte_ideal'] is not None:
                FTEPlanningResult.objects.create(
                    company         = company,
                    department      = a['dept'],
                    jabatan         = None,
                    headcount_aktual= a['headcount'],
                    fte_ideal       = a['fte_ideal'],
                    catatan         = f'Snapshot auto {timezone.now().strftime("%Y-%m-%d %H:%M")}',
                )
                saved += 1
        messages.success(request, f'Snapshot disimpan untuk {saved} departemen.')
        return redirect('od:fte_planning')

    ctx = {
        'analysis'    : analysis,
        'total_over'  : total_over,
        'total_under' : total_under,
        'total_ideal' : total_ideal,
        'total_no_std': total_no_std,
    }
    return render(request, 'od/fte_planning.html', ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE (redirect ke performance app dengan konteks OD)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def od_performance_dashboard(request):
    """Proxy view — redirect ke performance dashboard dalam konteks OD."""
    return redirect('perf_dashboard')


# ══════════════════════════════════════════════════════════════════════════════
#  OD FASE 2 — COMPETENCY MATRIX & GAP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

from .models import (
    CompetencyCategory, Competency, PositionCompetency, EmployeeCompetency
)


def _get_company(request):
    """Helper multi-tenant: ambil company aktif dari request."""
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        from apps.core.models import Company
        company = Company.objects.first()
    return company


# ── Kategori Kompetensi ───────────────────────────────────────────────────────

@login_required
@addon_required('od')
def competency_category_list(request):
    company = _company(request)
    qs = CompetencyCategory.objects.filter(company=company) if company else CompetencyCategory.objects.all()
    return render(request, 'od/competency_category_list.html', {'kategori_list': qs})


@login_required
@addon_required('od')
def competency_category_create(request):
    company = _company(request)
    if request.method == 'POST':
        p = request.POST
        CompetencyCategory.objects.create(
            company   = company,
            nama      = p.get('nama', '').strip(),
            deskripsi = p.get('deskripsi', '').strip(),
            warna     = p.get('warna', '#818cf8'),
            urutan    = p.get('urutan') or 0,
        )
        messages.success(request, 'Kategori kompetensi berhasil ditambahkan.')
        return redirect('od:competency_category_list')
    return render(request, 'od/competency_category_form.html', {'action': 'Tambah'})


@login_required
@addon_required('od')
def competency_category_edit(request, pk):
    company = _company(request)
    obj = get_object_or_404(CompetencyCategory, pk=pk, company=company)
    if request.method == 'POST':
        p = request.POST
        obj.nama      = p.get('nama', '').strip()
        obj.deskripsi = p.get('deskripsi', '').strip()
        obj.warna     = p.get('warna', '#818cf8')
        obj.urutan    = p.get('urutan') or 0
        obj.aktif     = 'aktif' in p
        obj.save()
        messages.success(request, 'Kategori kompetensi diperbarui.')
        return redirect('od:competency_category_list')
    return render(request, 'od/competency_category_form.html', {'action': 'Edit', 'obj': obj})


@login_required
@addon_required('od')
def competency_category_delete(request, pk):
    company = _company(request)
    obj = get_object_or_404(CompetencyCategory, pk=pk, company=company)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Kategori dihapus.')
    return redirect('od:competency_category_list')


@login_required
@addon_required('od')
def competency_list(request):
    company = _company(request)
    qs = Competency.objects.select_related('kategori').filter(aktif=True)
    if company:
        qs = qs.filter(company=company)
    kategori_qs = CompetencyCategory.objects.all()
    if company:
        kategori_qs = kategori_qs.filter(company=company)
    return render(request, 'od/competency_list.html', {
        'competencies': qs, 'kategori_list': kategori_qs
    })


@login_required
@addon_required('od')
def competency_create(request):
    company = _company(request)
    if request.method == 'POST':
        Competency.objects.create(
            company     = company,
            kode        = request.POST['kode'],
            nama        = request.POST['nama'],
            kategori_id = request.POST.get('kategori_id') or None,
            deskripsi   = request.POST.get('deskripsi', ''),
            level_1_desc = request.POST.get('level_1_desc', ''),
            level_2_desc = request.POST.get('level_2_desc', ''),
            level_3_desc = request.POST.get('level_3_desc', ''),
            level_4_desc = request.POST.get('level_4_desc', ''),
            level_5_desc = request.POST.get('level_5_desc', ''),
        )
        messages.success(request, 'Kompetensi berhasil ditambahkan.')
        return redirect('od:competency_list')
    kategori_qs = CompetencyCategory.objects.filter(company=company) if company else CompetencyCategory.objects.all()
    return render(request, 'od/competency_form.html', {
        'kategori_list': kategori_qs, 'action': 'Tambah'
    })


@login_required
@addon_required('od')
def competency_edit(request, pk):
    obj = get_object_or_404(Competency, pk=pk)
    company = _company(request)
    if request.method == 'POST':
        obj.kode        = request.POST['kode']
        obj.nama        = request.POST['nama']
        obj.kategori_id = request.POST.get('kategori_id') or None
        obj.deskripsi   = request.POST.get('deskripsi', '')
        for i in range(1, 6):
            setattr(obj, f'level_{i}_desc', request.POST.get(f'level_{i}_desc', ''))
        obj.aktif = 'aktif' in request.POST
        obj.save()
        messages.success(request, 'Kompetensi diperbarui.')
        return redirect('od:competency_list')
    kategori_qs = CompetencyCategory.objects.filter(company=company) if company else CompetencyCategory.objects.all()
    return render(request, 'od/competency_form.html', {
        'obj': obj, 'kategori_list': kategori_qs, 'action': 'Edit'
    })


@login_required
@addon_required('od')
def competency_delete(request, pk):
    get_object_or_404(Competency, pk=pk).delete()
    messages.success(request, 'Kompetensi dihapus.')
    return redirect('od:competency_list')


@login_required
@addon_required('od')
def position_competency(request, jabatan_id):
    """Kelola standar kompetensi per jabatan."""
    jabatan = get_object_or_404(Position, pk=jabatan_id)
    company = _company(request)
    std_qs  = PositionCompetency.objects.filter(jabatan=jabatan).select_related('competency')
    all_comp = Competency.objects.filter(aktif=True)
    if company:
        all_comp = all_comp.filter(company=company)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            comp_id  = request.POST['competency_id']
            level    = int(request.POST.get('level_required', 3))
            bobot    = int(request.POST.get('bobot', 1))
            wajib    = 'wajib' in request.POST
            PositionCompetency.objects.update_or_create(
                jabatan_id=jabatan_id, competency_id=comp_id,
                defaults=dict(company=company, level_required=level, bobot=bobot, wajib=wajib)
            )
            messages.success(request, 'Standar kompetensi ditambahkan.')
        elif action == 'delete':
            PositionCompetency.objects.filter(pk=request.POST.get('pc_id')).delete()
            messages.success(request, 'Standar kompetensi dihapus.')
        return redirect('od:position_competency', jabatan_id=jabatan_id)

    return render(request, 'od/position_competency.html', {
        'jabatan': jabatan, 'standards': std_qs, 'all_competencies': all_comp,
        'level_range': range(1, 6),
    })


@login_required
@addon_required('od')
def competency_matrix(request):
    """Matrix kompetensi: baris = karyawan, kolom = kompetensi. Gap ditandai."""
    company  = _company(request)
    dept_id  = request.GET.get('dept')
    periode  = request.GET.get('periode', str(timezone.now().year))

    employees = _emp_qs(request).select_related('jabatan', 'department')
    if dept_id:
        employees = employees.filter(department_id=dept_id)

    competencies = Competency.objects.filter(aktif=True)
    if company:
        competencies = competencies.filter(company=company)

    # Build matrix: {emp_id: {comp_id: {aktual, required, gap}}}
    assessments = EmployeeCompetency.objects.filter(
        employee__in=employees, competency__in=competencies, periode=periode
    ).select_related('employee', 'competency')
    ass_map = {}
    for a in assessments:
        ass_map.setdefault(a.employee_id, {})[a.competency_id] = a.level_aktual

    requirements = PositionCompetency.objects.filter(
        jabatan__in=employees.values_list('jabatan_id', flat=True).distinct()
    ).select_related('jabatan', 'competency')
    req_map = {}
    for r in requirements:
        req_map.setdefault(r.jabatan_id, {})[r.competency_id] = r.level_required

    matrix = []
    for emp in employees:
        row = {'employee': emp, 'cells': []}
        for comp in competencies:
            aktual   = ass_map.get(emp.pk, {}).get(comp.pk)
            required = req_map.get(emp.jabatan_id, {}).get(comp.pk)
            gap      = (aktual - required) if (aktual and required) else None
            row['cells'].append({
                'competency': comp, 'aktual': aktual,
                'required': required, 'gap': gap
            })
        matrix.append(row)

    company = _get_company(request)
    depts = Department.objects.filter(company=company) if company else Department.objects.all()
    return render(request, 'od/competency_matrix.html', {
        'matrix'      : matrix,
        'competencies': competencies,
        'depts'       : depts,
        'selected_dept': dept_id,
        'periode'     : periode,
    })


@login_required
@addon_required('od')
def employee_competency_assess(request, employee_id):
    """Input/edit penilaian kompetensi satu karyawan."""
    from apps.employees.models import Employee as EmpModel
    employee = get_object_or_404(EmpModel, pk=employee_id)
    company  = _company(request)
    periode  = request.GET.get('periode', str(timezone.now().year))

    competencies = Competency.objects.filter(aktif=True)
    if company:
        competencies = competencies.filter(company=company)

    # Existing assessments
    existing = {a.competency_id: a for a in EmployeeCompetency.objects.filter(
        employee=employee, periode=periode
    )}

    if request.method == 'POST':
        periode_post = request.POST.get('periode', periode)
        metode = request.POST.get('metode', 'manager')
        saved = 0
        for comp in competencies:
            level_key = f'level_{comp.pk}'
            level_val = request.POST.get(level_key)
            if level_val:
                EmployeeCompetency.objects.update_or_create(
                    employee=employee, competency=comp, periode=periode_post,
                    defaults=dict(
                        company   = company,
                        level_aktual = int(level_val),
                        metode    = metode,
                        catatan   = request.POST.get(f'catatan_{comp.pk}', ''),
                    )
                )
                saved += 1
        messages.success(request, f'{saved} kompetensi berhasil dinilai.')
        return redirect('od:competency_matrix')

    # Required per jabatan
    req_map = {}
    if employee.jabatan:
        for r in PositionCompetency.objects.filter(jabatan=employee.jabatan):
            req_map[r.competency_id] = r.level_required

    comp_rows = []
    for comp in competencies:
        comp_rows.append({
            'comp'    : comp,
            'aktual'  : existing.get(comp.pk) and existing[comp.pk].level_aktual,
            'required': req_map.get(comp.pk),
        })

    return render(request, 'od/employee_competency_form.html', {
        'employee' : employee,
        'comp_rows': comp_rows,
        'periode'  : periode,
        'level_range': range(1, 6),
    })


@login_required
@addon_required('od')
def competency_gap_report(request):
    """Laporan gap kompetensi: siapa yang paling butuh development."""
    company = _company(request)
    periode = request.GET.get('periode', str(timezone.now().year))
    dept_id = request.GET.get('dept')

    employees = _emp_qs(request).select_related('jabatan', 'department')
    if dept_id:
        employees = employees.filter(department_id=dept_id)

    report = []
    for emp in employees:
        if not emp.jabatan:
            continue
        required = PositionCompetency.objects.filter(jabatan=emp.jabatan).select_related('competency')
        assessed = {a.competency_id: a.level_aktual for a in EmployeeCompetency.objects.filter(
            employee=emp, periode=periode
        )}
        gaps = []
        total_gap = 0
        for req in required:
            aktual = assessed.get(req.competency_id, 0)
            gap    = aktual - req.level_required
            total_gap += gap
            if gap < 0:
                gaps.append({
                    'competency': req.competency, 'aktual': aktual,
                    'required': req.level_required, 'gap': gap, 'wajib': req.wajib
                })
        gaps.sort(key=lambda x: x['gap'])  # paling negatif duluan
        report.append({
            'employee'    : emp,
            'gaps'        : gaps,
            'total_gap'   : total_gap,
            'gap_count'   : len(gaps),
            'pct_assessed': round(len(assessed) / required.count() * 100) if required.count() else 0,
        })
    report.sort(key=lambda x: x['total_gap'])  # urut: paling banyak gap dulu

    has_gap = any(r['gaps'] for r in report)
    company = _get_company(request)
    depts = Department.objects.filter(company=company) if company else Department.objects.all()
    return render(request, 'od/competency_gap_report.html', {
        'report'      : report,
        'depts'       : depts,
        'selected_dept': dept_id,
        'periode'     : periode,
        'has_gap'     : has_gap,
    })
