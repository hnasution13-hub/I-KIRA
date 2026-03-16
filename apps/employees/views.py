from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Employee, EmployeeDocument, PointOfHire, JobSite, Perusahaan
from apps.core.models import Department, Position
from apps.core.decorators import hr_required, manager_required
from apps.wilayah.models import Provinsi, Kabupaten


def _can_see_salary(user):
    """Hanya Supervisor ke atas (admin, hr_manager, manager) yang bisa lihat/edit gaji."""
    return user.role in ('admin', 'hr_manager', 'manager')


@login_required
def employee_list(request):
    company   = getattr(request, 'company', None)
    employees = Employee.objects.select_related('department', 'jabatan', 'job_site', 'perusahaan')
    if company:
        employees = employees.filter(company=company)
    search    = request.GET.get('q', '')
    dept      = request.GET.get('dept', '')
    status    = request.GET.get('status', 'Aktif')
    job_site  = request.GET.get('job_site', '')
    perusahaan = request.GET.get('perusahaan', '')

    if search:
        employees = employees.filter(
            Q(nama__icontains=search) | Q(nik__icontains=search) | Q(email__icontains=search)
        )
    if dept:
        employees = employees.filter(department_id=dept)
    if status:
        employees = employees.filter(status=status)
    if job_site:
        employees = employees.filter(job_site_id=job_site)
    if perusahaan:
        employees = employees.filter(perusahaan_id=perusahaan)

    return render(request, 'employees/employee_list.html', {
        'employees'   : employees,
        'departments' : Department.objects.filter(aktif=True, **({'company': company} if company else {})),
        'job_sites'   : JobSite.objects.filter(aktif=True),
        'perusahaans' : Perusahaan.objects.filter(aktif=True),
        'search'      : search,
        'status_filter': status,
        'job_site_filter': job_site,
        'perusahaan_filter': perusahaan,
    })


@login_required
def employee_detail(request, pk):
    company = getattr(request, 'company', None)
    qs = Employee.objects.select_related(
        'department', 'jabatan', 'point_of_hire', 'job_site',
        'provinsi', 'kabupaten',
    )
    if company:
        qs = qs.filter(company=company)
    employee   = get_object_or_404(qs, pk=pk)
    documents  = employee.documents.all()
    contracts  = employee.contracts.order_by('-tanggal_mulai')[:5]
    leaves     = employee.leaves.order_by('-created_at')[:5]
    violations = employee.violations.order_by('-tanggal_kejadian')[:5]
    try:
        salary = employee.salary_benefit if _can_see_salary(request.user) else None
    except Exception:
        salary = None
    from apps.core.addon_decorators import check_addon
    return render(request, 'employees/employee_detail.html', {
        'employee': employee, 'documents': documents,
        'contracts': contracts, 'leaves': leaves,
        'violations': violations, 'salary': salary,
        'can_see_salary': _can_see_salary(request.user),
        'addon_advanced_psychotest': check_addon(request, 'advanced_psychotest'),
    })


@login_required
@hr_required
def employee_form(request, pk=None):
    instance = get_object_or_404(Employee, pk=pk) if pk else None

    if request.method == 'POST':
        nik = request.POST.get('nik', '').strip()
        company   = getattr(request, 'company', None)
        nik_qs = Employee.objects.filter(nik=nik)
        if company:
            nik_qs = nik_qs.filter(company=company)
        if instance:
            nik_qs = nik_qs.exclude(pk=instance.pk)
        if nik_qs.exists():
            messages.error(request, f'NIK "{nik}" sudah digunakan oleh karyawan lain.')
            return _render_form(request, instance)

        # ── Resolve tempat_lahir: form kirim ID kabupaten, model simpan nama string ──
        tempat_lahir_id = request.POST.get('tempat_lahir_id', '').strip()
        tempat_lahir_str = ''
        if tempat_lahir_id:
            try:
                from apps.wilayah.models import Kabupaten
                kab = Kabupaten.objects.get(pk=tempat_lahir_id)
                tempat_lahir_str = kab.nama
            except Exception:
                tempat_lahir_str = ''

        # ── Resolve kecamatan/kelurahan: form kirim ID, model simpan nama string ──
        kecamatan_str = ''
        kelurahan_str = ''
        kecamatan_id = request.POST.get('kecamatan_id', '').strip()
        kelurahan_id = request.POST.get('kelurahan_id', '').strip()
        if kecamatan_id:
            try:
                from apps.wilayah.models import Kecamatan
                kecamatan_str = Kecamatan.objects.get(pk=kecamatan_id).nama
            except Exception:
                pass
        if kelurahan_id:
            try:
                from apps.wilayah.models import Kelurahan
                kelurahan_str = Kelurahan.objects.get(pk=kelurahan_id).nama
            except Exception:
                pass

        # ── Helper safe int ──────────────────────────────────────────────────
        def _int(key, default=0):
            try:
                return int(request.POST.get(key, default) or default)
            except (ValueError, TypeError):
                return default

        data = {
            # Data Utama
            'nik'             : nik,
            'nama'            : request.POST.get('nama', ''),
            'department_id'   : request.POST.get('department') or None,
            'jabatan_id'      : request.POST.get('jabatan') or None,
            'status_karyawan' : request.POST.get('status_karyawan', 'PKWT'),
            'join_date'       : request.POST.get('join_date'),
            'status'          : request.POST.get('status', 'Aktif'),
            'point_of_hire_id': request.POST.get('point_of_hire') or None,
            'job_site_id'     : request.POST.get('job_site') or None,
            # Data Pribadi
            'jenis_kelamin'   : request.POST.get('jenis_kelamin', ''),
            'tempat_lahir'    : tempat_lahir_str,
            'tanggal_lahir'   : request.POST.get('tanggal_lahir') or None,
            'agama'           : request.POST.get('agama', ''),
            'pendidikan'      : request.POST.get('pendidikan', ''),
            'golongan_darah'  : request.POST.get('golongan_darah', ''),
            # Dokumen
            'no_ktp'          : request.POST.get('no_ktp', ''),
            'no_npwp'         : request.POST.get('no_npwp', ''),
            'no_bpjs_tk'      : request.POST.get('no_bpjs_tk', ''),
            'no_bpjs_kes'     : request.POST.get('no_bpjs_kes', ''),
            'no_kk'           : request.POST.get('no_kk', ''),
            # Keluarga
            'status_nikah'    : request.POST.get('status_nikah', ''),
            'ptkp'            : request.POST.get('ptkp', ''),
            'jumlah_anak'     : _int('jumlah_anak'),
            # Kontak
            'no_hp'           : request.POST.get('no_hp', ''),
            'hp_darurat'      : request.POST.get('no_darurat', ''),
            'email'           : request.POST.get('email', ''),
            'nama_darurat'    : request.POST.get('nama_darurat', ''),
            'hub_darurat'     : request.POST.get('hub_darurat', ''),
            # Bank
            'nama_bank'       : request.POST.get('bank_name', ''),
            'no_rek'          : request.POST.get('bank_account', ''),
            'nama_rek'        : request.POST.get('bank_account_name', ''),
            # Alamat KTP
            'alamat'          : request.POST.get('alamat', ''),
            'rt'              : request.POST.get('rt', ''),
            'rw'              : request.POST.get('rw', ''),
            'provinsi_id'     : request.POST.get('provinsi_id') or None,
            'kabupaten_id'    : request.POST.get('kabupaten_id') or None,
            'kecamatan'       : kecamatan_str,
            'kelurahan'       : kelurahan_str,
            'kode_pos'        : request.POST.get('kode_pos', ''),
        }

        # ── Field opsional yang mungkin belum ada di model lama ─────────────
        # Ditulis defensif agar tidak crash kalau field belum ada di DB
        _optional_fields = {
            'etnis'          : request.POST.get('etnis', ''),
            'no_skck'        : request.POST.get('no_skck', ''),
            'jenis_sim'      : request.POST.get('jenis_sim', ''),
            'no_sim'         : request.POST.get('no_sim', ''),
            'nama_pasangan'  : request.POST.get('nama_pasangan', ''),
            'nama_bapak'     : request.POST.get('nama_bapak', ''),
            'nama_ibu'       : request.POST.get('nama_ibu', ''),
            'no_hp_2'        : request.POST.get('no_hp_2', ''),
            'no_darurat_2'   : request.POST.get('no_darurat_2', ''),
            # Alamat domisili
            'domisili_sama'      : request.POST.get('domisili_sama') == '1',
            'alamat_domisili'    : request.POST.get('alamat_domisili', ''),
            'rt_domisili'        : request.POST.get('rt_domisili', ''),
            'rw_domisili'        : request.POST.get('rw_domisili', ''),
            'provinsi_domisili_id'  : request.POST.get('provinsi_domisili_id') or None,
            'kabupaten_domisili_id' : request.POST.get('kabupaten_domisili_id') or None,
            'kode_pos_domisili'  : request.POST.get('kode_pos_domisili', ''),
        }
        # Resolve kecamatan/kelurahan domisili
        kec_dom_id = request.POST.get('kecamatan_domisili_id', '').strip()
        kel_dom_id = request.POST.get('kelurahan_domisili_id', '').strip()
        if kec_dom_id:
            try:
                from apps.wilayah.models import Kecamatan
                _optional_fields['kecamatan_domisili'] = Kecamatan.objects.get(pk=kec_dom_id).nama
            except Exception:
                pass
        if kel_dom_id:
            try:
                from apps.wilayah.models import Kelurahan
                _optional_fields['kelurahan_domisili'] = Kelurahan.objects.get(pk=kel_dom_id).nama
            except Exception:
                pass

        # Hanya masukkan ke data kalau field-nya memang ada di model
        _emp_fields = {f.name for f in Employee._meta.get_fields() if hasattr(f, 'name')}
        for k, v in _optional_fields.items():
            field_key = k.replace('_id', '') if k.endswith('_id') else k
            if k in _emp_fields or field_key in _emp_fields:
                data[k] = v

        if not data.get('join_date'):
            messages.error(request, 'Tanggal masuk wajib diisi.')
            return _render_form(request, instance)

        # ── Pisahkan FK _id fields dari CharField biasa ─────────────────────
        # Django butuh set `department_id` langsung (bukan setattr 'department')
        # agar tidak trigger query tambahan / error RelatedObjectDoesNotExist
        fk_id_keys = {k for k in data if k.endswith('_id')}
        regular_keys = {k for k in data if not k.endswith('_id')}

        try:
            if instance:
                # Update FK fields
                for k in fk_id_keys:
                    setattr(instance, k, data[k])
                # Update regular fields — hanya yang benar-benar ada di model
                _model_fields = {f.attname for f in Employee._meta.concrete_fields}
                _model_fields |= {f.name for f in Employee._meta.concrete_fields}
                for k in regular_keys:
                    if k in _model_fields:
                        setattr(instance, k, data[k])
                if 'foto' in request.FILES:
                    instance.foto = request.FILES['foto']
                instance.save()
                _save_anak(instance, request.POST)
                messages.success(request, f'Data {instance.nama} berhasil diperbarui.')
            else:
                # Buat instance baru — hanya kirim field yang valid ke konstruktor
                _model_attnames = {f.attname for f in Employee._meta.concrete_fields}
                _model_attnames |= {f.name for f in Employee._meta.concrete_fields}
                safe_data = {k: v for k, v in data.items() if k in _model_attnames}
                emp = Employee(**safe_data)
                if company:
                    emp.company = company
                if 'foto' in request.FILES:
                    emp.foto = request.FILES['foto']
                emp.save()
                _save_anak(emp, request.POST)
                messages.success(request, f'Karyawan {emp.nama} berhasil ditambahkan.')
            return redirect('employee_list')

        except Exception as exc:
            import logging, traceback
            logger = logging.getLogger('apps')
            logger.error('employee_form POST error: %s\n%s', exc, traceback.format_exc())
            messages.error(request, f'Terjadi kesalahan saat menyimpan data: {exc}')
            return _render_form(request, instance)

    return _render_form(request, instance)


def _save_anak(employee, post_data):
    """Simpan data anak dari form POST ke model AnakKaryawan."""
    from .models import AnakKaryawan
    # Hapus data lama, replace dengan yang baru
    employee.anak_list.all().delete()
    nama_list  = post_data.getlist('anak_nama[]')
    tgl_list   = post_data.getlist('anak_tgl_lahir[]')
    jk_list    = post_data.getlist('anak_jk[]')
    bpjs_list  = post_data.getlist('anak_bpjs[]')
    tanggungan = post_data.getlist('anak_tanggungan[]')

    for i, nama in enumerate(nama_list):
        nama = nama.strip()
        if not nama:
            continue
        AnakKaryawan.objects.create(
            employee       = employee,
            urutan         = i + 1,
            nama           = nama,
            tgl_lahir      = tgl_list[i] if i < len(tgl_list) and tgl_list[i] else None,
            jenis_kelamin  = jk_list[i] if i < len(jk_list) else '',
            no_bpjs_kes    = bpjs_list[i] if i < len(bpjs_list) else '',
            tanggungan_bpjs= str(i) in tanggungan,
        )

def _render_form(request, instance):
    from apps.wilayah.models import Bank
    return render(request, 'employees/employee_form.html', {
        'instance'          : instance,
        'departments'       : Department.objects.filter(aktif=True, **({'company': getattr(request, 'company', None)} if getattr(request, 'company', None) else {})),
        'positions'         : Position.objects.filter(aktif=True, **({'company': getattr(request, 'company', None)} if getattr(request, 'company', None) else {})),
        'provinsi_list'     : Provinsi.objects.all(),
        'kabupaten_list'    : Kabupaten.objects.all(),
        'poh_list'          : Kabupaten.objects.all().order_by('nama'),
        'jobsite_list'      : JobSite.objects.filter(aktif=True),
        'bank_list'         : Bank.objects.all().order_by('nama'),
        'golongan_darah_list': ['A','B','AB','O','A+','A-','B+','B-','AB+','AB-','O+','O-'],
    })


@login_required
@hr_required
def salary_form(request, pk):
    """Edit gaji — hanya untuk Supervisor ke atas."""
    if not _can_see_salary(request.user):
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('employee_list')

    from apps.payroll.models import SalaryBenefit
    employee = get_object_or_404(Employee, pk=pk)
    salary, _ = SalaryBenefit.objects.get_or_create(employee=employee)

    if request.method == 'POST':
        def intval(key):
            try: return int(request.POST.get(key, 0) or 0)
            except: return 0

        salary.gaji_pokok              = intval('gaji_pokok')
        salary.tunjangan_jabatan       = intval('tunjangan_jabatan')
        salary.tunjangan_komunikasi    = intval('tunjangan_komunikasi')
        salary.tunjangan_site          = intval('tunjangan_site')
        salary.tunjangan_kehadiran     = intval('tunjangan_kehadiran')
        salary.tunjangan_makan         = intval('tunjangan_makan')
        salary.tunjangan_transport     = intval('tunjangan_transport')
        salary.tunjangan_tempat_tinggal = intval('tunjangan_tempat_tinggal')
        salary.tunjangan_alat_tipe     = request.POST.get('tunjangan_alat_tipe', '')
        salary.tunjangan_alat_rate     = intval('tunjangan_alat_rate')
        salary.bonus_tahunan           = intval('bonus_tahunan')
        salary.thr                     = intval('thr')
        salary.save()
        messages.success(request, f'Data gaji {employee.nama} berhasil disimpan.')
        return redirect('employee_detail', pk=pk)

    return render(request, 'employees/salary_form.html', {
        'employee': employee,
        'salary'  : salary,
    })


@login_required
@hr_required
def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.status = 'Tidak Aktif'
        employee.save()
        messages.success(request, f'Karyawan {employee.nama} berhasil dinonaktifkan.')
    return redirect('employee_list')


@login_required
@hr_required
def export_karyawan(request):
    from .export_import import export_karyawan_excel
    company = getattr(request, 'company', None)
    qs = Employee.objects.select_related('department', 'jabatan', 'provinsi', 'kabupaten', 'perusahaan', 'point_of_hire', 'job_site')
    if company:
        qs = qs.filter(company=company)
    if request.GET.get('status'): qs = qs.filter(status=request.GET['status'])
    if request.GET.get('dept'):   qs = qs.filter(department_id=request.GET['dept'])
    return export_karyawan_excel(qs)


@login_required
@hr_required
def download_template(request):
    from .export_import import download_template_import
    company = getattr(request, 'company', None)
    return download_template_import(company=company)


@login_required
@hr_required
def import_karyawan(request):
    from apps.core.models import Company
    is_developer = getattr(request, 'is_developer', False)
    companies    = Company.objects.filter(status='aktif').order_by('nama') if is_developer else None

    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Pilih file Excel terlebih dahulu.')
            return render(request, 'employees/employee_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        file = request.FILES['file']
        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Format file harus .xlsx atau .xls')
            return render(request, 'employees/employee_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        from .export_import import import_karyawan_excel
        company = getattr(request, 'company', None)

        if is_developer:
            company_id = request.POST.get('company_id')
            if not company_id:
                messages.error(request, 'Pilih Company tujuan import terlebih dahulu.')
                return render(request, 'employees/employee_import.html', {
                    'is_developer': is_developer, 'companies': companies,
                })
            try:
                company = Company.objects.get(pk=company_id)
            except Company.DoesNotExist:
                messages.error(request, 'Company tidak ditemukan.')
                return render(request, 'employees/employee_import.html', {
                    'is_developer': is_developer, 'companies': companies,
                })

        if not company:
            messages.error(request, 'Company tidak terdeteksi. Hubungi Developer.')
            return render(request, 'employees/employee_import.html', {
                'is_developer': is_developer, 'companies': companies,
            })

        success, errors = import_karyawan_excel(file, company)

        if success:
            messages.success(request, f'{success} data karyawan berhasil diimport ke {company.nama}.')

        for err in errors:
            baris  = err.get('baris', '-')
            nik    = err.get('nik', '-') or '-'
            nama   = err.get('nama', '-') or '-'
            alasan = err.get('alasan', '')
            messages.warning(request, f'Baris {baris} | NIK: {nik} | {nama} → {alasan}')

        return redirect('employee_import')

    return render(request, 'employees/employee_import.html', {
        'is_developer': is_developer,
        'companies':    companies,
    })

# ── Manajemen Akun Karyawan (Portal Login) ───────────────────────────────────

@login_required
@hr_required
def employee_accounts(request):
    """Daftar karyawan + status akun portal mereka + log perubahan biodata."""
    from apps.portal.models import BiodataChangeLog
    company   = getattr(request, 'company', None)
    employees = Employee.objects.filter(status='Aktif').select_related(
        'user', 'department', 'jabatan'
    ).order_by('department__nama', 'nama')
    if company:
        employees = employees.filter(company=company)
    logs = BiodataChangeLog.objects.select_related(
        'employee', 'user'
    ).order_by('-waktu')[:100]
    if company:
        logs = BiodataChangeLog.objects.filter(
            employee__company=company
        ).select_related('employee', 'user').order_by('-waktu')[:100]
    return render(request, 'employees/accounts.html', {
        'employees': employees,
        'biodata_logs': logs,
    })


@login_required
@hr_required
def employee_account_create(request, pk):
    """Buat/reset akun portal untuk karyawan."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    emp = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            username = emp.nik
            password = request.POST.get('password') or emp.nik
            if User.objects.filter(username=username).exclude(pk=emp.user_id).exists():
                messages.error(request, f'Username {username} sudah dipakai akun lain.')
                return redirect('employee_accounts')
            if emp.user:
                # Reset password
                emp.user.set_password(password)
                emp.user.save()
                messages.success(request, f'Password akun {emp.nama} berhasil direset.')
            else:
                # Buat akun baru
                user = User.objects.create_user(
                    username=username, password=password,
                    first_name=emp.nama.split()[0],
                    last_name=' '.join(emp.nama.split()[1:]) if len(emp.nama.split()) > 1 else '',
                )
                emp.user = user
                emp.save(update_fields=['user'])
                messages.success(request, f'Akun portal {emp.nama} berhasil dibuat. Username: {username}, Password: {password}')

        elif action == 'revoke':
            if emp.user:
                user = emp.user
                emp.user = None
                emp.save(update_fields=['user'])
                user.delete()
                messages.warning(request, f'Akun portal {emp.nama} telah dihapus.')

    return redirect('employee_accounts')


@login_required
@hr_required
def employee_account_bulk_create(request):
    """Buat akun sekaligus untuk semua karyawan aktif yang belum punya akun."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if request.method == 'POST':
        company   = getattr(request, 'company', None)
        employees = Employee.objects.filter(status='Aktif', user__isnull=True)
        if company:
            employees = employees.filter(company=company)
        created = 0
        for emp in employees:
            if not emp.nik:
                continue
            if User.objects.filter(username=emp.nik).exists():
                continue
            user = User.objects.create_user(
                username=emp.nik,
                password=emp.nik,
                first_name=emp.nama.split()[0] if emp.nama else emp.nik,
                last_name=' '.join(emp.nama.split()[1:]) if emp.nama and len(emp.nama.split()) > 1 else '',
                company=getattr(emp, 'company', None),
                role='employee',
            )
            emp.user = user
            emp.save(update_fields=['user'])
            created += 1
        messages.success(request, f'{created} akun berhasil dibuat. Password default = NIK masing-masing.')
    return redirect('employee_accounts')


# ══════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE DEVICE — Anti-Fraud Portal
# ══════════════════════════════════════════════════════════════════════════════

@login_required
@hr_required
def employee_add_device(request, pk):
    """Daftarkan perangkat (MAC address) untuk karyawan — dari halaman employee_detail."""
    from .models import Employee, EmployeeDevice
    from django.contrib import messages
    from django.shortcuts import get_object_or_404

    emp = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        mac = request.POST.get('mac_address', '').strip().upper()
        nama = request.POST.get('nama_perangkat', '').strip()
        platform = request.POST.get('platform', '').strip()
        catatan = request.POST.get('catatan', '').strip()

        if not mac:
            messages.error(request, 'MAC Address tidak boleh kosong.')
            return redirect('employee_detail', pk=pk)

        obj, created = EmployeeDevice.objects.get_or_create(
            employee=emp,
            mac_address=mac,
            defaults={
                'nama_perangkat': nama,
                'platform': platform,
                'catatan': catatan,
                'terdaftar_oleh': request.user.get_full_name() or request.user.username,
                'aktif': True,
            }
        )
        if created:
            messages.success(request, f'Perangkat {mac} berhasil didaftarkan untuk {emp.nama}.')
        else:
            if not obj.aktif:
                obj.aktif = True
                obj.save(update_fields=['aktif'])
                messages.success(request, f'Perangkat {mac} diaktifkan kembali.')
            else:
                messages.info(request, f'Perangkat {mac} sudah terdaftar untuk karyawan ini.')

    return redirect('employee_detail', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINT — dipakai job_library_detail.html & orgchart_detail.html
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def api_jabatan_by_dept(request):
    """
    GET /employees/api/jabatan/?dept=<department_id>
    Kembalikan JSON list jabatan aktif untuk departemen tertentu.
    Kalau dept kosong, kembalikan semua jabatan aktif di company.
    Dipakai untuk cascade dropdown Departemen → Jabatan di form karyawan.
    """
    from django.http import JsonResponse
    company = getattr(request, 'company', None)
    dept_id = request.GET.get('dept', '').strip()

    qs = Position.objects.filter(aktif=True)
    if company:
        qs = qs.filter(company=company)
    if dept_id:
        qs = qs.filter(department_id=dept_id)

    data = [{'id': p.id, 'nama': p.nama} for p in qs.order_by('nama')]
    return JsonResponse({'jabatan': data})


@login_required
def api_employees(request):
    """
    GET /employees/api/?jabatan=<pk>
    Kembalikan JSON list karyawan aktif untuk jabatan tertentu.
    Dipakai di job_library_detail.html dan orgchart detail panel.
    """
    from django.http import JsonResponse
    company    = getattr(request, 'company', None)
    jabatan_id = request.GET.get('jabatan')
    dept_id    = request.GET.get('department')

    qs = Employee.objects.filter(status='Aktif').select_related('jabatan', 'department')
    if company:
        qs = qs.filter(company=company)
    if jabatan_id:
        qs = qs.filter(jabatan_id=jabatan_id)
    if dept_id:
        qs = qs.filter(department_id=dept_id)

    total = qs.count()
    data  = [
        {'id': e.id, 'nama': e.nama, 'nik': e.nik,
         'jabatan': e.jabatan.nama if e.jabatan else '',
         'department': e.department.nama if e.department else ''}
        for e in qs[:10]
    ]
    return JsonResponse({'employees': data, 'total': total})
