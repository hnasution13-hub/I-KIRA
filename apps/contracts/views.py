from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import hr_required
from django.views.decorators.http import require_POST
from .models import Contract
from apps.employees.models import Employee
from apps.core.utils import get_company_qs, get_employee_related_qs


@login_required
def contract_list(request):
    contracts = get_employee_related_qs(Contract, request).select_related('employee').order_by('-tanggal_mulai')
    return render(request, 'contracts/contract_list.html', {'contracts': contracts})


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'contracts/contract_detail.html', {'contract': contract})


@login_required
def contract_form(request, pk=None):
    instance = get_object_or_404(Contract, pk=pk) if pk else None
    if request.method == 'POST':
        emp = get_object_or_404(Employee, pk=request.POST.get('employee'))
        data = {
            'employee': emp,
            'tipe_kontrak': request.POST.get('tipe_kontrak'),
            'tanggal_mulai': request.POST.get('tanggal_mulai'),
            'tanggal_selesai': request.POST.get('tanggal_selesai') or None,
            'jabatan': request.POST.get('jabatan', ''),
            'departemen': request.POST.get('departemen', ''),
            'gaji_pokok': int(request.POST.get('gaji_pokok', 0) or 0),
            'status_gaji': request.POST.get('status_gaji', 'reguler'),
            'nama_penandatangan': request.POST.get('nama_penandatangan', ''),
            'jabatan_penandatangan': request.POST.get('jabatan_penandatangan', ''),
            'status': request.POST.get('status', 'Aktif'),
            'keterangan': request.POST.get('keterangan', ''),
        }
        if 'file_kontrak' in request.FILES:
            data['file_kontrak'] = request.FILES['file_kontrak']
        if instance:
            for k, v in data.items():
                setattr(instance, k, v)
            instance.save()
        else:
            # Developer: request.company = None, ambil dari company employee
            data['company'] = request.company or emp.company
            Contract.objects.create(**data)
        messages.success(request, 'Kontrak berhasil disimpan.')
        return redirect('contract_list')

    return render(request, 'contracts/contract_form.html', {
        'instance': instance,
        'employees': get_company_qs(Employee, request, status='Aktif'),
    })


@login_required
def contract_expiring(request):
    from datetime import date, timedelta
    today = date.today()
    contracts = get_employee_related_qs(Contract, request).filter(
        status='Aktif',
        tanggal_selesai__isnull=False,
        tanggal_selesai__lte=today + timedelta(days=30),
        tanggal_selesai__gte=today,
    ).select_related('employee').order_by('tanggal_selesai')
    return render(request, 'contracts/expiring_list.html', {'contracts': contracts})


# P2.6: Contract Renewal/Perpanjang
@login_required
def contract_renew(request, pk):
    """Perpanjang kontrak: buat kontrak baru pre-filled dari kontrak lama, tandai lama sebagai Renewed."""
    old_contract = get_object_or_404(Contract, pk=pk)

    if request.method == 'POST':
        emp = old_contract.employee
        data = {
            'employee': emp,
            'tipe_kontrak': request.POST.get('tipe_kontrak'),
            'tanggal_mulai': request.POST.get('tanggal_mulai'),
            'tanggal_selesai': request.POST.get('tanggal_selesai') or None,
            'jabatan': request.POST.get('jabatan', ''),
            'departemen': request.POST.get('departemen', ''),
            'gaji_pokok': int(request.POST.get('gaji_pokok', 0) or 0),
            'status': 'Aktif',
            'keterangan': request.POST.get('keterangan', ''),
        }
        if 'file_kontrak' in request.FILES:
            data['file_kontrak'] = request.FILES['file_kontrak']
        new_contract = Contract.objects.create(**data)
        # Tandai kontrak lama sebagai Renewed
        old_contract.status = 'Renewed'
        old_contract.save()
        messages.success(request, f'Kontrak {emp.nama} berhasil diperpanjang. Nomor baru: {new_contract.nomor_kontrak}')
        return redirect('contract_detail', pk=new_contract.pk)

    return render(request, 'contracts/contract_renew.html', {
        'old_contract': old_contract,
    })


# FIX P1: Contract Delete
@login_required
@hr_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if request.method == 'POST':
        nama = contract.employee.nama
        contract.delete()
        messages.success(request, f'Kontrak {nama} berhasil dihapus.')
        return redirect('contract_list')
    return render(request, 'contracts/contract_confirm_delete.html', {'contract': contract})


@login_required
def api_employee_info(request):
    """AJAX: return data karyawan (jabatan, departemen, gaji, status_gaji) by NIK/pk — multi-tenant safe."""
    import json
    from django.http import JsonResponse
    emp_id = request.GET.get('employee_id')
    if not emp_id:
        return JsonResponse({'error': 'employee_id required'}, status=400)
    # Multi-tenant: pastikan employee milik company yang sama
    emp = get_company_qs(Employee, request).filter(pk=emp_id).select_related('jabatan', 'department').first()
    if not emp:
        return JsonResponse({'error': 'not found'}, status=404)
    data = {
        'jabatan': emp.jabatan.nama if emp.jabatan else '',
        'departemen': emp.department.nama if emp.department else '',
        'gaji_pokok': 0,
        'status_gaji': 'reguler',
    }
    try:
        sb = emp.salary_benefit
        data['gaji_pokok'] = sb.gaji_pokok
        data['status_gaji'] = sb.status_gaji
    except Exception:
        pass
    return JsonResponse(data)


@login_required
def _format_alamat_lengkap(emp):
    """Susun alamat lengkap dari field-field Employee."""
    parts = []
    if emp.alamat:
        parts.append(emp.alamat)
    rt_rw = ''
    if emp.rt and emp.rw:
        rt_rw = f'RT {emp.rt}/RW {emp.rw}'
    elif emp.rt:
        rt_rw = f'RT {emp.rt}'
    elif emp.rw:
        rt_rw = f'RW {emp.rw}'
    if rt_rw:
        parts.append(rt_rw)
    if emp.kelurahan:
        parts.append(f'Kel. {emp.kelurahan}')
    if emp.kecamatan:
        parts.append(f'Kec. {emp.kecamatan}')
    if emp.kabupaten_id:
        try:
            parts.append(str(emp.kabupaten))
        except Exception:
            pass
    if emp.provinsi_id:
        try:
            parts.append(str(emp.provinsi))
        except Exception:
            pass
    if emp.kode_pos:
        parts.append(emp.kode_pos)
    return ', '.join(filter(None, parts)) or '__________________'


def _get_contract_with_employee(request, pk):
    return get_object_or_404(
        get_employee_related_qs(Contract, request).select_related(
            'employee', 'employee__jabatan', 'employee__department',
            'employee__kabupaten', 'employee__provinsi', 'company'
        ),
        pk=pk
    )


@login_required
def pkwt_print(request, pk):
    """Halaman print/PDF PKWT — multi-tenant safe."""
    contract = _get_contract_with_employee(request, pk)
    durasi_str = ''
    if contract.tanggal_mulai and contract.tanggal_selesai:
        delta = contract.tanggal_selesai - contract.tanggal_mulai
        total_bulan = round(delta.days / 30)
        if total_bulan >= 12:
            tahun = total_bulan // 12
            sisa_bulan = total_bulan % 12
            if sisa_bulan:
                durasi_str = f'{tahun} ({_terbilang_tahun(tahun)}) tahun {sisa_bulan} bulan'
            else:
                durasi_str = f'{tahun} ({_terbilang_tahun(tahun)}) tahun'
        else:
            durasi_str = f'{total_bulan} ({_terbilang_bulan(total_bulan)}) bulan'

    return render(request, 'contracts/pkwt_print.html', {
        'contract': contract,
        'company': contract.company,
        'durasi_str': durasi_str,
        'alamat_lengkap': _format_alamat_lengkap(contract.employee),
    })


def _terbilang_tahun(n):
    kata = ['', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan', 'Sepuluh']
    return kata[n] if n <= 10 else str(n)


def _terbilang_bulan(n):
    kata = ['', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan',
            'Sepuluh', 'Sebelas', 'Dua Belas']
    return kata[n] if n <= 12 else str(n)


@login_required
def pkwtt_print(request, pk):
    """Halaman print/PDF PKWTT — multi-tenant safe."""
    contract = _get_contract_with_employee(request, pk)
    return render(request, 'contracts/pkwtt_print.html', {
        'contract': contract,
        'company': contract.company,
        'alamat_lengkap': _format_alamat_lengkap(contract.employee),
    })


@login_required
def phl_print(request, pk):
    """Halaman print/PDF Perjanjian Harian Lepas — multi-tenant safe."""
    contract = _get_contract_with_employee(request, pk)
    return render(request, 'contracts/phl_print.html', {
        'contract': contract,
        'company': contract.company,
        'alamat_lengkap': _format_alamat_lengkap(contract.employee),
    })
