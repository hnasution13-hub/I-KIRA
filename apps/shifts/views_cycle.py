"""
TAMBAHKAN ke apps/shifts/views.py
===================================
Views untuk ShiftCycle (pola security 4-3, 12 jam, dll)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import date
import json, calendar

# Import models (sesuaikan setelah merge ke models.py)
from .models_cycle import (
    ShiftCycle, EmployeeShiftCycle,
    get_cycle_shift_for_employee,
    generate_roster_from_cycle,
)
from .models import Shift, ShiftRoster
from apps.employees.models import Employee
from apps.core.models import Department

def _get_company(request):
    """Helper multi-tenant: ambil company aktif dari request."""
    company = getattr(request, 'company', None)
    if not company and getattr(request.user, 'is_superuser', False):
        from apps.core.models import Company
        company = Company.objects.first()
    return company




# ══════════════════════════════════════════════════════════════════════════════
#  MASTER POLA CYCLIC
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def cycle_list(request):
    cycles = ShiftCycle.objects.prefetch_related('assignments').all()
    company = _get_company(request)
    shifts = Shift.objects.filter(company=company, aktif=True).order_by('nama') if company else Shift.objects.filter(aktif=True).order_by('nama')

    # Hitung preview pola untuk tiap cycle
    for c in cycles:
        pola = c.pola
        preview = []
        for sid in pola:
            if sid is None:
                preview.append({'label': 'OFF', 'warna': '#6c757d', 'is_off': True})
            else:
                s = next((x for x in shifts if x.id == sid), None)
                if s:
                    preview.append({'label': s.kode, 'warna': s.warna, 'is_off': False})
                else:
                    preview.append({'label': '?', 'warna': '#adb5bd', 'is_off': False})
        c.preview = preview
        c.jumlah_assignment = c.assignments.filter(aktif=True).count()

    return render(request, 'shifts/cycle_list.html', {
        'cycles': cycles,
        'shifts': shifts,
    })


@login_required
def cycle_form(request, pk=None):
    instance = get_object_or_404(ShiftCycle, pk=pk) if pk else None
    shifts   = Shift.objects.filter(aktif=True).order_by('nama')

    if request.method == 'POST':
        nama       = request.POST.get('nama', '').strip()
        keterangan = request.POST.get('keterangan', '')
        aktif      = bool(request.POST.get('aktif'))
        pola_raw   = request.POST.get('pola_json', '[]')

        # Validasi JSON
        try:
            pola = json.loads(pola_raw)
            if not isinstance(pola, list) or len(pola) == 0:
                raise ValueError('Pola harus array minimal 1 elemen')
            # Validasi tiap elemen: int shift_id atau null
            for item in pola:
                if item is not None and not isinstance(item, int):
                    raise ValueError(f'Elemen pola harus angka shift_id atau null, dapat: {item}')
        except (json.JSONDecodeError, ValueError) as e:
            messages.error(request, f'Format pola tidak valid: {e}')
            return render(request, 'shifts/cycle_form.html', {
                'instance': instance, 'shifts': shifts,
            })

        if not nama:
            messages.error(request, 'Nama pola wajib diisi.')
            return render(request, 'shifts/cycle_form.html', {
                'instance': instance, 'shifts': shifts,
            })

        data = dict(nama=nama, keterangan=keterangan, pola_json=pola_raw, aktif=aktif)
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
            messages.success(request, f'Pola "{nama}" berhasil diperbarui.')
        else:
            instance = ShiftCycle.objects.create(**data)
            messages.success(request, f'Pola "{nama}" berhasil disimpan.')
        return redirect('cycle_list')

    return render(request, 'shifts/cycle_form.html', {
        'instance': instance,
        'shifts': shifts,
        'pola_json_init': instance.pola_json if instance else '[]',
    })


@login_required
def cycle_delete(request, pk):
    obj = get_object_or_404(ShiftCycle, pk=pk)
    if request.method == 'POST':
        nama = obj.nama
        obj.delete()
        messages.success(request, f'Pola "{nama}" dihapus.')
        return redirect('cycle_list')
    return render(request, 'shifts/cycle_confirm_delete.html', {'obj': obj})


# ══════════════════════════════════════════════════════════════════════════════
#  ASSIGNMENT POLA KE KARYAWAN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def cycle_assignment_list(request):
    dept_id  = request.GET.get('dept', '')
    cycle_id = request.GET.get('cycle', '')

    qs = EmployeeShiftCycle.objects.select_related(
        'employee', 'employee__department', 'cycle'
    ).order_by('employee__nama', '-mulai_dari')

    if dept_id:
        qs = qs.filter(employee__department_id=dept_id)
    if cycle_id:
        qs = qs.filter(cycle_id=cycle_id)

    return render(request, 'shifts/cycle_assignment_list.html', {
        'assignments': qs,
        'cycles': ShiftCycle.objects.filter(company=company, aktif=True) if company else ShiftCycle.objects.filter(aktif=True),
        'departments': Department.objects.filter(company=company, aktif=True) if company else Department.objects.filter(aktif=True),
        'dept_filter': dept_id,
        'cycle_filter': cycle_id,
    })


@login_required
def cycle_assignment_form(request, pk=None):
    instance  = get_object_or_404(EmployeeShiftCycle, pk=pk) if pk else None
    # Pre-fill dari query param
    emp_preselect = request.GET.get('emp')

    if request.method == 'POST':
        emp_id     = request.POST.get('employee_id')
        cycle_id   = request.POST.get('cycle_id')
        mulai_dari = request.POST.get('mulai_dari')
        berlaku_sampai = request.POST.get('berlaku_sampai') or None
        keterangan = request.POST.get('keterangan', '')
        aktif      = bool(request.POST.get('aktif'))
        auto_gen   = bool(request.POST.get('auto_generate'))

        if not emp_id or not cycle_id or not mulai_dari:
            messages.error(request, 'Karyawan, pola, dan tanggal mulai wajib diisi.')
        else:
            data = dict(
                employee_id=emp_id, cycle_id=cycle_id,
                mulai_dari=mulai_dari, berlaku_sampai=berlaku_sampai,
                keterangan=keterangan, aktif=aktif,
            )
            if instance:
                for k, v in data.items():
                    setattr(instance, k, v)
                instance.save()
                messages.success(request, 'Assignment pola berhasil diperbarui.')
            else:
                instance = EmployeeShiftCycle.objects.create(**data)
                messages.success(request, 'Assignment pola berhasil disimpan.')

            # Auto-generate roster bulan ini jika diminta
            if auto_gen:
                today = date.today()
                emp   = Employee.objects.get(pk=emp_id)
                n = generate_roster_from_cycle(emp, today.year, today.month)
                messages.info(request, f'Auto-generate: {n} hari roster bulan ini berhasil dibuat.')

            return redirect('cycle_assignment_list')

    return render(request, 'shifts/cycle_assignment_form.html', {
        'instance': instance,
        'cycles': ShiftCycle.objects.filter(company=company, aktif=True).order_by('nama') if company else ShiftCycle.objects.filter(aktif=True).order_by('nama'),
        'employees': Employee.objects.filter(company=company, status='Aktif').select_related('department').order_by('nama') if company else Employee.objects.filter(status='Aktif').select_related('department').order_by('nama'),
        'emp_preselect': emp_preselect,
    })


@login_required
def cycle_assignment_delete(request, pk):
    obj = get_object_or_404(EmployeeShiftCycle, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Assignment pola dihapus.')
        return redirect('cycle_assignment_list')
    return render(request, 'shifts/cycle_assignment_confirm_delete.html', {'obj': obj})


# ══════════════════════════════════════════════════════════════════════════════
#  PREVIEW JADWAL CYCLIC PER KARYAWAN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def cycle_preview(request, employee_id):
    emp   = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year',  today.year))

    _, days_in_month = calendar.monthrange(year, month)
    shifts_all = {s.id: s for s in Shift.objects.filter(aktif=True)}

    # Ambil assignment cyclic aktif
    assignment = EmployeeShiftCycle.objects.filter(
        employee=emp, aktif=True
    ).select_related('cycle').order_by('-mulai_dari').first()

    days = []
    for d in range(1, days_in_month + 1):
        tgl = date(year, month, d)

        # Cek roster manual override
        roster = ShiftRoster.objects.filter(employee=emp, tanggal=tgl).select_related('shift').first()

        if roster:
            shift     = roster.shift
            is_off    = roster.is_off
            source    = 'manual'
            hari_ke   = None
        elif assignment and assignment.is_active_on(tgl):
            delta   = (tgl - assignment.mulai_dari).days
            hari_ke = delta % assignment.cycle.panjang_siklus
            sid     = assignment.cycle.get_shift_for_date(tgl, assignment.mulai_dari)
            shift   = shifts_all.get(sid) if sid else None
            is_off  = (sid is None)
            source  = 'cycle'
        else:
            shift   = None
            is_off  = False
            source  = 'none'
            hari_ke = None

        days.append({
            'tanggal': tgl,
            'shift':   shift,
            'is_off':  is_off,
            'source':  source,
            'hari_ke': hari_ke,
        })

    # Hitung statistik bulan ini
    total_kerja = sum(1 for d in days if not d['is_off'] and d['shift'])
    total_off   = sum(1 for d in days if d['is_off'])

    return render(request, 'shifts/cycle_preview.html', {
        'employee':   emp,
        'assignment': assignment,
        'days':       days,
        'month':      month,
        'year':       year,
        'bulan_nama': calendar.month_name[month],
        'total_kerja': total_kerja,
        'total_off':   total_off,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  AJAX: Auto-generate roster dari cycle untuk 1 bulan
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def cycle_generate_roster(request):
    try:
        data    = json.loads(request.body)
        emp_ids = data.get('employee_ids', [])
        year    = int(data.get('year',  date.today().year))
        month   = int(data.get('month', date.today().month))
        override = data.get('override', False)

        employees = Employee.objects.filter(pk__in=emp_ids) if emp_ids \
                    else Employee.objects.filter(company=company, status='Aktif') if company else Employee.objects.filter(status='Aktif')

        total = 0
        skipped = 0
        for emp in employees:
            if override:
                # Hapus roster cycle-generated dulu (bukan manual)
                ShiftRoster.objects.filter(
                    employee=emp,
                    tanggal__month=month,
                    tanggal__year=year,
                    keterangan='Auto-generate dari pola cyclic'
                ).delete()
            n = generate_roster_from_cycle(emp, year, month)
            total   += n
            skipped += 0  # bisa dikembangkan

        return JsonResponse({
            'ok': True,
            'generated': total,
            'employees': len(list(employees)),
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
