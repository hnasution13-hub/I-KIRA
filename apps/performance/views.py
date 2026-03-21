from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import (
    PeriodePenilaian, KPITemplate, PenilaianKaryawan, KPIItem, ReviewAtasan
)
from apps.employees.models import Employee
from apps.core.models import Company
from apps.core.addon_decorators import addon_required

def _get_company(request):
    """Helper multi-tenant: ambil company aktif dari request."""
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        from apps.core.models import Company
        company = Company.objects.first()
    return company




def _company(request):
    return getattr(request, 'company', None)


def _is_hr(request):
    return getattr(request, 'is_developer', False) or \
           getattr(request, 'is_administrator', False) or \
           getattr(request.user, 'role', '') in ['administrator', 'admin', 'hr_manager', 'hr_staff']


def _emp_qs(request):
    company = _get_company(request)
    qs = Employee.objects.filter(company=company, status='Aktif') if company else Employee.objects.filter(status='Aktif')
    c  = _company(request)
    if c:
        qs = qs.filter(company=c)
    return qs


def _approval_engine(penilaian):
    """Helper: buat ApprovalEngine untuk penilaian kinerja."""
    from utils.approval_engine import ApprovalEngine
    return ApprovalEngine(
        company=penilaian.company,
        modul='performance',
        jabatan_pemohon=penilaian.employee.jabatan if penilaian.employee else None,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@addon_required('od')
def perf_dashboard(request):
    company = _company(request)

    def base_qs():
        qs = PenilaianKaryawan.objects.select_related('employee', 'periode')
        if company:
            qs = qs.filter(company=company)
        return qs

    periode_aktif_qs = PeriodePenilaian.objects.filter(status='aktif')
    if company:
        periode_aktif_qs = periode_aktif_qs.filter(company=company)
    periode_aktif = periode_aktif_qs.first()

    total_penilaian  = base_qs().count()
    menunggu_review  = base_qs().filter(status='submit').count()
    sudah_approved   = base_qs().filter(status='approved').count()
    total_karyawan   = _emp_qs(request).count()

    predikat_dist = (
        base_qs().filter(status='approved')
        .values('predikat')
        .annotate(jumlah=Count('id'))
        .order_by('-jumlah')
    )
    chart_predikat_labels = [p['predikat'] for p in predikat_dist]
    chart_predikat_data   = [p['jumlah']   for p in predikat_dist]

    ranking_qs = base_qs().filter(status='approved').order_by('-skor_akhir')
    if periode_aktif:
        ranking_qs = ranking_qs.filter(periode=periode_aktif)
    ranking = ranking_qs[:10]

    perlu_aksi = base_qs().filter(status='submit').select_related(
        'employee', 'periode', 'atasan'
    ).order_by('tanggal_submit')[:10]

    company = _get_company(request)
    semua_periode = PeriodePenilaian.objects.filter(company=company) if company else PeriodePenilaian.objects.all()
    if company:
        semua_periode = semua_periode.filter(company=company)

    skor_per_periode = (
        base_qs().filter(status='approved')
        .values('periode__nama')
        .annotate(rata=Avg('skor_akhir'))
        .order_by('periode__tanggal_mulai')
    )
    chart_periode_labels = [s['periode__nama'] for s in skor_per_periode]
    chart_periode_data   = [round(float(s['rata']), 1) for s in skor_per_periode]

    ctx = {
        'total_penilaian'      : total_penilaian,
        'menunggu_review'      : menunggu_review,
        'sudah_approved'       : sudah_approved,
        'total_karyawan'       : total_karyawan,
        'periode_aktif'        : periode_aktif,
        'ranking'              : ranking,
        'perlu_aksi'           : perlu_aksi,
        'semua_periode'        : semua_periode,
        'chart_predikat_labels': json.dumps(chart_predikat_labels),
        'chart_predikat_data'  : json.dumps(chart_predikat_data),
        'chart_periode_labels' : json.dumps(chart_periode_labels),
        'chart_periode_data'   : json.dumps(chart_periode_data),
    }
    return render(request, 'performance/dashboard.html', ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  PERIODE PENILAIAN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def periode_list(request):
    company = _company(request)
    company = _get_company(request)
    qs = PeriodePenilaian.objects.filter(company=company) if company else PeriodePenilaian.objects.all()
    if company:
        qs = qs.filter(company=company)
    return render(request, 'performance/periode_list.html', {'periodes': qs})


@login_required
def periode_create(request):
    if request.method == 'POST':
        company = _company(request)
        if not company:
            company = Company.objects.filter(id=request.POST.get('company_id')).first()
        PeriodePenilaian.objects.create(
            company         = company,
            nama            = request.POST['nama'],
            tipe            = request.POST['tipe'],
            tanggal_mulai   = request.POST['tanggal_mulai'],
            tanggal_selesai = request.POST['tanggal_selesai'],
            status          = request.POST.get('status', 'draft'),
            deskripsi       = request.POST.get('deskripsi', ''),
        )
        messages.success(request, 'Periode penilaian berhasil dibuat.')
        return redirect('periode_list')
    companies = Company.objects.all() if not _company(request) else None
    return render(request, 'performance/periode_form.html', {'companies': companies, 'action': 'Tambah'})


@login_required
def periode_edit(request, pk):
    p = get_object_or_404(PeriodePenilaian, pk=pk, **({'company': request.company} if request.company else {}))
    if request.method == 'POST':
        p.nama            = request.POST['nama']
        p.tipe            = request.POST['tipe']
        p.tanggal_mulai   = request.POST['tanggal_mulai']
        p.tanggal_selesai = request.POST['tanggal_selesai']
        p.status          = request.POST.get('status', p.status)
        p.deskripsi       = request.POST.get('deskripsi', '')
        p.save()
        messages.success(request, 'Periode berhasil diperbarui.')
        return redirect('periode_list')
    return render(request, 'performance/periode_form.html', {'obj': p, 'action': 'Edit'})


@login_required
@require_POST
def periode_delete(request, pk):
    p = get_object_or_404(PeriodePenilaian, pk=pk, **({'company': request.company} if request.company else {}))
    messages.success(request, 'Periode dihapus.')
    return redirect('periode_list')


# ══════════════════════════════════════════════════════════════════════════════
#  KPI TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def kpi_template_list(request):
    company = _company(request)
    company = _get_company(request)
    qs = KPITemplate.objects.filter(company=company, aktif=True) if company else KPITemplate.objects.filter(aktif=True)
    if company:
        qs = qs.filter(company=company)
    return render(request, 'performance/kpi_template_list.html', {'templates': qs})


@login_required
def kpi_template_create(request):
    if request.method == 'POST':
        company = _company(request)
        if not company:
            company = Company.objects.get(pk=request.POST['company_id'])
        KPITemplate.objects.create(
            company   = company,
            nama      = request.POST['nama'],
            deskripsi = request.POST.get('deskripsi', ''),
            satuan    = request.POST['satuan'],
            arah      = request.POST.get('arah', 'tinggi'),
            kategori  = request.POST.get('kategori', ''),
        )
        messages.success(request, 'Template KPI ditambahkan.')
        return redirect('kpi_template_list')
    return render(request, 'performance/kpi_template_form.html', {'action': 'Tambah'})


@login_required
def kpi_template_edit(request, pk):
    tmpl = get_object_or_404(KPITemplate, pk=pk, **({'company': request.company} if request.company else {}))
    if request.method == 'POST':
        tmpl.nama      = request.POST['nama']
        tmpl.deskripsi = request.POST.get('deskripsi', '')
        tmpl.satuan    = request.POST['satuan']
        tmpl.arah      = request.POST.get('arah', 'tinggi')
        tmpl.kategori  = request.POST.get('kategori', '')
        tmpl.save()
        messages.success(request, 'Template KPI diperbarui.')
        return redirect('kpi_template_list')
    return render(request, 'performance/kpi_template_form.html', {'obj': tmpl, 'action': 'Edit'})


@login_required
@require_POST
def kpi_template_delete(request, pk):
    KPITemplate.objects.filter(pk=pk).update(aktif=False)
    messages.success(request, 'Template KPI dinonaktifkan.')
    return redirect('kpi_template_list')


# ══════════════════════════════════════════════════════════════════════════════
#  PENILAIAN KARYAWAN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def penilaian_list(request):
    company  = _company(request)
    qs = PenilaianKaryawan.objects.select_related('employee', 'periode', 'atasan')
    if company:
        qs = qs.filter(company=company)

    # Filter: hanya tampilkan penilaian sendiri untuk employee biasa
    user = request.user
    if not _is_hr(request) and not user.is_developer:
        try:
            emp = user.employee
            qs  = qs.filter(Q(employee=emp) | Q(atasan=emp))
        except Exception:
            qs = qs.none()

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    ctx = {
        'penilaian_list': qs.order_by('-periode__tanggal_mulai', 'employee__nama'),
        'status_choices': PenilaianKaryawan.STATUS_CHOICES,
    }
    return render(request, 'performance/penilaian_list.html', ctx)


@login_required
def penilaian_create(request):
    company   = _company(request)
    employees = _emp_qs(request).select_related('jabatan', 'department')
    company = _get_company(request)
    periodes  = PeriodePenilaian.objects.filter(company=company, status='aktif') if company else PeriodePenilaian.objects.filter(status='aktif')
    if company:
        periodes = periodes.filter(company=company)

    if request.method == 'POST':
        emp_id     = request.POST['employee_id']
        periode_id = request.POST['periode_id']
        employee   = get_object_or_404(Employee, pk=emp_id, **({'company': request.company} if request.company else {}))
        periode    = get_object_or_404(PeriodePenilaian, pk=periode_id, **({'company': request.company} if request.company else {}))

        if PenilaianKaryawan.objects.filter(employee=employee, periode=periode).exists():
            messages.error(request, f'Penilaian {employee.nama} untuk periode {periode.nama} sudah ada.')
            return redirect('penilaian_create')

        # ── Resolve atasan otomatis dari ApprovalEngine ──────────────────
        from utils.approval_engine import ApprovalEngine
        engine = ApprovalEngine(
            company=company or employee.company,
            modul='performance',
            jabatan_pemohon=employee.jabatan,
        )
        atasan_emp = engine.get_first_approver_employee()
        atasan_id  = request.POST.get('atasan_id') or (atasan_emp.pk if atasan_emp else None)

        penilaian = PenilaianKaryawan.objects.create(
            company  = company or employee.company,
            employee = employee,
            periode  = periode,
            atasan_id= atasan_id,
            status   = 'draft',
        )

        template_ids = request.POST.getlist('template_ids')
        for tid in template_ids:
            tmpl = KPITemplate.objects.filter(pk=tid).first()
            if tmpl:
                KPIItem.objects.create(
                    penilaian = penilaian,
                    template  = tmpl,
                    nama_kpi  = tmpl.nama,
                    satuan    = tmpl.satuan,
                    arah      = tmpl.arah,
                    bobot     = round(100 / len(template_ids), 2),
                    target    = 0,
                )

        aspek_defaults = ['Kedisiplinan', 'Komunikasi', 'Teamwork', 'Inisiatif', 'Kualitas Kerja']
        for aspek in aspek_defaults:
            ReviewAtasan.objects.create(penilaian=penilaian, aspek=aspek, bobot=20)

        messages.success(request, f'Penilaian {employee.nama} berhasil dibuat.')
        return redirect('penilaian_detail', pk=penilaian.pk)

    kpi_templates = KPITemplate.objects.filter(aktif=True)
    if company:
        kpi_templates = kpi_templates.filter(company=company)

    # Bangun map dept_id -> list atasan untuk filter JS di template
    import json as _json
    atasan_by_dept = {}
    for e in employees.select_related('department', 'jabatan'):
        dept_id = str(e.department_id) if e.department_id else '0'
        atasan_by_dept.setdefault(dept_id, []).append({
            'id'  : e.pk,
            'nama': f"{e.nama} — {e.jabatan}",
        })

    ctx = {
        'employees'      : employees,
        'periodes'       : periodes,
        'kpi_templates'  : kpi_templates,
        'atasan_list'    : employees,
        'atasan_by_dept_json': _json.dumps(atasan_by_dept),
    }
    return render(request, 'performance/penilaian_create.html', ctx)


@login_required
def penilaian_detail(request, pk):
    penilaian = get_object_or_404(
        PenilaianKaryawan.objects.select_related('employee', 'periode', 'atasan'),
        pk=pk, **({'company': request.company} if request.company else {})
    )
    kpi_items    = penilaian.kpi_items.all()
    review_items = penilaian.review_items.all()

    # Approval chain untuk ditampilkan
    from utils.approval_engine import get_approval_chain_display
    approval_chain = get_approval_chain_display(penilaian.employee, 'performance')

    # Cek apakah user ini bisa approve
    engine     = _approval_engine(penilaian)
    can_approve = engine.can_approve(request.user)

    ctx = {
        'penilaian'         : penilaian,
        'kpi_items'         : kpi_items,
        'review_items'      : review_items,
        'total_bobot_kpi'   : sum(float(i.bobot) for i in kpi_items),
        'total_bobot_review': sum(float(i.bobot) for i in review_items),
        'approval_chain'    : approval_chain,
        'can_approve'       : can_approve,
    }
    return render(request, 'performance/penilaian_detail.html', ctx)


@login_required
def penilaian_input_kpi(request, pk):
    penilaian = get_object_or_404(PenilaianKaryawan, pk=pk, **({'company': request.company} if request.company else {}))
    if penilaian.status not in ['draft', 'rejected']:
        messages.warning(request, 'Penilaian tidak bisa diedit pada status ini.')
        return redirect('penilaian_detail', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        for item in penilaian.kpi_items.all():
            target    = request.POST.get(f'target_{item.pk}', '').strip()
            realisasi = request.POST.get(f'realisasi_{item.pk}', '').strip()
            bobot     = request.POST.get(f'bobot_{item.pk}', str(item.bobot)).strip()
            catatan   = request.POST.get(f'catatan_{item.pk}', '').strip()
            item.target    = float(target)    if target    else item.target
            item.realisasi = float(realisasi) if realisasi else None
            item.bobot     = float(bobot)     if bobot     else item.bobot
            item.catatan   = catatan
            item.save()

        penilaian.catatan_karyawan = request.POST.get('catatan_karyawan', '')
        penilaian.hitung_skor()

        if action == 'submit':
            penilaian.status         = 'submit'
            penilaian.tanggal_submit = timezone.now()
            penilaian.save(update_fields=['status', 'tanggal_submit', 'catatan_karyawan'])
            messages.success(request, 'Penilaian berhasil diajukan ke atasan.')
        else:
            penilaian.save(update_fields=['catatan_karyawan'])
            messages.success(request, 'Data tersimpan.')

        return redirect('penilaian_detail', pk=pk)

    return render(request, 'performance/penilaian_input_kpi.html', {
        'penilaian': penilaian,
        'kpi_items': penilaian.kpi_items.all(),
    })


@login_required
def penilaian_review_atasan(request, pk):
    """
    Atasan mengisi review kualitatif & approve/reject via ApprovalEngine.
    Akses: HR, atasan jabatan (dari ApprovalMatrix / hierarki), atau developer.
    """
    penilaian = get_object_or_404(PenilaianKaryawan, pk=pk, **({'company': request.company} if request.company else {}))

    if not engine.can_approve(request.user):
        messages.error(request, 'Anda tidak berwenang mereview penilaian ini.')
        return redirect('penilaian_detail', pk=pk)

    if penilaian.status not in ['submit', 'review']:
        messages.warning(request, 'Penilaian belum diajukan atau sudah selesai.')
        return redirect('penilaian_detail', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        for item in penilaian.review_items.all():
            skor    = request.POST.get(f'skor_{item.pk}', '').strip()
            catatan = request.POST.get(f'catatan_{item.pk}', '').strip()
            bobot   = request.POST.get(f'bobot_{item.pk}', str(item.bobot)).strip()
            item.skor    = int(skor)    if skor    else None
            item.catatan = catatan
            item.bobot   = float(bobot) if bobot   else item.bobot
            item.save()

        # Hitung skor review
        review_items = penilaian.review_items.all()
        total_bobot  = sum(float(i.bobot) for i in review_items)
        if total_bobot > 0:
            weighted = sum(
                (i.skor_persen * float(i.bobot) / 100)
                for i in review_items if i.skor_persen is not None
            )
            penilaian.skor_review = round(weighted / total_bobot * 100, 2)
        else:
            penilaian.skor_review = 0

        penilaian.catatan_atasan = request.POST.get('catatan_atasan', '')
        penilaian.hitung_skor()
        catatan = request.POST.get('catatan_atasan', '')

        if action == 'approve':
            # Gunakan ApprovalEngine untuk approve
            engine.approve(penilaian, request.user, catatan=catatan)
            messages.success(request, f'Penilaian {penilaian.employee.nama} disetujui.')
        elif action == 'reject':
            engine.reject(penilaian, request.user, catatan=catatan)
            messages.warning(request, f'Penilaian dikembalikan ke {penilaian.employee.nama}.')
        else:
            penilaian.status = 'review'
            penilaian.save(update_fields=['status', 'catatan_atasan', 'skor_review'])
            messages.success(request, 'Review tersimpan.')

        return redirect('penilaian_detail', pk=pk)

    return render(request, 'performance/penilaian_review.html', {
        'penilaian'   : penilaian,
        'kpi_items'   : penilaian.kpi_items.all(),
        'review_items': penilaian.review_items.all(),
    })


@login_required
@require_POST
def penilaian_delete(request, pk):
    p = get_object_or_404(PenilaianKaryawan, pk=pk, **({'company': request.company} if request.company else {}))
    messages.success(request, 'Penilaian dihapus.')
    return redirect('penilaian_list')


# ══════════════════════════════════════════════════════════════════════════════
#  KPI ITEM — tambah/hapus inline
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def kpi_item_add(request, penilaian_pk):
    penilaian = get_object_or_404(PenilaianKaryawan, pk=penilaian_pk, **({'company': request.company} if request.company else {}))
    KPIItem.objects.create(
        penilaian = penilaian,
        nama_kpi  = request.POST.get('nama_kpi', 'KPI Baru'),
        satuan    = request.POST.get('satuan', '%'),
        arah      = request.POST.get('arah', 'tinggi'),
        bobot     = float(request.POST.get('bobot', 10)),
        target    = float(request.POST.get('target', 0)),
    )
    messages.success(request, 'KPI ditambahkan.')
    return redirect('penilaian_input_kpi', pk=penilaian_pk)


@login_required
@require_POST
def kpi_item_delete(request, pk):
    item = get_object_or_404(KPIItem, pk=pk, penilaian__company=request.company) if request.company else get_object_or_404(KPIItem, pk=pk)
    penilaian_pk = item.penilaian_id
    item.delete()
    messages.success(request, 'KPI dihapus.')
    return redirect('penilaian_input_kpi', pk=penilaian_pk)


# ══════════════════════════════════════════════════════════════════════════════
#  RANKING
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def ranking_view(request):
    company    = _company(request)
    periode_id = request.GET.get('periode')

    periodes = PeriodePenilaian.objects.all()
    if company:
        periodes = periodes.filter(company=company)

    qs = PenilaianKaryawan.objects.filter(status='approved').select_related(
        'employee', 'periode', 'employee__jabatan', 'employee__department'
    )
    if company:
        qs = qs.filter(company=company)
    if periode_id:
        qs = qs.filter(periode_id=periode_id)

    ranking = qs.order_by('-skor_akhir')

    predikat_stats = {}
    for p in ranking:
        predikat_stats[p.predikat] = predikat_stats.get(p.predikat, 0) + 1

    ctx = {
        'ranking'         : ranking,
        'periodes'        : periodes,
        'selected_periode': periode_id,
        'predikat_stats'  : predikat_stats,
    }
    return render(request, 'performance/ranking.html', ctx)
