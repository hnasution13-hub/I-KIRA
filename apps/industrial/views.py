import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import hr_required
from datetime import date

from .models import Violation, Severance, PerjanjianBersama
from apps.employees.models import Employee
from apps.core.utils import get_company_qs, get_employee_related_qs
from utils.pesangon_calculator import PesangonCalculator, MasaKerja, PASAL_CHOICES, PASAL_MAP

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# VIOLATION
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def violation_list(request):
    violations = get_employee_related_qs(Violation, request).select_related('employee').order_by('-tanggal_kejadian')
    employee_filter = request.GET.get('employee')
    status_filter   = request.GET.get('status')
    if employee_filter:
        violations = violations.filter(employee_id=employee_filter)
    if status_filter:
        violations = violations.filter(status=status_filter)
    return render(request, 'industrial/violation_list.html', {
        'violations': violations,
        'employees' : get_company_qs(Employee, request, status='Aktif'),
    })


@login_required
def violation_detail(request, pk):
    violation = get_object_or_404(Violation, pk=pk)
    return render(request, 'industrial/violation_detail.html', {'violation': violation})


@login_required
@hr_required
def violation_form(request, pk=None):
    instance = get_object_or_404(Violation, pk=pk) if pk else None

    if request.method == 'POST':
        employee = get_object_or_404(Employee, pk=request.POST.get('employee'))
        data = {
            'employee'         : employee,
            'tipe_pelanggaran' : request.POST.get('tipe_pelanggaran'),
            'tanggal_kejadian' : request.POST.get('tanggal_kejadian'),
            'deskripsi'        : request.POST.get('deskripsi'),
            'tingkat'          : request.POST.get('tingkat'),
            'poin'             : int(request.POST.get('poin', 0)),
            'sanksi'           : request.POST.get('sanksi', ''),
            'status'           : request.POST.get('status', 'Pending'),
        }
        if 'dokumen' in request.FILES:
            data['dokumen'] = request.FILES['dokumen']

        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, 'Data pelanggaran berhasil diperbarui.')
        else:
            data['company'] = request.company or employee.company
            Violation.objects.create(**data)
            messages.success(request, 'Data pelanggaran berhasil disimpan.')
        return redirect('violation_list')

    return render(request, 'industrial/violation_form.html', {
        'instance' : instance,
        'employees': get_company_qs(Employee, request, status='Aktif'),
    })


# ─────────────────────────────────────────────────────────────────────────────
# SEVERANCE / PESANGON
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def severance_list(request):
    severances = get_employee_related_qs(
        Severance, request
    ).select_related('employee', 'employee__company').order_by('-tanggal_phk')
    return render(request, 'industrial/severance_list.html', {'severances': severances})


@login_required
@hr_required
def severance_calculator(request):
    result   = None
    employee = None
    pasal_choices_grouped = _get_pasal_grouped()

    if request.method == 'POST':
        emp_id = request.POST.get('employee')
        if not emp_id:
            messages.error(request, 'Pilih karyawan terlebih dahulu.')
            return redirect('severance_calculator')

        employee    = get_object_or_404(Employee, pk=emp_id)
        tanggal_phk = request.POST.get('tanggal_phk', '').strip()
        alasan_phk  = request.POST.get('alasan_phk', 'PHK Perusahaan')
        dasar_pasal = request.POST.get('dasar_pasal', '').strip()

        # Tombol mana yang diklik
        action = 'save' if 'save' in request.POST else 'calculate'

        # ── Validasi minimal untuk calculate/save ─────────────────────────
        # Jika hanya pilih karyawan (onchange submit), jangan hitung
        if not tanggal_phk and not dasar_pasal:
            return render(request, 'industrial/severance_calculator.html', {
                'employees'            : get_company_qs(Employee, request),
                'employee'             : employee,
                'result'               : None,
                'alasan_choices'       : Severance.ALASAN_PHK_CHOICES,
                'pasal_choices'        : PASAL_CHOICES,
                'pasal_choices_grouped': pasal_choices_grouped,
            })

        # ── Ambil gaji dari form input (prioritas utama) ───────────────────
        try:
            gaji_pokok = int(request.POST.get('gaji_pokok', '0').strip() or 0)
        except (ValueError, TypeError):
            gaji_pokok = 0

        try:
            tunjangan_tetap = int(request.POST.get('tunjangan_tetap', '0').strip() or 0)
        except (ValueError, TypeError):
            tunjangan_tetap = 0

        # Fallback ke salary_benefit hanya jika form kosong / 0
        if gaji_pokok == 0:
            try:
                gaji_pokok = int(employee.salary_benefit.gaji_pokok or 0)
            except Exception:
                pass

        if tunjangan_tetap == 0:
            try:
                tunjangan_tetap = int(employee.salary_benefit.total_tunjangan_tetap or 0)
            except Exception:
                pass

        try:
            tgl_phk_parsed = date.fromisoformat(tanggal_phk) if tanggal_phk else date.today()
        except ValueError:
            tgl_phk_parsed = date.today()

        # ── Hitung (selalu, baik calculate maupun save) ────────────────────
        result = PesangonCalculator.hitung(
            gaji_pokok      = gaji_pokok,
            tunjangan_tetap = tunjangan_tetap,
            join_date       = employee.join_date,
            tanggal_phk     = tgl_phk_parsed,
            alasan_phk      = alasan_phk,
            dasar_pasal     = dasar_pasal,
            status_karyawan = employee.status_karyawan,
        )
        # Simpan input ke result agar form bisa persist
        result['gaji_pokok']      = gaji_pokok
        result['tunjangan_tetap'] = tunjangan_tetap
        result['tanggal_phk']     = str(tgl_phk_parsed)
        result['alasan_phk']      = alasan_phk

        # ── Simpan jika tombol "Hitung & Simpan" yang diklik ───────────────
        if action == 'save':
            try:
                company   = request.company or employee.company
                severance = Severance(
                    company          = company,
                    employee         = employee,
                    tanggal_phk      = tgl_phk_parsed,
                    alasan_phk       = alasan_phk,
                    dasar_pasal      = dasar_pasal,
                    gaji_pokok       = gaji_pokok,
                    tunjangan_tetap  = tunjangan_tetap,
                    masa_kerja_tahun = result['masa_kerja_tahun'],
                    masa_kerja_bulan = result['masa_kerja_bulan'],
                    total_upah       = result['total_upah'],
                    pengali_pesangon = result['pengali_pesangon'],
                    pesangon         = result['pesangon'],
                    upmk             = result['upmk'],
                    uang_pisah       = result['uang_pisah'],
                    kompensasi_pkwt  = result['kompensasi_pkwt'],
                    total_pesangon   = result['total'],
                    keterangan       = request.POST.get('keterangan', ''),
                )
                severance.save()
                messages.success(
                    request,
                    f'Pesangon <strong>{employee.nama}</strong> berhasil disimpan.'
                )
                return redirect('severance_list')
            except Exception as e:
                import traceback
                err_detail = traceback.format_exc()
                print('=== SEVERANCE SAVE ERROR ===')
                print(err_detail)
                print('============================')
                logger.exception('Error saving severance')
                messages.error(request, f'Gagal menyimpan: {e}')

    return render(request, 'industrial/severance_calculator.html', {
        'employees'            : get_company_qs(Employee, request),
        'employee'             : employee,
        'result'               : result,
        'alasan_choices'       : Severance.ALASAN_PHK_CHOICES,
        'pasal_choices'        : PASAL_CHOICES,
        'pasal_choices_grouped': pasal_choices_grouped,
    })


@login_required
def severance_detail(request, pk):
    severance = get_object_or_404(Severance, pk=pk)
    return render(request, 'industrial/severance_detail.html', {'severance': severance})


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _get_pasal_grouped():
    pkwt  = [(k, v['label']) for k, v in PASAL_MAP.items() if k == '61A']
    phk   = [(k, v['label']) for k, v in PASAL_MAP.items() if k != '61A' and not v['pakai_uang_pisah']]
    pisah = [(k, v['label']) for k, v in PASAL_MAP.items() if v['pakai_uang_pisah']]
    return {'pkwt': pkwt, 'phk': phk, 'uang_pisah': pisah}


# ─────────────────────────────────────────────────────────────────────────────
# PERJANJIAN BERSAMA
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def pb_list(request):
    pbs = get_employee_related_qs(
        PerjanjianBersama, request
    ).select_related('employee', 'company', 'severance').order_by('-tanggal_pb')
    return render(request, 'industrial/pb_list.html', {'pbs': pbs})


@login_required
@hr_required
def pb_create(request):
    """
    Step 1: tampilkan daftar Severance → pilih satu → redirect ke step 2
    Step 2: isi komponen PB → simpan
    """
    # Ambil severance dari query param (step 1 → step 2)
    severance_id = request.GET.get('severance') or request.POST.get('severance_id')
    severance    = None

    if severance_id:
        severance = get_object_or_404(Severance, pk=severance_id)

    # ── STEP 2: Form komponen ──────────────────────────────────────────────
    if request.method == 'POST' and severance and 'step' in request.POST:
        try:
            emp     = severance.employee
            company = request.company or emp.company

            # Snapshot karyawan
            jabatan    = str(emp.jabatan)    if emp.jabatan    else ''
            departemen = str(emp.department) if emp.department else ''
            alamat_parts = [emp.alamat]
            if emp.rt and emp.rw:
                alamat_parts.append(f'RT/RW {emp.rt}/{emp.rw}')
            if emp.kelurahan:
                alamat_parts.append(f'Kel. {emp.kelurahan}')
            if emp.kecamatan:
                alamat_parts.append(f'Kec. {emp.kecamatan}')
            if emp.kabupaten:
                alamat_parts.append(str(emp.kabupaten))
            if emp.provinsi:
                alamat_parts.append(str(emp.provinsi))
            alamat_snap = ', '.join(filter(None, alamat_parts))

            gaji_pokok = int(severance.gaji_pokok or 0)

            # Hitung nilai komponen
            sisa_cuti_tahunan = int(request.POST.get('sisa_cuti_tahunan', 0) or 0)
            nilai_cuti_tahunan = round((gaji_pokok / 26) * sisa_cuti_tahunan)

            pakai_cuti_roster = 'pakai_cuti_roster' in request.POST
            sisa_cuti_roster  = int(request.POST.get('sisa_cuti_roster', 0) or 0)
            nilai_cuti_roster = round((gaji_pokok / 30) * sisa_cuti_roster) if pakai_cuti_roster else 0

            sisa_hari_kerja = int(request.POST.get('sisa_hari_kerja', 0) or 0)
            nilai_sisa_gaji = round((gaji_pokok / 26) * sisa_hari_kerja)

            pakai_uang_transport = 'pakai_uang_transport' in request.POST
            nilai_uang_transport = int(request.POST.get('nilai_uang_transport', 0) or 0) if pakai_uang_transport else 0

            tanggal_cut_off_str = request.POST.get('tanggal_cut_off', '').strip()
            from datetime import date as _date
            try:
                tanggal_cut_off = _date.fromisoformat(tanggal_cut_off_str) if tanggal_cut_off_str else None
            except ValueError:
                tanggal_cut_off = None

            action = request.POST.get('action', 'draft')

            # Ambil dari pasal label
            from utils.pesangon_calculator import PASAL_MAP
            pasal_info = PASAL_MAP.get(severance.dasar_pasal)
            dasar_pasal_label = pasal_info['label'] if pasal_info else severance.dasar_pasal

            pb = PerjanjianBersama(
                company   = company,
                employee  = emp,
                severance = severance,
                nomor_pb  = request.POST.get('nomor_pb', '').strip(),
                tanggal_pb = request.POST.get('tanggal_pb'),
                tempat_pb  = request.POST.get('tempat_pb', '').strip(),
                dasar_pasal = severance.dasar_pasal,
                tanggal_phk = severance.tanggal_phk,
                alasan_phk  = severance.alasan_phk,
                status      = 'final' if action == 'final' else 'draft',

                snap_nama           = emp.nama,
                snap_nik            = emp.nik,
                snap_jabatan        = jabatan,
                snap_departemen     = departemen,
                snap_tanggal_masuk  = emp.join_date,
                snap_alamat         = alamat_snap,
                snap_gaji_pokok     = gaji_pokok,
                snap_status_karyawan = emp.status_karyawan,

                nama_penandatangan    = request.POST.get('nama_penandatangan', '').strip(),
                jabatan_penandatangan = request.POST.get('jabatan_penandatangan', '').strip(),

                total_pesangon  = severance.total_pesangon,
                upmk            = severance.upmk,

                sisa_cuti_tahunan  = sisa_cuti_tahunan,
                nilai_cuti_tahunan = nilai_cuti_tahunan,

                pakai_cuti_roster  = pakai_cuti_roster,
                sisa_cuti_roster   = sisa_cuti_roster,
                nilai_cuti_roster  = nilai_cuti_roster,

                tanggal_cut_off = tanggal_cut_off,
                sisa_hari_kerja = sisa_hari_kerja,
                nilai_sisa_gaji = nilai_sisa_gaji,

                pakai_uang_transport = pakai_uang_transport,
                nilai_uang_transport = nilai_uang_transport,

                jadwal_pembayaran = request.POST.get('jadwal_pembayaran', '').strip(),
                catatan           = request.POST.get('catatan', '').strip(),
            )
            pb.hitung_grand_total()
            pb.save()
            messages.success(request,
                f'Perjanjian Bersama <strong>{emp.nama}</strong> berhasil disimpan.')
            return redirect('pb_detail', pb.pk)

        except Exception as e:
            import traceback
            print('=== PB SAVE ERROR ===')
            print(traceback.format_exc())
            print('=====================')
            messages.error(request, f'Gagal menyimpan: {e}')

    # ── STEP 1: Daftar Severance ───────────────────────────────────────────
    if not severance:
        q = request.GET.get('q', '').strip()
        severances = get_employee_related_qs(
            Severance, request
        ).select_related('employee').order_by('-tanggal_phk')
        if q:
            severances = severances.filter(employee__nama__icontains=q)

        return render(request, 'industrial/pb_form.html', {
            'step'      : 1,
            'severances': severances,
            'company'   : request.company,
        })

    # Step 2 (GET — tampilkan form)
    from datetime import date as _date
    return render(request, 'industrial/pb_form.html', {
        'step'     : 2,
        'severance': severance,
        'pb'       : None,
        'company'  : request.company or severance.employee.company,
        'today'    : _date.today().isoformat(),
    })


@login_required
@hr_required
def pb_edit(request, pk):
    pb        = get_object_or_404(PerjanjianBersama, pk=pk)
    severance = pb.severance

    if request.method == 'POST':
        try:
            gaji_pokok = int(pb.snap_gaji_pokok or 0)

            sisa_cuti_tahunan = int(request.POST.get('sisa_cuti_tahunan', 0) or 0)
            nilai_cuti_tahunan = round((gaji_pokok / 26) * sisa_cuti_tahunan)

            pakai_cuti_roster = 'pakai_cuti_roster' in request.POST
            sisa_cuti_roster  = int(request.POST.get('sisa_cuti_roster', 0) or 0)
            nilai_cuti_roster = round((gaji_pokok / 30) * sisa_cuti_roster) if pakai_cuti_roster else 0

            sisa_hari_kerja = int(request.POST.get('sisa_hari_kerja', 0) or 0)
            nilai_sisa_gaji = round((gaji_pokok / 26) * sisa_hari_kerja)

            pakai_uang_transport = 'pakai_uang_transport' in request.POST
            nilai_uang_transport = int(request.POST.get('nilai_uang_transport', 0) or 0) if pakai_uang_transport else 0

            tanggal_cut_off_str = request.POST.get('tanggal_cut_off', '').strip()
            from datetime import date as _date
            try:
                pb.tanggal_cut_off = _date.fromisoformat(tanggal_cut_off_str) if tanggal_cut_off_str else None
            except ValueError:
                pb.tanggal_cut_off = None

            pb.nomor_pb               = request.POST.get('nomor_pb', '').strip()
            pb.tanggal_pb             = request.POST.get('tanggal_pb')
            pb.tempat_pb              = request.POST.get('tempat_pb', '').strip()
            pb.nama_penandatangan     = request.POST.get('nama_penandatangan', '').strip()
            pb.jabatan_penandatangan  = request.POST.get('jabatan_penandatangan', '').strip()
            pb.sisa_cuti_tahunan      = sisa_cuti_tahunan
            pb.nilai_cuti_tahunan     = nilai_cuti_tahunan
            pb.pakai_cuti_roster      = pakai_cuti_roster
            pb.sisa_cuti_roster       = sisa_cuti_roster
            pb.nilai_cuti_roster      = nilai_cuti_roster
            pb.sisa_hari_kerja        = sisa_hari_kerja
            pb.nilai_sisa_gaji        = nilai_sisa_gaji
            pb.pakai_uang_transport   = pakai_uang_transport
            pb.nilai_uang_transport   = nilai_uang_transport
            pb.jadwal_pembayaran      = request.POST.get('jadwal_pembayaran', '').strip()
            pb.catatan                = request.POST.get('catatan', '').strip()
            pb.status = 'final' if request.POST.get('action') == 'final' else 'draft'
            pb.hitung_grand_total()
            pb.save()
            messages.success(request, 'Perjanjian Bersama berhasil diperbarui.')
            return redirect('pb_detail', pb.pk)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'Gagal menyimpan: {e}')

    from datetime import date as _date
    return render(request, 'industrial/pb_form.html', {
        'step'     : 2,
        'severance': severance,
        'pb'       : pb,
        'company'  : request.company or pb.company,
        'today'    : _date.today().isoformat(),
    })


@login_required
def pb_detail(request, pk):
    pb = get_object_or_404(
        PerjanjianBersama.objects.select_related(
            'employee', 'company', 'severance'
        ), pk=pk
    )
    return render(request, 'industrial/pb_detail.html', {'pb': pb})


@login_required
def pb_print(request, pk):
    from utils.pesangon_calculator import PASAL_MAP
    pb = get_object_or_404(
        PerjanjianBersama.objects.select_related(
            'employee', 'company', 'severance'
        ), pk=pk
    )
    pasal_info = PASAL_MAP.get(pb.dasar_pasal)
    pb.dasar_pasal_label = pasal_info['label'] if pasal_info else pb.dasar_pasal
    return render(request, 'industrial/pb_print.html', {'pb': pb})
