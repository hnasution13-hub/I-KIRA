from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import date, datetime, time
from decimal import Decimal

from apps.attendance.models import Attendance
from apps.employees.models import Employee
from apps.portal.models import BiodataChangeLog


def portal_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('portal_login')
        # Superuser bypass — tidak perlu punya data karyawan
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            emp = request.user.employee
            if emp.status != 'Aktif':
                logout(request)
                messages.error(request, 'Akun Anda tidak aktif. Hubungi HR.')
                return redirect('portal_login')
        except Exception:
            logout(request)
            messages.error(request, 'Akun tidak terhubung ke data karyawan. Hubungi HR.')
            return redirect('portal_login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _validate_device_mac(emp, mac_address, user_agent=''):
    """
    Cek apakah MAC address perangkat sudah terdaftar untuk karyawan ini.
    Return (device_obj_or_None, is_known: bool, flag_reason: str)
    """
    from apps.employees.models import EmployeeDevice
    if not mac_address:
        return None, False, 'MAC address tidak tersedia dari perangkat'
    try:
        device = EmployeeDevice.objects.get(employee=emp, mac_address=mac_address.upper(), aktif=True)
        # Update last_seen
        device.last_seen = timezone.now()
        device.user_agent = user_agent
        device.save(update_fields=['last_seen', 'user_agent'])
        return device, True, ''
    except EmployeeDevice.DoesNotExist:
        return None, False, f'Perangkat MAC {mac_address} belum terdaftar untuk karyawan ini'


def _save_checkin_log(emp, device, mac_address, lat, lng, accuracy, tipe, request,
                      device_known, gps_valid, flag=False, flag_reason='',
                      jarak_meter=None, dalam_radius=None, ditolak=False, alasan_tolak=''):
    """Simpan log check-in ke PortalCheckInLog."""
    from apps.employees.models import PortalCheckInLog
    try:
        PortalCheckInLog.objects.create(
            employee=emp,
            device=device,
            mac_address=mac_address or '',
            latitude=lat or None,
            longitude=lng or None,
            akurasi_gps=accuracy or None,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            tipe=tipe,
            device_dikenal=device_known,
            gps_valid=gps_valid,
            flagged=flag,
            catatan_flag=flag_reason,
            jarak_meter=jarak_meter,
            dalam_radius=dalam_radius,
            ditolak=ditolak,
            alasan_tolak=alasan_tolak,
        )
    except Exception:
        pass  # Log gagal tidak boleh hentikan proses checkin


def portal_login(request):
    if request.user.is_authenticated:
        return redirect('portal_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        tanggal_lahir_input = request.POST.get('tanggal_lahir', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            # Superuser/staff: skip semua validasi, langsung masuk
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('portal_dashboard')
            try:
                emp = user.employee
                if emp.status != 'Aktif':
                    messages.error(request, 'Akun tidak aktif. Hubungi HR.')
                    return render(request, 'portal/login.html')
                if not emp.tanggal_lahir or str(emp.tanggal_lahir) != tanggal_lahir_input:
                    messages.error(request, 'Tanggal lahir tidak sesuai.')
                    return render(request, 'portal/login.html')
            except Exception:
                messages.error(request, 'Akun tidak terhubung ke data karyawan. Hubungi HR.')
                return render(request, 'portal/login.html')
            login(request, user)
            return redirect('portal_dashboard')
        messages.error(request, 'NIK atau password salah.')
    return render(request, 'portal/login.html')


@login_required
def portal_qa_access(request):
    """Akses portal langsung untuk superuser/developer — bypass login portal."""
    if not request.user.is_superuser:
        messages.error(request, 'Akses ditolak.')
        return redirect('dashboard')
    return redirect('portal_dashboard')


@portal_required
def portal_profile(request):
    """Profile karyawan — lihat & edit biodata pribadi."""
    # QA mode untuk superuser
    if request.user.is_superuser:
        return render(request, 'portal/profile.html', {
            'emp': None, 'logs': [], 'qa_mode': True,
        })

    emp = request.user.employee

    # Field yang boleh diedit beserta labelnya
    EDITABLE_FIELDS = [
        ('nama',         'Nama Lengkap'),
        ('no_hp',        'No. HP'),
        ('email',        'Email'),
        ('alamat',       'Alamat'),
        ('rt',           'RT'),
        ('rw',           'RW'),
        ('kode_pos',     'Kode Pos'),
        ('agama',        'Agama'),
        ('status_nikah', 'Status Nikah'),
        ('golongan_darah','Golongan Darah'),
        ('pendidikan',   'Pendidikan'),
        ('jumlah_anak',  'Jumlah Anak'),
        ('nama_darurat', 'Nama Kontak Darurat'),
        ('hub_darurat',  'Hubungan Kontak Darurat'),
        ('hp_darurat',   'No. HP Kontak Darurat'),
    ]

    if request.method == 'POST':
        changed = False
        for field, label in EDITABLE_FIELDS:
            nilai_lama = str(getattr(emp, field, '') or '')
            nilai_baru = request.POST.get(field, '').strip()
            if nilai_baru != nilai_lama:
                BiodataChangeLog.objects.create(
                    employee=emp,
                    user=request.user,
                    field_name=field,
                    label=label,
                    nilai_lama=nilai_lama,
                    nilai_baru=nilai_baru,
                )
                setattr(emp, field, nilai_baru)
                changed = True
        if changed:
            emp.save()
            messages.success(request, 'Biodata berhasil diperbarui.')
        else:
            messages.info(request, 'Tidak ada perubahan.')
        return redirect('portal_profile')

    from apps.employees.models import Employee as EmpModel

    # KPI
    from apps.performance.models import PenilaianKaryawan, Review360Session
    penilaian_list = PenilaianKaryawan.objects.filter(
        employee=emp
    ).select_related('periode').order_by('-periode__tanggal_mulai')[:5]
    review360_list = Review360Session.objects.filter(
        employee=emp, status='selesai'
    ).select_related('periode').order_by('-created_at')[:3]

    # Kontrak
    from apps.contracts.models import Contract
    kontrak_list = Contract.objects.filter(employee=emp).order_by('-tanggal_mulai')

    # Surat Peringatan
    from apps.industrial.models import SuratPeringatan, Violation
    sp_list         = SuratPeringatan.objects.filter(employee=emp).order_by('-tanggal_sp')
    pelanggaran_list = Violation.objects.filter(employee=emp).order_by('-tanggal_kejadian')

    # Hasil Psikotes
    from apps.advanced_psychotest.models import AdvResult, TEST_TYPE_CHOICES
    psikotes_list = AdvResult.objects.filter(
        employee=emp
    ).select_related('session').order_by('-created_at')

    return render(request, 'portal/profile.html', {
        'emp'                   : emp,
        'agama_choices'         : EmpModel.AGAMA_CHOICES,
        'status_nikah_choices'  : EmpModel.STATUS_NIKAH_CHOICES,
        'golongan_darah_choices': EmpModel.GOLONGAN_DARAH_CHOICES,
        'pendidikan_choices'    : EmpModel.PENDIDIKAN_CHOICES,
        'penilaian_list'        : penilaian_list,
        'review360_list'        : review360_list,
        'kontrak_list'          : kontrak_list,
        'sp_list'               : sp_list,
        'pelanggaran_list'      : pelanggaran_list,
        'psikotes_list'         : psikotes_list,
        'test_type_labels'      : dict(TEST_TYPE_CHOICES),
    })


def portal_logout(request):
    logout(request)
    return redirect('portal_login')


def _hitung_keterlambatan(jam_masuk):
    jam_normal = time(8, 0)
    if jam_masuk > jam_normal:
        delta = datetime.combine(date.today(), jam_masuk) - datetime.combine(date.today(), jam_normal)
        return int(delta.total_seconds() // 60)
    return 0


def _hitung_lembur(jam_masuk, jam_keluar):
    delta = datetime.combine(date.today(), jam_keluar) - datetime.combine(date.today(), jam_masuk)
    total_jam = delta.total_seconds() / 3600
    jam_efektif = total_jam - 1
    lembur = max(0, jam_efektif - 8)
    return round(Decimal(str(lembur)), 1)


@portal_required
def portal_dashboard(request):
    # Superuser QA — tidak punya employee, gunakan dummy context
    if request.user.is_superuser:
        try:
            emp = request.user.employee
        except Exception:
            return render(request, 'portal/dashboard.html', {
                'emp': None, 'today': date.today(), 'now': timezone.localtime(),
                'att_today': None, 'can_checkin': False, 'can_checkout': False,
                'month_records': [], 'total_hadir': 0, 'total_izin': 0,
                'total_absen': 0, 'total_lembur': 0, 'total_telat': 0,
                'qa_mode': True,
            })
    emp   = request.user.employee
    today = date.today()
    now   = timezone.localtime()

    att_today = Attendance.objects.filter(employee=emp, tanggal=today).first()
    can_checkin  = not att_today or (att_today and not att_today.check_in)
    can_checkout = bool(att_today and att_today.check_in and not att_today.check_out)

    month_records = Attendance.objects.filter(
        employee=emp, tanggal__month=today.month, tanggal__year=today.year
    ).order_by('-tanggal')

    return render(request, 'portal/dashboard.html', {
        'emp': emp, 'today': today, 'now': now,
        'att_today': att_today,
        'can_checkin': can_checkin, 'can_checkout': can_checkout,
        'month_records': month_records[:10],
        'total_hadir':  month_records.filter(status='Hadir').count(),
        'total_izin':   month_records.filter(status__in=['Izin','Sakit','Cuti']).count(),
        'total_absen':  month_records.filter(status='Tidak Hadir').count(),
        'total_lembur': sum(float(r.lembur_jam or 0) for r in month_records),
        'total_telat':  sum(r.keterlambatan or 0 for r in month_records),
    })


@portal_required
def portal_checkin(request):
    if request.user.is_superuser:
        return redirect('portal_dashboard')
    if request.method != 'POST':
        return redirect('portal_dashboard')
    emp   = request.user.employee
    today = date.today()
    now   = timezone.localtime()

    # ── Anti-Fraud: ambil data GPS + MAC dari POST ──────────────────────────
    mac_address  = request.POST.get('mac_address', '').strip().upper()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw= request.POST.get('longitude', '').strip()
    accuracy_raw = request.POST.get('gps_accuracy', '').strip()
    gps_denied   = request.POST.get('gps_denied', '0') == '1'
    tipe_action  = 'checkin'

    # Parse GPS
    try:
        latitude  = float(latitude_raw)  if latitude_raw  else None
        longitude = float(longitude_raw) if longitude_raw else None
        accuracy  = float(accuracy_raw)  if accuracy_raw  else None
    except ValueError:
        latitude = longitude = accuracy = None

    gps_valid = (latitude is not None and longitude is not None and not gps_denied)

    # ── Validasi Radius Geofencing ──────────────────────────────────────────
    from utils.geofencing import validasi_radius
    geo = validasi_radius(emp, latitude, longitude)

    if not geo['valid']:
        # Simpan log penolakan sebagai bukti
        device, device_known, mac_flag_reason = _validate_device_mac(
            emp, mac_address, request.META.get('HTTP_USER_AGENT', '')
        )
        _save_checkin_log(
            emp=emp, device=device, mac_address=mac_address,
            lat=latitude, lng=longitude, accuracy=accuracy,
            tipe='checkin', request=request,
            device_known=False, gps_valid=gps_valid,
            flag=True, flag_reason=geo['pesan_hr'],
            jarak_meter=geo['jarak_meter'],
            dalam_radius=False,
            ditolak=True,
            alasan_tolak=geo['pesan_hr'],
        )
        messages.error(request, geo['pesan'])
        return redirect('portal_dashboard')

    # Validasi MAC address
    device, device_known, mac_flag_reason = _validate_device_mac(
        emp, mac_address, request.META.get('HTTP_USER_AGENT', '')
    )

    # Flag jika perangkat tidak dikenal atau GPS tidak aktif
    flag = False
    flag_reasons = []
    if not device_known:
        flag = True
        flag_reasons.append(mac_flag_reason or 'Perangkat tidak terdaftar')
    if not gps_valid:
        flag = True
        flag_reasons.append('GPS tidak aktif atau ditolak')
    flag_reason = ' | '.join(flag_reasons)

    # Peringatan ke user jika ada flag
    if not device_known and mac_address:
        messages.warning(request, f'⚠ Perangkat ini belum terdaftar (MAC: {mac_address}). Aktivitas dicatat untuk verifikasi HR.')
    elif not mac_address:
        messages.warning(request, '⚠ Perangkat tidak dapat diidentifikasi. Hubungi HR untuk mendaftarkan perangkat Anda.')
    if not gps_valid:
        messages.warning(request, '⚠ Lokasi GPS tidak tersedia. Pastikan izin lokasi diaktifkan.')

    with transaction.atomic():
        att, created = Attendance.objects.select_for_update().get_or_create(
            employee=emp, tanggal=today,
            defaults={
                'check_in': now.time(), 'status': 'Hadir',
                'keterlambatan': _hitung_keterlambatan(now.time()),
            }
        )
        if not created:
            if att.check_in and not att.check_out:
                if now.time() <= att.check_in:
                    messages.error(request,
                        f'Jam check-out ({now.strftime("%H:%M")}) tidak boleh lebih awal dari check-in ({att.check_in.strftime("%H:%M")}).')
                    return redirect('portal_dashboard')
                else:
                    lembur = _hitung_lembur(att.check_in, now.time())
                    att.check_out  = now.time()
                    att.lembur_jam = lembur
                    att.save()
                    tipe_action = 'checkout'
                    pesan = f'Check-out berhasil pukul {now.strftime("%H:%M")}.'
                    if lembur > 0:
                        pesan += f' Lembur tercatat: {lembur} jam.'
                    messages.success(request, pesan)
            elif att.check_in and att.check_out:
                messages.info(request, 'Anda sudah check-in dan check-out hari ini.')
                return redirect('portal_dashboard')
            else:
                att.check_in = now.time()
                att.status = 'Hadir'
                att.keterlambatan = _hitung_keterlambatan(now.time())
                att.save()
                messages.success(request, f'Check-in berhasil pukul {now.strftime("%H:%M")}.')
        else:
            messages.success(request, f'Check-in berhasil pukul {now.strftime("%H:%M")}.')

    # Simpan log anti-fraud
    _save_checkin_log(
        emp=emp, device=device, mac_address=mac_address,
        lat=latitude, lng=longitude, accuracy=accuracy,
        tipe=tipe_action, request=request,
        device_known=device_known, gps_valid=gps_valid,
        flag=flag, flag_reason=flag_reason,
        jarak_meter=geo['jarak_meter'],
        dalam_radius=geo['valid'],
        ditolak=False,
        alasan_tolak='',
    )

    return redirect('portal_dashboard')


@portal_required
def portal_sync_checkin(request):
    """
    Endpoint untuk menerima sync check-in/out offline dari IndexedDB.
    Dipanggil oleh portal-offline.js saat device kembali online.
    """
    if request.user.is_superuser:
        from django.http import JsonResponse
        return JsonResponse({'status': 'skip', 'reason': 'superuser'})

    if request.method != 'POST':
        from django.http import JsonResponse
        return JsonResponse({'status': 'error', 'reason': 'method not allowed'}, status=405)

    emp   = request.user.employee
    today = date.today()
    now   = timezone.localtime()

    # Ambil waktu offline dari POST (format: HH:MM atau HH:MM:SS)
    offline_time_raw = request.POST.get('offline_time', '').strip()
    offline_type     = request.POST.get('offline_type', 'checkin').strip()

    # Parse waktu offline
    checkin_time = now.time()
    if offline_time_raw:
        try:
            from datetime import datetime as dt
            for fmt in ('%H:%M:%S', '%H:%M'):
                try:
                    checkin_time = dt.strptime(offline_time_raw, fmt).time()
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    # Ambil GPS + MAC sama seperti checkin biasa
    mac_address   = request.POST.get('mac_address', '').strip().upper()
    latitude_raw  = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    accuracy_raw  = request.POST.get('gps_accuracy', '').strip()
    gps_denied    = request.POST.get('gps_denied', '0') == '1'

    try:
        latitude  = float(latitude_raw)  if latitude_raw  else None
        longitude = float(longitude_raw) if longitude_raw else None
        accuracy  = float(accuracy_raw)  if accuracy_raw  else None
    except ValueError:
        latitude = longitude = accuracy = None

    gps_valid = (latitude is not None and longitude is not None and not gps_denied)

    # ── Validasi Radius Geofencing (offline sync tetap divalidasi) ──────────
    from utils.geofencing import validasi_radius
    geo = validasi_radius(emp, latitude, longitude)
    if not geo['valid']:
        device, device_known, _ = _validate_device_mac(
            emp, mac_address, request.META.get('HTTP_USER_AGENT', '')
        )
        _save_checkin_log(
            emp=emp, device=device, mac_address=mac_address,
            lat=latitude, lng=longitude, accuracy=accuracy,
            tipe='checkin', request=request,
            device_known=False, gps_valid=gps_valid,
            flag=True, flag_reason=geo['pesan_hr'],
            jarak_meter=geo['jarak_meter'],
            dalam_radius=False,
            ditolak=True, alasan_tolak=geo['pesan_hr'],
        )
        from django.http import JsonResponse
        return JsonResponse({
            'status': 'error',
            'reason': 'diluar_radius',
            'pesan': geo['pesan'],
            'jarak_meter': geo['jarak_meter'],
            'radius_meter': geo['radius_meter'],
        }, status=403)

    device, device_known, mac_flag_reason = _validate_device_mac(
        emp, mac_address, request.META.get('HTTP_USER_AGENT', '')
    )
    flag        = not device_known or not gps_valid
    flag_reason = ' | '.join(filter(None, [
        (mac_flag_reason or 'Perangkat tidak terdaftar') if not device_known else '',
        'GPS tidak aktif (offline mode)' if not gps_valid else '',
        'Data disimpan offline',
    ]))

    with transaction.atomic():
        att, created = Attendance.objects.select_for_update().get_or_create(
            employee=emp, tanggal=today,
            defaults={
                'check_in': checkin_time, 'status': 'Hadir',
                'keterlambatan': _hitung_keterlambatan(checkin_time),
            }
        )
        tipe_action = 'checkin'
        if not created:
            if att.check_in and not att.check_out and offline_type == 'checkout':
                lembur = _hitung_lembur(att.check_in, checkin_time)
                att.check_out  = checkin_time
                att.lembur_jam = lembur
                att.save()
                tipe_action = 'checkout'
            elif att.check_in and att.check_out:
                from django.http import JsonResponse
                return JsonResponse({'status': 'skip', 'reason': 'already done'})
            elif not att.check_in:
                att.check_in = checkin_time
                att.status   = 'Hadir'
                att.keterlambatan = _hitung_keterlambatan(checkin_time)
                att.save()

    _save_checkin_log(
        emp=emp, device=device, mac_address=mac_address,
        lat=latitude, lng=longitude, accuracy=accuracy,
        tipe=tipe_action, request=request,
        device_known=device_known, gps_valid=gps_valid,
        flag=flag, flag_reason=flag_reason,
        jarak_meter=geo['jarak_meter'],
        dalam_radius=geo['valid'],
        ditolak=False, alasan_tolak='',
    )

    from django.http import JsonResponse
    return JsonResponse({'status': 'ok', 'type': tipe_action, 'time': checkin_time.strftime('%H:%M')})


def portal_offline(request):
    """Halaman fallback saat device offline."""
    return render(request, 'portal/offline.html')


@portal_required
def portal_riwayat(request):
    if request.user.is_superuser:
        today = date.today()
        BULAN = [(1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
                 (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
                 (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember')]
        return render(request, 'portal/riwayat.html', {
            'emp': None, 'records': [], 'month': today.month, 'year': today.year,
            'bulan_choices': BULAN, 'tahun_choices': list(range(2023, today.year + 1)),
            'total_hadir': 0, 'total_izin': 0, 'total_absen': 0, 'qa_mode': True,
        })
    emp   = request.user.employee
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year', today.year))

    records = Attendance.objects.filter(
        employee=emp, tanggal__month=month, tanggal__year=year
    ).order_by('-tanggal')

    BULAN = [(1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
             (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
             (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember')]

    return render(request, 'portal/riwayat.html', {
        'emp': emp, 'records': records, 'month': month, 'year': year,
        'bulan_choices': BULAN,
        'tahun_choices': list(range(2023, today.year + 1)),
        'total_hadir': records.filter(status='Hadir').count(),
        'total_izin':  records.filter(status__in=['Izin','Sakit','Cuti']).count(),
        'total_absen': records.filter(status='Tidak Hadir').count(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  PORTAL — SLIP GAJI
# ══════════════════════════════════════════════════════════════════════════════

@portal_required
def portal_slip_gaji(request):
    if request.user.is_superuser:
        return render(request, 'portal/slip_gaji.html', {
            'emp': None, 'slips': [], 'qa_mode': True,
        })
    emp = request.user.employee
    from apps.payroll.models import PayrollDetail
    slips = PayrollDetail.objects.filter(
        employee=emp
    ).select_related('payroll').order_by('-payroll__periode')

    return render(request, 'portal/slip_gaji.html', {
        'emp': emp,
        'slips': slips,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  PORTAL — PENGAJUAN CUTI
# ══════════════════════════════════════════════════════════════════════════════

@portal_required
def portal_cuti(request):
    if request.user.is_superuser:
        TIPE_CHOICES = ['Cuti Tahunan','Cuti Sakit','Cuti Melahirkan','Izin','Cuti Khusus']
        return render(request, 'portal/cuti.html', {
            'emp': None, 'leaves': [], 'tipe_choices': TIPE_CHOICES, 'qa_mode': True,
            'approval_chain': [],
        })
    emp = request.user.employee
    from apps.attendance.models import Leave

    if request.method == 'POST':
        from apps.attendance.models import Leave
        from datetime import date as _date
        tipe = request.POST.get('tipe_cuti', 'Cuti Tahunan')
        tanggal_mulai_str   = request.POST.get('tanggal_mulai', '').strip()
        tanggal_selesai_str = request.POST.get('tanggal_selesai', '').strip()
        alasan = request.POST.get('alasan', '').strip()  # FIX BUG-2: field benar adalah alasan
        if tanggal_mulai_str and tanggal_selesai_str:
            try:
                tgl_mulai   = _date.fromisoformat(tanggal_mulai_str)
                tgl_selesai = _date.fromisoformat(tanggal_selesai_str)
                if tgl_selesai < tgl_mulai:
                    messages.error(request, 'Tanggal selesai tidak boleh sebelum tanggal mulai.')
                    return redirect('portal_cuti')
                jumlah_hari = (tgl_selesai - tgl_mulai).days + 1  # FIX BUG-2: hitung jumlah_hari
            except ValueError:
                messages.error(request, 'Format tanggal tidak valid.')
                return redirect('portal_cuti')
            leave = Leave.objects.create(
                employee=emp,
                tipe_cuti=tipe,
                tanggal_mulai=tgl_mulai,
                tanggal_selesai=tgl_selesai,
                jumlah_hari=jumlah_hari,  # FIX BUG-2: wajib diisi
                alasan=alasan or '-',     # FIX BUG-2: field benar adalah alasan (required)
                status='Pending',
            )
            # Kirim notifikasi ke approver pertama via ApprovalEngine
            try:
                from utils.approval_engine import ApprovalEngine
                engine = ApprovalEngine(emp.company, modul='leave', jabatan_pemohon=emp.jabatan)
                engine._send_notification(leave, request.user, action='submitted')
            except Exception:
                pass
            messages.success(request, 'Pengajuan cuti berhasil dikirim.')
            return redirect('portal_cuti')
        else:
            messages.error(request, 'Tanggal tidak boleh kosong.')

    leaves = Leave.objects.filter(employee=emp).order_by('-tanggal_mulai')[:20]
    TIPE_CHOICES = [
        'Cuti Tahunan', 'Cuti Sakit', 'Cuti Melahirkan',
        'Izin', 'Cuti Khusus',
    ]

    # Tampilkan approval chain di portal
    try:
        from utils.approval_engine import get_approval_chain_display
        approval_chain = get_approval_chain_display(emp, 'leave')
    except Exception:
        approval_chain = []

    return render(request, 'portal/cuti.html', {
        'emp': emp,
        'leaves': leaves,
        'tipe_choices': TIPE_CHOICES,
        'approval_chain': approval_chain,
    })


# ══════════════════════════════════════════════════════════════════════════════
#  PORTAL — JADWAL SHIFT
# ══════════════════════════════════════════════════════════════════════════════

@portal_required
def portal_jadwal(request):
    if request.user.is_superuser:
        today = date.today()
        BULAN = [(1,'Jan'),(2,'Feb'),(3,'Mar'),(4,'Apr'),(5,'Mei'),(6,'Jun'),
                 (7,'Jul'),(8,'Agt'),(9,'Sep'),(10,'Okt'),(11,'Nov'),(12,'Des')]
        return render(request, 'portal/jadwal.html', {
            'emp': None, 'assignments': [], 'month': today.month, 'year': today.year,
            'today': today, 'bulan_choices': BULAN,
            'tahun_choices': list(range(2023, today.year + 2)), 'qa_mode': True,
        })
    emp = request.user.employee
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    try:
        from apps.shifts.models import ShiftAssignment
        assignments = ShiftAssignment.objects.filter(
            employee=emp,
            tanggal__month=month,
            tanggal__year=year,
        ).select_related('shift').order_by('tanggal')
    except Exception:
        assignments = []

    BULAN = [(1,'Jan'),(2,'Feb'),(3,'Mar'),(4,'Apr'),(5,'Mei'),(6,'Jun'),
             (7,'Jul'),(8,'Agt'),(9,'Sep'),(10,'Okt'),(11,'Nov'),(12,'Des')]

    return render(request, 'portal/jadwal.html', {
        'emp': emp,
        'assignments': assignments,
        'month': month,
        'year': year,
        'today': today,
        'bulan_choices': BULAN,
        'tahun_choices': list(range(2023, today.year + 2)),
    })
