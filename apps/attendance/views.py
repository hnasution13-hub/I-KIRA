from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction  # FIX BUG-003: gunakan atomic transaction
from django.views.decorators.http import require_POST  # FIX BUG-004
from django.utils import timezone
from django.db.models import Sum
from .models import Attendance, Leave
from .forms import LeaveForm, OvertimeForm  # FIX BUG-011: gunakan form untuk validasi
from apps.employees.models import Employee
from utils.email_sender import send_leave_notification
from apps.core.utils import get_company_qs, get_employee_related_qs
from apps.core.decorators import hr_required, manager_required
from datetime import date, datetime, time


@login_required
def attendance_list(request):
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    company     = getattr(request, 'company', None)
    base_qs     = get_employee_related_qs(Attendance, request)
    attendances = base_qs.filter(
        tanggal__month=month, tanggal__year=year
    ).select_related('employee').order_by('-tanggal', 'employee__nama')
    return render(request, 'attendance/attendance_list.html', {
        'attendances': attendances, 'month': month, 'year': year
    })


@login_required
def check_in(request):
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        now = datetime.now()
        # FIX BUG-003: Gunakan select_for_update() + atomic transaction
        # untuk mencegah race condition saat dua request bersamaan
        with transaction.atomic():
            att, created = Attendance.objects.select_for_update().get_or_create(
                employee=emp, tanggal=date.today(),
                defaults={'check_in': now.time(), 'status': 'Hadir'}
            )
            if not created:
                if not att.check_out:
                    # FIX BUG-003: Validasi check_out > check_in
                    if att.check_in and now.time() <= att.check_in:
                        messages.error(
                            request,
                            f'Jam check-out ({now.strftime("%H:%M")}) tidak boleh '
                            f'lebih awal dari jam check-in ({att.check_in.strftime("%H:%M")}).'
                        )
                    else:
                        att.check_out = now.time()
                        att.save()
                        messages.success(request, f'Check-out {emp.nama} berhasil.')
                else:
                    messages.info(request, f'{emp.nama} sudah check-in dan check-out hari ini.')
            else:
                messages.success(request, f'Check-in {emp.nama} berhasil.')
        return redirect('attendance_list')
    return render(request, 'attendance/check_in.html', {
        'employees': get_company_qs(Employee, request, status='Aktif')
    })


@login_required
def leave_list(request):
    leaves = get_employee_related_qs(Leave, request).select_related('employee').order_by('-created_at')
    return render(request, 'attendance/leave_list.html', {'leaves': leaves})


@login_required
@hr_required
def leave_form(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save()
            send_leave_notification(leave, action='submitted')
            messages.success(request, 'Pengajuan cuti berhasil dikirim.')
            return redirect('leave_list')
        else:
            messages.error(request, 'Data tidak valid. Periksa kembali formulir.')
    else:
        form = LeaveForm()
    return render(request, 'attendance/leave_form.html', {'form': form})


@login_required
@require_POST
@manager_required
def leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if leave.status != 'Pending':
        messages.warning(request, 'Cuti ini sudah diproses sebelumnya.')
        return redirect('leave_list')

    from utils.approval_engine import ApprovalEngine
    engine = ApprovalEngine(
        company=leave.employee.company,
        modul='leave',
        jabatan_pemohon=leave.employee.jabatan,
    )
    if not engine.can_approve(request.user):
        messages.error(request, 'Anda tidak berwenang menyetujui cuti ini.')
        return redirect('leave_list')

    catatan = request.POST.get('catatan_approval', '')
    engine.approve(leave, request.user, catatan=catatan)
    send_leave_notification(leave, action='approved')
    messages.success(request, f'Cuti {leave.employee.nama} disetujui.')
    return redirect('leave_list')


@login_required
@require_POST
@manager_required
def leave_reject(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if leave.status != 'Pending':
        messages.warning(request, 'Cuti ini sudah diproses sebelumnya.')
        return redirect('leave_list')

    from utils.approval_engine import ApprovalEngine
    engine = ApprovalEngine(
        company=leave.employee.company,
        modul='leave',
        jabatan_pemohon=leave.employee.jabatan,
    )
    if not engine.can_approve(request.user):
        messages.error(request, 'Anda tidak berwenang menolak cuti ini.')
        return redirect('leave_list')

    catatan = request.POST.get('catatan_approval', '')
    engine.reject(leave, request.user, catatan=catatan)
    send_leave_notification(leave, action='rejected')
    messages.warning(request, f'Cuti {leave.employee.nama} ditolak.')



@login_required
def leave_detail(request, pk):
    """Detail cuti + approval chain karyawan tersebut."""
    leave = get_object_or_404(Leave, pk=pk)
    from utils.approval_engine import get_approval_chain_display, ApprovalEngine
    approval_chain = get_approval_chain_display(leave.employee, 'leave')
    engine = ApprovalEngine(
        company=leave.employee.company,
        modul='leave',
        jabatan_pemohon=leave.employee.jabatan,
    )
    can_approve = engine.can_approve(request.user)
    return render(request, 'attendance/leave_detail.html', {
        'leave':          leave,
        'approval_chain': approval_chain,
        'can_approve':    can_approve,
    })


@login_required
@require_POST
def overtime_approve(request, pk):
    """Approve lembur via ApprovalEngine."""
    att = get_object_or_404(Attendance, pk=pk)
    from utils.approval_engine import ApprovalEngine
    engine = ApprovalEngine(
        company=att.employee.company,
        modul='overtime',
        jabatan_pemohon=att.employee.jabatan,
    )
    if not engine.can_approve(request.user):
        messages.error(request, 'Anda tidak berwenang menyetujui lembur ini.')
        return redirect('overtime_list')
    engine._log(att, request.user, 'APPROVE', f'Lembur {att.tanggal} disetujui')
    att.keterangan = f'[APPROVED] {request.POST.get("catatan", "")}'.strip()
    att.save(update_fields=['keterangan'])
    messages.success(request, f'Lembur {att.employee.nama} ({att.tanggal}) disetujui.')
    return redirect('overtime_list')


@login_required
@require_POST
def overtime_reject(request, pk):
    """Reject lembur via ApprovalEngine."""
    att = get_object_or_404(Attendance, pk=pk)
    from utils.approval_engine import ApprovalEngine
    engine = ApprovalEngine(
        company=att.employee.company,
        modul='overtime',
        jabatan_pemohon=att.employee.jabatan,
    )
    if not engine.can_approve(request.user):
        messages.error(request, 'Anda tidak berwenang menolak lembur ini.')
        return redirect('overtime_list')
    engine._log(att, request.user, 'REJECT', f'Lembur {att.tanggal} ditolak')
    att.keterangan = f'[REJECTED] {request.POST.get("catatan", "")}'.strip()
    att.lembur_jam  = 0
    att.lembur_upah = 0
    att.save(update_fields=['keterangan', 'lembur_jam', 'lembur_upah'])
    messages.warning(request, f'Lembur {att.employee.nama} ({att.tanggal}) ditolak.')
    return redirect('overtime_list')

@login_required
def attendance_report(request):
    # Terima parameter bulan/tahun (baru) ATAU month/year (lama) untuk kompatibilitas
    bulan = int(request.GET.get('bulan', request.GET.get('month', 0)))
    tahun = int(request.GET.get('tahun', request.GET.get('year', date.today().year)))
    dept_filter = request.GET.get('department', '')
    employee_id = request.GET.get('employee', '')

    bulan_choices = [
        (1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
        (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
        (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember'),
    ]

    company = getattr(request, 'company', None)
    from apps.core.models import Department
    departments = Department.objects.filter(**(({'company': company}) if company else {})).order_by('nama')

    attendances = None
    summary = None

    if bulan:
        base_att = get_employee_related_qs(Attendance, request)
        attendances = base_att.filter(
            tanggal__month=bulan, tanggal__year=tahun
        ).select_related('employee', 'employee__department').order_by('employee__nama', 'tanggal')

        if dept_filter:
            attendances = attendances.filter(employee__department_id=dept_filter)
        if employee_id:
            attendances = attendances.filter(employee_id=employee_id)

        total_karyawan = attendances.values('employee').distinct().count()
        total_hadir    = attendances.filter(status='Hadir').count()
        total_alpha    = attendances.filter(status='Tidak Hadir').count()
        total_sakit    = attendances.filter(status='Sakit').count()
        total_izin     = attendances.filter(status__in=['Izin', 'Cuti']).count()
        total_telat    = attendances.aggregate(t=Sum('keterlambatan'))['t'] or 0
        total_lembur   = attendances.aggregate(j=Sum('lembur_jam'))['j'] or 0
        rata_hadir     = round(total_hadir / total_karyawan, 1) if total_karyawan else 0

        summary = {
            'total_karyawan': total_karyawan,
            'total_hadir':    total_hadir,
            'total_alpha':    total_alpha,
            'total_sakit':    total_sakit,
            'total_izin':     total_izin,
            'total_telat':    total_telat,
            'total_lembur':   float(total_lembur),
            'rata_hadir':     rata_hadir,
        }

    # Build report_data per karyawan (digroup)
    report_data = []
    if attendances is not None:
        from utils.payroll_calculator import PayrollCalculator
        from datetime import date as _date
        import calendar as _cal
        emp_atts = {}
        for a in attendances:
            emp_atts.setdefault(a.employee_id, {'employee': a.employee, 'records': []})
            emp_atts[a.employee_id]['records'].append(a)

        for eid, data in emp_atts.items():
            recs = data['records']
            hk = PayrollCalculator.hitung_hari_kerja(
                _date(tahun, bulan, 1),
                _date(tahun, bulan, _cal.monthrange(tahun, bulan)[1]),
                holiday_dates=[],
            )
            report_data.append({
                'employee':    data['employee'],
                'hari_kerja':  hk,
                'hari_hadir':  sum(1 for r in recs if r.status == 'Hadir'),
                'hari_absen':  sum(1 for r in recs if r.status == 'Tidak Hadir'),
                'hari_sakit':  sum(1 for r in recs if r.status == 'Sakit'),
                'hari_izin':   sum(1 for r in recs if r.status in ['Izin','Cuti']),
                'hari_wfh':    sum(1 for r in recs if r.status == 'WFH'),
                'total_telat': sum(r.keterlambatan or 0 for r in recs if r.status == 'Hadir'),
                'total_lembur': sum(float(r.lembur_jam or 0) for r in recs if r.status == 'Hadir'),
            })
        report_data.sort(key=lambda x: x['employee'].nama)

    return render(request, 'attendance/attendance_report.html', {
        'attendances':       attendances,
        'report_data':       report_data,
        'summary':           summary,
        'employees':         get_company_qs(Employee, request, status='Aktif').order_by('nama'),
        'departments':       departments,
        'bulan_choices':     bulan_choices,
        'bulan':             bulan,
        'tahun':             tahun,
        'dept_filter':       dept_filter,
        'selected_employee': employee_id,
        'month':             bulan,
        'year':              tahun,
    })


@login_required
def attendance_calendar(request):
    # FIX BUG-012: Sediakan data untuk kalender
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    employee_id = request.GET.get('employee')

    attendances = get_employee_related_qs(Attendance, request).filter(
        tanggal__month=month, tanggal__year=year
    ).select_related('employee')

    if employee_id:
        attendances = attendances.filter(employee_id=employee_id)

    # Format data untuk kalender (tanggal -> status)
    calendar_data = {
        a.tanggal.isoformat(): a.status for a in attendances
    }

    return render(request, 'attendance/calendar.html', {
        'calendar_data': calendar_data,
        'employees': get_company_qs(Employee, request, status='Aktif'),
        'month': month,
        'year': year,
        'selected_employee': employee_id,
    })


# ── FIX P1: Overtime views ──────────────────────────────────────────────────

@login_required
def overtime_list(request):
    month = int(request.GET.get('bulan', date.today().month))
    year = int(request.GET.get('tahun', date.today().year))
    employee_id = request.GET.get('employee')

    overtimes = get_employee_related_qs(Attendance, request).filter(
        tanggal__month=month,
        tanggal__year=year,
        lembur_jam__gt=0,
    ).select_related('employee').order_by('-tanggal')

    if employee_id:
        overtimes = overtimes.filter(employee_id=employee_id)

    totals = overtimes.aggregate(
        total_jam=Sum('lembur_jam'),
        total_upah=Sum('lembur_upah'),
    )

    bulan_choices = [
        (1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
        (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
        (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember'),
    ]
    tahun_choices = list(range(2020, date.today().year + 2))

    return render(request, 'attendance/overtime_list.html', {
        'overtimes': overtimes,
        'employees': get_company_qs(Employee, request, status='Aktif').order_by('nama'),
        'bulan_choices': bulan_choices,
        'tahun_choices': tahun_choices,
        'month': month,
        'year': year,
        'total_records': overtimes.count(),
        'total_jam_lembur': round(float(totals['total_jam'] or 0), 1),
        'total_upah_lembur': int(totals['total_upah'] or 0),
    })


@login_required
@hr_required
def overtime_recalculate(request):
    """Recalculate ulang lembur_upah untuk semua data lembur — bulk update, 1 query."""
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])

    qs = get_employee_related_qs(Attendance, request).filter(
        lembur_jam__gt=0
    ).select_related('employee__salary_benefit')

    to_update = []
    skipped   = 0

    for att in qs:
        try:
            sb = att.employee.salary_benefit
            if sb.status_gaji == 'all_in':
                skipped += 1
                continue
            tarif     = sb.lembur_tarif_per_jam if sb.lembur_tarif_per_jam else sb.upah_per_jam
            upah_baru = int(float(tarif) * float(att.lembur_jam))
            att.lembur_upah = upah_baru
            to_update.append(att)
        except Exception:
            skipped += 1

    # Bulk update — 1 query untuk semua record sekaligus
    if to_update:
        Attendance.objects.bulk_update(to_update, ['lembur_upah'], batch_size=500)

    messages.success(request,
        f'Recalculate selesai: {len(to_update)} data diupdate, {skipped} dilewati (all-in / tidak ada salary).')
    return redirect('overtime_list')


@login_required
@hr_required
def overtime_form(request, pk=None):
    """Input / edit lembur manual pada data absensi."""
    instance = get_object_or_404(Attendance, pk=pk) if pk else None

    if request.method == 'POST':
        form = OvertimeForm(request.POST)
        if form.is_valid():
            emp = form.cleaned_data['employee']
            tgl = form.cleaned_data['tanggal']
            jam = form.cleaned_data['jam_lembur']
            ket = form.cleaned_data['keterangan']

            # Hitung upah lembur: pakai tarif override jika diisi, fallback ke gaji_pokok/173
            upah = 0
            try:
                sb = emp.salary_benefit
                # status all_in → lembur tidak dibayar terpisah
                if sb.status_gaji == 'all_in':
                    upah = 0
                else:
                    tarif = sb.lembur_tarif_per_jam if sb.lembur_tarif_per_jam else sb.upah_per_jam
                    upah = int(float(tarif) * float(jam))
            except Exception:
                pass

            att, created = Attendance.objects.get_or_create(
                employee=emp,
                tanggal=tgl,
                defaults={'status': 'Hadir'},
            )
            att.lembur_jam = jam
            att.lembur_upah = upah
            att.keterangan = ket
            att.save()

            messages.success(request, f'Data lembur {emp.nama} berhasil disimpan.')
            return redirect('overtime_list')
    else:
        initial = {}
        if instance:
            initial = {
                'employee': instance.employee,
                'tanggal': instance.tanggal,
                'jam_lembur': instance.lembur_jam,
                'keterangan': instance.keterangan,
            }
        form = OvertimeForm(initial=initial)

    return render(request, 'attendance/overtime_form.html', {
        'form': form,
        'instance': instance,
    })


@login_required
@hr_required
def attendance_bulk(request):
    """Input absensi massal — HR input 1 hari untuk semua karyawan sekaligus."""
    from apps.attendance.models import Holiday
    company   = getattr(request, 'company', None)
    employees = get_company_qs(Employee, request, status='Aktif').order_by('nama')
    today = date.today()

    if request.method == 'POST':
        tanggal_str = request.POST.get('tanggal', '')
        try:
            tgl = date.fromisoformat(tanggal_str)
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid.')
            return redirect('attendance_bulk')

        saved = 0
        for emp in employees:
            key = f'status_{emp.pk}'
            status = request.POST.get(key, '')
            if not status:
                continue  # skip karyawan yang tidak diisi

            check_in_str  = request.POST.get(f'check_in_{emp.pk}', '').strip()
            check_out_str = request.POST.get(f'check_out_{emp.pk}', '').strip()
            keterangan    = request.POST.get(f'ket_{emp.pk}', '').strip()

            def parse_time(s):
                if not s:
                    return None
                try:
                    return datetime.strptime(s, '%H:%M').time()
                except ValueError:
                    return None

            ci = parse_time(check_in_str)
            co = parse_time(check_out_str)

            # Hitung keterlambatan
            telat = 0
            if ci:
                normal = time(8, 0)
                if ci > normal:
                    delta = datetime.combine(tgl, ci) - datetime.combine(tgl, normal)
                    telat = int(delta.total_seconds() // 60)

            # Hitung lembur
            lembur = 0
            if ci and co and co > ci:
                from decimal import Decimal
                total_jam = (datetime.combine(tgl, co) - datetime.combine(tgl, ci)).total_seconds() / 3600
                lembur = max(0, round(total_jam - 1 - 8, 1))

            Attendance.objects.update_or_create(
                employee=emp, tanggal=tgl,
                defaults={
                    'status': status,
                    'check_in': ci,
                    'check_out': co,
                    'keterlambatan': telat,
                    'lembur_jam': lembur,
                    'keterangan': keterangan,
                }
            )
            saved += 1

        messages.success(request, f'{saved} data absensi tanggal {tgl.strftime("%d/%m/%Y")} berhasil disimpan.')
        return redirect('attendance_list')

    # Pre-load data existing untuk tanggal tertentu (jika ada query param)
    tanggal_param = request.GET.get('tanggal', today.isoformat())
    try:
        tgl_view = date.fromisoformat(tanggal_param)
    except ValueError:
        tgl_view = today

    existing = {
        a.employee_id: a
        for a in Attendance.objects.filter(tanggal=tgl_view, employee__company=company)
    } if company else {
        a.employee_id: a
        for a in Attendance.objects.filter(tanggal=tgl_view)
    }

    is_holiday = Holiday.objects.filter(tanggal=tgl_view, company=company).exists() if company else Holiday.objects.filter(tanggal=tgl_view).exists()
    is_weekend  = tgl_view.weekday() >= 5  # Sabtu=5, Minggu=6

    STATUS_CHOICES = ['Hadir', 'Tidak Hadir', 'Izin', 'Sakit', 'Cuti', 'WFH', 'Libur']

    return render(request, 'attendance/attendance_bulk.html', {
        'employees':     employees,
        'tanggal':       tgl_view,
        'existing':      existing,
        'is_holiday':    is_holiday,
        'is_weekend':    is_weekend,
        'status_choices': STATUS_CHOICES,
        'today':         today,
    })
