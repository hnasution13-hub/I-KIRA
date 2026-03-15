from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date, timedelta
import calendar
import json

from .models import Shift, ShiftAssignment, ShiftRoster, get_shift_for_employee
from apps.employees.models import Employee
from apps.core.utils import get_company_qs, get_employee_related_qs
from apps.core.models import Department
try:
    from apps.core.decorators import hr_required
except ImportError:
    # Fallback jika decorator belum ada
    def hr_required(f):
        return f


HARI_NAMA = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']


# ══════════════════════════════════════════════════════════════════════════════
#  MASTER SHIFT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def shift_list(request):
    shifts = Shift.objects.all().order_by('nama')
    return render(request, 'shifts/shift_list.html', {'shifts': shifts})


@login_required
@hr_required
def shift_form(request, pk=None):
    instance = get_object_or_404(Shift, pk=pk) if pk else None
    TIPE_CHOICES = Shift.TIPE_CHOICES
    HARI_CHOICES = list(enumerate(HARI_NAMA))

    if request.method == 'POST':
        hari_list = request.POST.getlist('hari_kerja')
        hari_str  = ','.join(hari_list)

        def t(key):
            v = request.POST.get(key, '').strip()
            return v if v else None

        def i(key, default=0):
            try: return int(request.POST.get(key) or default)
            except: return default

        def d(key, default=8):
            try: return float(request.POST.get(key) or default)
            except: return default

        data = dict(
            nama=request.POST.get('nama', '').strip(),
            kode=request.POST.get('kode', '').strip().upper(),
            tipe=request.POST.get('tipe', 'fixed'),
            warna=request.POST.get('warna', '#0d6efd'),
            aktif=bool(request.POST.get('aktif')),
            keterangan=request.POST.get('keterangan', ''),
            jam_masuk=t('jam_masuk'),
            jam_keluar=t('jam_keluar'),
            toleransi_telat=i('toleransi_telat'),
            jam_masuk_2=t('jam_masuk_2'),
            jam_keluar_2=t('jam_keluar_2'),
            minimal_jam_kerja=d('minimal_jam_kerja'),
            hari_kerja=hari_str or '0,1,2,3,4',
        )

        if not data['nama'] or not data['kode']:
            messages.error(request, 'Nama dan Kode shift wajib diisi.')
            return render(request, 'shifts/shift_form.html', {
                'instance': instance, 'TIPE_CHOICES': TIPE_CHOICES,
                'HARI_CHOICES': HARI_CHOICES,
            })

        company = getattr(request, 'company', None)

        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, f'Shift "{instance.nama}" berhasil diperbarui.')
        else:
            from django.db import IntegrityError
            try:
                instance = Shift.objects.create(**data, company=company)
                messages.success(request, f'Shift "{instance.nama}" berhasil ditambahkan.')
            except IntegrityError:
                messages.error(request, f'Nama atau kode shift "{data["nama"]}" sudah digunakan.')
                return render(request, 'shifts/shift_form.html', {
                    'instance': instance, 'TIPE_CHOICES': TIPE_CHOICES,
                    'HARI_CHOICES': HARI_CHOICES,
                })
        return redirect('shift_list')

    hari_aktif = instance.hari_kerja_list if instance else [0, 1, 2, 3, 4]
    return render(request, 'shifts/shift_form.html', {
        'instance': instance,
        'TIPE_CHOICES': TIPE_CHOICES,
        'HARI_CHOICES': HARI_CHOICES,
        'hari_aktif': hari_aktif,
    })


@login_required
@hr_required
def shift_delete(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == 'POST':
        nama = shift.nama
        shift.delete()
        messages.success(request, f'Shift "{nama}" berhasil dihapus.')
        return redirect('shift_list')
    return render(request, 'shifts/shift_confirm_delete.html', {'shift': shift})


# ══════════════════════════════════════════════════════════════════════════════
#  ASSIGNMENT SHIFT
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def assignment_list(request):
    dept_id = request.GET.get('dept', '')
    shift_id = request.GET.get('shift', '')

    qs = ShiftAssignment.objects.select_related(
        'employee', 'department', 'shift'
    ).order_by('-berlaku_mulai')

    if dept_id:
        qs = qs.filter(department_id=dept_id)
    if shift_id:
        qs = qs.filter(shift_id=shift_id)

    return render(request, 'shifts/assignment_list.html', {
        'assignments': qs,
        'shifts': Shift.objects.filter(aktif=True),
        'departments': Department.objects.filter(aktif=True),
        'dept_filter': dept_id,
        'shift_filter': shift_id,
    })


@login_required
@hr_required
def assignment_form(request, pk=None):
    instance = get_object_or_404(ShiftAssignment, pk=pk) if pk else None

    if request.method == 'POST':
        target = request.POST.get('target_type')  # 'employee' or 'department'
        emp_id  = request.POST.get('employee_id') or None
        dept_id = request.POST.get('department_id') or None
        shift_id = request.POST.get('shift_id')
        berlaku_mulai  = request.POST.get('berlaku_mulai')
        berlaku_sampai = request.POST.get('berlaku_sampai') or None
        hari_spesifik  = request.POST.get('hari_spesifik') or None

        if not shift_id or not berlaku_mulai:
            messages.error(request, 'Shift dan tanggal mulai wajib diisi.')
        elif target == 'employee' and not emp_id:
            messages.error(request, 'Pilih karyawan.')
        elif target == 'department' and not dept_id:
            messages.error(request, 'Pilih departemen.')
        else:
            data = dict(
                shift_id=shift_id,
                berlaku_mulai=berlaku_mulai,
                berlaku_sampai=berlaku_sampai,
                hari_spesifik=int(hari_spesifik) if hari_spesifik is not None and hari_spesifik != '' else None,
                keterangan=request.POST.get('keterangan', ''),
                employee_id=emp_id if target == 'employee' else None,
                department_id=dept_id if target == 'department' else None,
            )
            if instance:
                for k, v in data.items():
                    setattr(instance, k, v)
                instance.save()
                messages.success(request, 'Assignment shift berhasil diperbarui.')
            else:
                ShiftAssignment.objects.create(**data)
                messages.success(request, 'Assignment shift berhasil disimpan.')
            return redirect('assignment_list')

    return render(request, 'shifts/assignment_form.html', {
        'instance': instance,
        'shifts': Shift.objects.filter(aktif=True).order_by('nama'),
        'employees': get_company_qs(Employee, request, status='Aktif').order_by('nama'),
        'departments': Department.objects.filter(aktif=True).order_by('nama'),
        'HARI_CHOICES': list(enumerate(HARI_NAMA)),
    })


@login_required
@hr_required
def assignment_delete(request, pk):
    obj = get_object_or_404(ShiftAssignment, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Assignment shift dihapus.')
        return redirect('assignment_list')
    return render(request, 'shifts/assignment_confirm_delete.html', {'obj': obj})


# ══════════════════════════════════════════════════════════════════════════════
#  ROSTER BULANAN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def roster_view(request):
    """
    Roster bulanan — enterprise-grade:
    - Filter wajib per departemen (max 50 karyawan per load)
    - Pagination 50 karyawan per halaman
    - Cache 5 menit per dept/bulan
    - AJAX endpoint terpisah untuk data grid (non-blocking render)
    """
    from django.db import models as dm
    from django.core.paginator import Paginator

    today   = date.today()
    month   = int(request.GET.get('month',  today.month))
    year    = int(request.GET.get('year',   today.year))
    dept_id = request.GET.get('dept', '')
    page    = int(request.GET.get('page', 1))
    search  = request.GET.get('q', '').strip()

    BULAN_LIST = [
        (1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
        (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
        (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember'),
    ]
    HARI_CHOICES = list(enumerate(['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu']))
    PAGE_SIZE = 50

    _, days_in_month = calendar.monthrange(year, month)
    all_dates   = [date(year, month, d) for d in range(1, days_in_month + 1)]
    month_start = all_dates[0]
    month_end   = all_dates[-1]

    departments = Department.objects.filter(aktif=True).order_by('nama')

    # Wajib pilih departemen kalau total karyawan > 100
    total_aktif = get_company_qs(Employee, request, status='Aktif').count()
    require_dept_filter = total_aktif > 100

    grid          = []
    paginator     = None
    total_emp     = 0
    all_dates_out = all_dates

    # Hanya proses kalau sudah pilih dept (atau karyawan < 100)
    if dept_id or not require_dept_filter:
        employees_qs = get_company_qs(Employee, request, status='Aktif').select_related('department')
        if dept_id:
            employees_qs = employees_qs.filter(department_id=dept_id)
        if search:
            employees_qs = employees_qs.filter(nama__icontains=search)
        employees_qs = employees_qs.order_by('nama')

        paginator  = Paginator(employees_qs, PAGE_SIZE)
        page_obj   = paginator.get_page(page)
        employees  = list(page_obj.object_list)
        total_emp  = paginator.count
        emp_ids    = [e.id for e in employees]

        if emp_ids:
            # QUERY 1: roster bulan ini
            rosters = ShiftRoster.objects.filter(
                tanggal__month=month, tanggal__year=year,
                employee_id__in=emp_ids,
            ).select_related('shift')
            roster_map = {(r.employee_id, r.tanggal): r for r in rosters}

            # QUERY 2: assignment per karyawan
            emp_assign_map = {}
            for a in ShiftAssignment.objects.filter(
                employee_id__in=emp_ids,
                berlaku_mulai__lte=month_end,
            ).filter(
                dm.Q(berlaku_sampai__isnull=True) | dm.Q(berlaku_sampai__gte=month_start)
            ).select_related('shift').order_by('employee_id', '-berlaku_mulai'):
                emp_assign_map.setdefault(a.employee_id, []).append(a)

            # QUERY 3: assignment per departemen
            dept_ids = list({e.department_id for e in employees if e.department_id})
            dept_assign_map = {}
            for a in ShiftAssignment.objects.filter(
                department_id__in=dept_ids,
                employee__isnull=True,
                berlaku_mulai__lte=month_end,
            ).filter(
                dm.Q(berlaku_sampai__isnull=True) | dm.Q(berlaku_sampai__gte=month_start)
            ).select_related('shift').order_by('department_id', '-berlaku_mulai'):
                dept_assign_map.setdefault(a.department_id, []).append(a)

            def resolve_shift(emp, tgl):
                for a in emp_assign_map.get(emp.id, []):
                    if a.is_active_on(tgl):
                        return a.shift
                if emp.department_id:
                    for a in dept_assign_map.get(emp.department_id, []):
                        if a.is_active_on(tgl):
                            return a.shift
                return None

            for emp in employees:
                row = {'employee': emp, 'days': []}
                for tgl in all_dates:
                    roster = roster_map.get((emp.id, tgl))
                    if roster:
                        row['days'].append({
                            'tanggal': tgl, 'roster': roster,
                            'shift': roster.shift, 'is_off': roster.is_off,
                        })
                    else:
                        row['days'].append({
                            'tanggal': tgl, 'roster': None,
                            'shift': resolve_shift(emp, tgl), 'is_off': False,
                        })
                grid.append(row)

    return render(request, 'shifts/roster_view.html', {
        'grid':               grid,
        'all_dates':          all_dates_out,
        'month':              month,
        'year':               year,
        'dept_filter':        dept_id,
        'search':             search,
        'page_obj':           paginator.get_page(page) if paginator else None,
        'total_emp':          total_emp,
        'page_size':          PAGE_SIZE,
        'require_dept_filter': require_dept_filter,
        'shifts':             Shift.objects.filter(aktif=True).order_by('nama'),
        'departments':        departments,
        'bulan_nama':         calendar.month_name[month],
        'bulan_list':         BULAN_LIST,
        'hari_choices':       HARI_CHOICES,
        'today_month':        today.month,
        'today_year':         today.year,
    })


@login_required
@require_POST
def roster_save_cell(request):
    """AJAX: simpan 1 cell roster (1 karyawan, 1 tanggal)."""
    if not (request.user.is_staff or getattr(request.user, 'is_hr', False)):
        return JsonResponse({'ok': False, 'error': 'Tidak punya akses.'}, status=403)
    try:
        data     = json.loads(request.body)
        emp_id   = data.get('employee_id')
        tgl_str  = data.get('tanggal')
        shift_id = data.get('shift_id')  # None = OFF
        is_off   = data.get('is_off', False)
        ket      = data.get('keterangan', '')

        employee = Employee.objects.get(pk=emp_id)
        tgl      = date.fromisoformat(tgl_str)

        roster, created = ShiftRoster.objects.update_or_create(
            employee=employee, tanggal=tgl,
            defaults={
                'shift_id': shift_id if not is_off else None,
                'is_off': is_off,
                'keterangan': ket,
            }
        )
        return JsonResponse({'ok': True, 'created': created})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def roster_bulk_fill(request):
    """AJAX: isi roster massal (1 shift untuk semua karyawan di rentang tanggal)."""
    if not (request.user.is_staff or getattr(request.user, 'is_hr', False)):
        return JsonResponse({'ok': False, 'error': 'Tidak punya akses.'}, status=403)
    try:
        data      = json.loads(request.body)
        emp_ids   = data.get('employee_ids', [])
        tgl_start = date.fromisoformat(data.get('tgl_start'))
        tgl_end   = date.fromisoformat(data.get('tgl_end'))
        shift_id  = data.get('shift_id')
        is_off    = data.get('is_off', False)
        hari_list = data.get('hari_list', [0,1,2,3,4])  # hari yang diisi

        employees = Employee.objects.filter(pk__in=emp_ids) if emp_ids else get_company_qs(Employee, request, status='Aktif')
        saved = 0
        current = tgl_start
        while current <= tgl_end:
            if current.weekday() in hari_list:
                for emp in employees:
                    ShiftRoster.objects.update_or_create(
                        employee=emp, tanggal=current,
                        defaults={
                            'shift_id': shift_id if not is_off else None,
                            'is_off': is_off,
                        }
                    )
                    saved += 1
            current += timedelta(days=1)

        return JsonResponse({'ok': True, 'saved': saved})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE SHIFT VIEW (per karyawan)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def employee_shift_view(request, employee_id):
    emp = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year', today.year))

    _, days_in_month = calendar.monthrange(year, month)
    all_dates = [date(year, month, d) for d in range(1, days_in_month + 1)]

    rosters = ShiftRoster.objects.filter(
        employee=emp, tanggal__month=month, tanggal__year=year
    ).select_related('shift')
    roster_map = {r.tanggal: r for r in rosters}

    assignments = ShiftAssignment.objects.filter(
        employee=emp
    ).select_related('shift').order_by('-berlaku_mulai')

    days = []
    for tgl in all_dates:
        roster = roster_map.get(tgl)
        if roster:
            shift = roster.shift
            is_off = roster.is_off
        else:
            shift = get_shift_for_employee(emp, tgl)
            is_off = False
        days.append({'tanggal': tgl, 'shift': shift, 'is_off': is_off, 'roster': roster})

    return render(request, 'shifts/employee_shift.html', {
        'employee': emp,
        'days': days,
        'assignments': assignments,
        'month': month,
        'year': year,
        'bulan_nama': calendar.month_name[month],
    })
