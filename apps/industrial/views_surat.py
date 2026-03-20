"""
Views tambahan: SuratPeringatan, SuratPHK, SuratKeteranganKerja
Append ke apps/industrial/views.py
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import hr_required
from django.utils import timezone
from datetime import date, timedelta

from apps.core.utils import get_company_qs, get_employee_related_qs
from apps.employees.models import Employee
from .models import (
    Violation, SuratPeringatan, SuratPHK, SuratKeteranganKerja,
    PerjanjianBersama,
)
from utils.sp_rules import (
    PELANGGARAN_MAP, TINGKAT_TO_SP, SP_LEVEL_LABEL,
    get_sp_level_suggestion, get_pelanggaran_by_kategori,
)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _get_sp_aktif(employee):
    """Return list level SP yang masih aktif untuk karyawan."""
    today = date.today()
    return list(
        SuratPeringatan.objects.filter(
            employee=employee,
            status='aktif',
            tanggal_berlaku_sampai__gte=today,
        ).values_list('level', flat=True)
    )


def _get_company(request, employee=None):
    return request.company or (employee.company if employee else None)


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PERINGATAN — LIST
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def sp_list(request):
    company = _get_company(request)
    today   = date.today()

    # Auto-update status expired
    SuratPeringatan.objects.filter(
        company=company,
        status='aktif',
        tanggal_berlaku_sampai__lt=today,
    ).update(status='expired')

    qs = get_employee_related_qs(SuratPeringatan, request).select_related(
        'employee', 'violation'
    )

    # Filter
    q       = request.GET.get('q', '').strip()
    level   = request.GET.get('level', '')
    status  = request.GET.get('status', '')
    if q:
        qs = qs.filter(employee__nama__icontains=q)
    if level:
        qs = qs.filter(level=level)
    if status:
        qs = qs.filter(status=status)

    return render(request, 'industrial/sp_list.html', {
        'surat_peringatan': qs,
        'q': q, 'level_filter': level, 'status_filter': status,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PERINGATAN — CREATE (dari Violation atau mandiri)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def sp_create(request):
    company    = _get_company(request)
    violation  = None
    violation_id = request.GET.get('violation') or request.POST.get('violation_id')
    if violation_id:
        violation = get_object_or_404(Violation, pk=violation_id, **({'company': request.company} if request.company else {}))

    # Employee dari violation atau dari GET param
    employee   = None
    employee_id = request.GET.get('employee') or request.POST.get('employee_id')
    if violation:
        employee = violation.employee
    elif employee_id:
        employee = get_object_or_404(Employee, pk=employee_id, **({'company': request.company} if request.company else {}))

    # Hitung SP aktif & saran level
    sp_aktif        = _get_sp_aktif(employee) if employee else []
    kode_pelanggaran = request.GET.get('kode', '') or request.POST.get('kode_pelanggaran', '')
    suggestion      = get_sp_level_suggestion(kode_pelanggaran, sp_aktif) if kode_pelanggaran else None

    # ── POST: simpan SP ───────────────────────────────────────────────────────
    if request.method == 'POST' and employee:
        try:
            level = int(request.POST.get('level', 1))
            kode  = request.POST.get('kode_pelanggaran', '').strip()
            rule  = PELANGGARAN_MAP.get(kode, {})

            tanggal_sp = date.fromisoformat(request.POST.get('tanggal_sp'))
            berlaku_sampai = tanggal_sp + timedelta(days=180)  # 6 bulan

            # Cek apakah ada SP aktif di level sebelumnya untuk tracking eskalasi
            sp_aktif_objs = SuratPeringatan.objects.filter(
                employee=employee, status='aktif',
                tanggal_berlaku_sampai__gte=date.today(),
                level=level - 1,
            ).order_by('-tanggal_sp').first() if level > 1 else None

            sp = SuratPeringatan(
                company   = company or employee.company,
                employee  = employee,
                violation = violation,
                level     = level,
                kode_pelanggaran     = kode,
                label_pelanggaran    = rule.get('label', request.POST.get('label_pelanggaran', '')),
                kategori_pelanggaran = rule.get('kategori', ''),
                tingkat_pelanggaran  = rule.get('tingkat', ''),
                dasar_pasal          = rule.get('dasar_pasal', request.POST.get('dasar_pasal', '')),
                tanggal_sp           = tanggal_sp,
                tanggal_berlaku_sampai = berlaku_sampai,
                uraian_pelanggaran   = request.POST.get('uraian_pelanggaran', '').strip(),
                sanksi               = request.POST.get('sanksi', '').strip(),
                pernyataan_karyawan  = request.POST.get('pernyataan_karyawan', '').strip(),
                nama_penandatangan   = request.POST.get('nama_penandatangan', '').strip(),
                jabatan_penandatangan= request.POST.get('jabatan_penandatangan', '').strip(),
                catatan              = request.POST.get('catatan', '').strip(),
                is_eskalasi          = (sp_aktif_objs is not None),
                sp_sebelumnya        = sp_aktif_objs,
            )
            # Auto nomor jika kosong
            nomor = request.POST.get('nomor_sp', '').strip()
            sp.nomor_sp = nomor if nomor else sp.generate_nomor()
            sp.save()

            # Update status violation jika terhubung
            if violation:
                violation.status = 'Selesai'
                violation.save(update_fields=['status'])

            messages.success(request,
                f'<strong>{SP_LEVEL_LABEL[level]}</strong> untuk <strong>{employee.nama}</strong> berhasil diterbitkan.')
            return redirect('sp_detail', sp.pk)

        except Exception as e:
            import traceback; print(traceback.format_exc())
            messages.error(request, f'Gagal menyimpan: {e}')

    # ── Cek apakah perlu warning SP3 → PHK ───────────────────────────────────
    can_phk = (3 in sp_aktif)

    return render(request, 'industrial/sp_form.html', {
        'employee'         : employee,
        'violation'        : violation,
        'sp_aktif'         : sp_aktif,
        'suggestion'       : suggestion,
        'can_phk'          : can_phk,
        'pelanggaran_map'  : PELANGGARAN_MAP,
        'pelanggaran_by_kat': get_pelanggaran_by_kategori(),
        'sp_level_label'   : SP_LEVEL_LABEL,
        'company'          : company,
        'employees'        : get_company_qs(Employee, request, status='Aktif'),
        'today'            : date.today().isoformat(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PERINGATAN — DETAIL
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def sp_detail(request, pk):
    sp      = get_object_or_404(SuratPeringatan, pk=pk, **({'company': request.company} if request.company else {}))
    history = SuratPeringatan.objects.filter(
        employee=sp.employee
    ).order_by('tanggal_sp')
    return render(request, 'industrial/sp_detail.html', {
        'sp': sp, 'history': history,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PERINGATAN — PRINT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def sp_print(request, pk):
    sp = get_object_or_404(SuratPeringatan, pk=pk, **({'company': request.company} if request.company else {}))


# ══════════════════════════════════════════════════════════════════════════════
#  AJAX: get SP suggestion (untuk live update form)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def sp_suggest(request):
    from django.http import JsonResponse
    employee_id      = request.GET.get('employee_id')
    kode_pelanggaran = request.GET.get('kode', '')
    employee = None
    sp_aktif = []
    sp_history = []

    if employee_id:
        try:
            employee = Employee.objects.get(pk=employee_id)
            sp_aktif = _get_sp_aktif(employee)
            sp_history = list(
                SuratPeringatan.objects.filter(employee=employee)
                .order_by('-tanggal_sp')
                .values('level', 'nomor_sp', 'tanggal_sp', 'status',
                        'tanggal_berlaku_sampai', 'label_pelanggaran')[:10]
            )
            # Convert dates to string
            for item in sp_history:
                item['tanggal_sp'] = str(item['tanggal_sp'])
                item['tanggal_berlaku_sampai'] = str(item['tanggal_berlaku_sampai'])
                item['level_label'] = SP_LEVEL_LABEL.get(item['level'], '')
        except Employee.DoesNotExist:
            pass

    suggestion = get_sp_level_suggestion(kode_pelanggaran, sp_aktif) if kode_pelanggaran else {}
    return JsonResponse({
        'sp_aktif'   : sp_aktif,
        'sp_history' : sp_history,
        'suggestion' : suggestion,
        'can_phk'    : (3 in sp_aktif),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PHK — LIST
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def surat_phk_list(request):
    qs = get_employee_related_qs(SuratPHK, request).select_related('employee', 'perjanjian_bersama')
    q  = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(snap_nama__icontains=q)
    return render(request, 'industrial/surat_phk_list.html', {'surat_phk_list': qs, 'q': q})


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PHK — CREATE (dari PB final)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def surat_phk_create(request):
    company = _get_company(request)
    pb_id   = request.GET.get('pb') or request.POST.get('pb_id')
    pb      = get_object_or_404(PerjanjianBersama, pk=pb_id, **({'company': request.company} if request.company else {})) if pb_id else None

    # Cegah duplikat
    if pb and hasattr(pb, 'surat_phk'):
        messages.warning(request, 'Surat PHK untuk PB ini sudah ada.')
        return redirect('surat_phk_detail', pb.surat_phk.pk)

    if request.method == 'POST' and pb:
        try:
            surat = SuratPHK(
                company            = company or pb.company,
                employee           = pb.employee,
                perjanjian_bersama = pb,
            )
            surat.snapshot_dari_pb()

            # Override dari form
            surat.nomor_surat   = request.POST.get('nomor_surat', '').strip()
            surat.tanggal_surat = date.fromisoformat(request.POST.get('tanggal_surat'))
            surat.tempat_surat  = request.POST.get('tempat_surat', '').strip()
            surat.dasar_hukum   = request.POST.get('dasar_hukum', '').strip()
            surat.alasan_phk    = request.POST.get('alasan_phk', '').strip()
            surat.keterangan_kompensasi = request.POST.get('keterangan_kompensasi', '').strip()
            surat.catatan       = request.POST.get('catatan', '').strip()
            surat.nama_penandatangan    = request.POST.get('nama_penandatangan', '').strip()
            surat.jabatan_penandatangan = request.POST.get('jabatan_penandatangan', '').strip()
            surat.status        = request.POST.get('status', 'draft')

            if not surat.nomor_surat:
                surat.nomor_surat = surat.generate_nomor()

            surat.save()
            messages.success(request,
                f'Surat PHK untuk <strong>{surat.snap_nama}</strong> berhasil dibuat.')
            return redirect('surat_phk_detail', surat.pk)

        except Exception as e:
            import traceback; print(traceback.format_exc())
            messages.error(request, f'Gagal menyimpan: {e}')

    # PB list untuk step 1 (pilih PB)
    pb_list = None
    if not pb:
        pb_list = get_employee_related_qs(PerjanjianBersama, request).filter(
            status='final'
        ).select_related('employee').order_by('-tanggal_pb')
        # Exclude yang sudah punya surat PHK
        from django.db.models import Exists, OuterRef
        pb_list = pb_list.annotate(
            sudah_ada=Exists(SuratPHK.objects.filter(perjanjian_bersama=OuterRef('pk')))
        )

    return render(request, 'industrial/surat_phk_form.html', {
        'pb'      : pb,
        'pb_list' : pb_list,
        'company' : company,
        'today'   : date.today().isoformat(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PHK — DETAIL + PRINT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def surat_phk_detail(request, pk):
    surat = get_object_or_404(SuratPHK, pk=pk, **({'company': request.company} if request.company else {}))
    return render(request, 'industrial/surat_phk_detail.html', {'surat': surat})


@login_required
def surat_phk_print(request, pk):
    surat = get_object_or_404(SuratPHK, pk=pk, **({'company': request.company} if request.company else {}))
    return render(request, 'industrial/surat_phk_print.html', {'surat': surat})


# ══════════════════════════════════════════════════════════════════════════════
#  SKK — LIST
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def skk_list(request):
    qs = get_employee_related_qs(SuratKeteranganKerja, request).select_related('employee')
    q  = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(snap_nama__icontains=q)
    return render(request, 'industrial/skk_list.html', {'skk_list': qs, 'q': q})


# ══════════════════════════════════════════════════════════════════════════════
#  SKK — CREATE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def skk_create(request):
    company     = _get_company(request)
    employee_id = request.GET.get('employee') or request.POST.get('employee_id')
    employee    = get_object_or_404(Employee, pk=employee_id, **({'company': request.company} if request.company else {})) if employee_id else None

    if request.method == 'POST' and employee:
        try:
            tanggal_keluar_str = request.POST.get('tanggal_keluar', '').strip()
            tanggal_keluar     = date.fromisoformat(tanggal_keluar_str) if tanggal_keluar_str else None

            skk = SuratKeteranganKerja(
                company  = company or employee.company,
                employee = employee,
                snap_tanggal_keluar = tanggal_keluar,
            )
            skk.snapshot_dari_employee()

            skk.nomor_surat   = request.POST.get('nomor_surat', '').strip()
            skk.tanggal_surat = date.fromisoformat(request.POST.get('tanggal_surat'))
            skk.tujuan_surat  = request.POST.get('tujuan_surat', '').strip()
            skk.masa_kerja_keterangan = request.POST.get('masa_kerja_keterangan', '').strip() or skk.masa_kerja_keterangan
            skk.tampilkan_gaji = 'tampilkan_gaji' in request.POST
            skk.keterangan_tambahan    = request.POST.get('keterangan_tambahan', '').strip()
            skk.nama_penandatangan     = request.POST.get('nama_penandatangan', '').strip()
            skk.jabatan_penandatangan  = request.POST.get('jabatan_penandatangan', '').strip()

            if not skk.nomor_surat:
                skk.nomor_surat = skk.generate_nomor()

            skk.save()
            messages.success(request,
                f'SKK untuk <strong>{employee.nama}</strong> berhasil dibuat.')
            return redirect('skk_detail', skk.pk)

        except Exception as e:
            import traceback; print(traceback.format_exc())
            messages.error(request, f'Gagal menyimpan: {e}')

    return render(request, 'industrial/skk_form.html', {
        'employee'  : employee,
        'employees' : get_company_qs(Employee, request),
        'company'   : company,
        'today'     : date.today().isoformat(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  SKK — DETAIL + PRINT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def skk_detail(request, pk):
    skk = get_object_or_404(SuratKeteranganKerja, pk=pk, **({'company': request.company} if request.company else {}))
    return render(request, 'industrial/skk_detail.html', {'skk': skk})


@login_required
def skk_print(request, pk):
    skk = get_object_or_404(SuratKeteranganKerja, pk=pk, **({'company': request.company} if request.company else {}))
    return render(request, 'industrial/skk_print.html', {'skk': skk})
