"""
apps/registration/demo_seed.py
================================
Seed data dummy untuk akun Demo.
Dipanggil saat:
  - Company baru dibuat dengan status='demo'
  - Management command `reset_demo_accounts` berjalan
"""
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import date, timedelta
import random


# ── Data dummy ────────────────────────────────────────────────────────────────

DEPARTEMEN = ['Human Resources', 'Finance', 'Operations', 'IT', 'Marketing', 'General Affairs']

JABATAN = [
    ('Manager HR',        'Manager'),
    ('Staff HR',          'Staff'),
    ('Manager Finance',   'Manager'),
    ('Staff Finance',     'Staff'),
    ('Supervisor Ops',    'Supervisor'),
    ('Staff Operasional', 'Staff'),
    ('IT Officer',        'Staff'),
    ('Marketing Officer', 'Staff'),
]

KARYAWAN = [
    ('Budi Santoso',      'L', 'Manager HR',        'Human Resources'),
    ('Siti Rahayu',       'P', 'Staff HR',           'Human Resources'),
    ('Ahmad Fauzi',       'L', 'Manager Finance',    'Finance'),
    ('Dewi Kusuma',       'P', 'Staff Finance',      'Finance'),
    ('Eko Prasetyo',      'L', 'Supervisor Ops',     'Operations'),
    ('Fitri Handayani',   'P', 'Staff Operasional',  'Operations'),
    ('Gilang Ramadhan',   'L', 'IT Officer',         'IT'),
    ('Hana Pertiwi',      'P', 'Marketing Officer',  'Marketing'),
    ('Irwan Saputra',     'L', 'Staff HR',           'Human Resources'),
    ('Juwita Lestari',    'P', 'Staff Finance',      'Finance'),
]


def _fake_nik(i):
    return f'320101{str(i).zfill(6)}'


def _fake_tgl_lahir(i):
    year = 1985 + (i % 15)
    return date(year, (i % 12) + 1, (i % 28) + 1)


def _fake_gaji(jabatan_nama):
    base = {
        'Manager':     12_000_000,
        'Supervisor':   8_000_000,
        'Senior Staff': 6_000_000,
        'Staff':        4_500_000,
    }
    for key, val in base.items():
        if key.lower() in jabatan_nama.lower():
            return val + random.randint(0, 1_000_000)
    return 4_000_000


# ── Reset: hapus semua data transaksi demo ─────────────────────────────────────

RESET_MODELS = [
    # Urutan penting: FK child dulu, baru parent
    ('apps.attendance', 'LeaveRequest'),
    ('apps.attendance', 'OvertimeRequest'),
    ('apps.attendance', 'AttendanceRecord'),
    ('apps.payroll',    'PayrollRecord'),
    ('apps.contracts',  'Contract'),
    ('apps.industrial', 'Violation'),
    ('apps.industrial', 'SuratPeringatan'),
]


def reset_demo_data(company):
    """Hapus semua data transaksi untuk company demo."""
    from django.apps import apps as django_apps

    for app_label, model_name in RESET_MODELS:
        try:
            Model = django_apps.get_model(app_label, model_name)
            deleted, _ = Model.objects.filter(
                **_company_filter(Model, company)
            ).delete()
        except Exception:
            pass  # Model tidak ada atau field berbeda — skip

    # Reset absensi bulan ini
    try:
        from apps.attendance.models import AttendanceRecord
        AttendanceRecord.objects.filter(employee__company=company).delete()
    except Exception:
        pass


def _company_filter(Model, company):
    """Deteksi field company di model."""
    field_names = [f.name for f in Model._meta.get_fields()]
    if 'company' in field_names:
        return {'company': company}
    if 'employee' in field_names:
        return {'employee__company': company}
    return {}


# ── Seed: buat data dummy segar ────────────────────────────────────────────────

def seed_demo_data(company):
    """
    Buat data dummy lengkap untuk company demo.
    Aman dipanggil berulang (idempotent untuk master data).
    """
    from apps.core.models import Department, Position
    from apps.employees.models import Employee, PointOfHire, JobSite

    # 1. Departemen
    dept_map = {}
    for nama in DEPARTEMEN:
        dept, _ = Department.objects.get_or_create(
            company=company, nama=nama,
            defaults={'aktif': True}
        )
        dept_map[nama] = dept

    # 2. Point of Hire & Job Site
    poh, _ = PointOfHire.objects.get_or_create(
        company=company, nama='Jakarta',
        defaults={'aktif': True}
    )
    site, _ = JobSite.objects.get_or_create(
        company=company, nama='Kantor Pusat',
        defaults={'aktif': True}
    )

    # 3. Jabatan
    pos_map = {}
    for nama, level in JABATAN:
        dept_name = _guess_dept(nama)
        pos, _ = Position.objects.get_or_create(
            company=company, nama=nama,
            defaults={
                'level':  level,
                'aktif':  True,
                'department': dept_map.get(dept_name),
            }
        )
        pos_map[nama] = pos

    # 4. Karyawan dummy (hapus dulu yg lama, buat ulang)
    Employee.objects.filter(company=company).delete()
    for i, (nama, jk, jabatan_nama, dept_nama) in enumerate(KARYAWAN, start=1):
        jabatan = pos_map.get(jabatan_nama)
        dept    = dept_map.get(dept_nama)
        tgl_lahir = _fake_tgl_lahir(i)
        tgl_masuk = date.today() - timedelta(days=random.randint(180, 900))
        Employee.objects.create(
            company       = company,
            nik           = _fake_nik(i),
            nama          = nama,
            jenis_kelamin = jk,
            tanggal_lahir = tgl_lahir,
            tanggal_masuk = tgl_masuk,
            jabatan       = jabatan,
            department    = dept,
            point_of_hire = poh,
            job_site      = site,
            status        = 'Aktif',
            gaji_pokok    = _fake_gaji(jabatan_nama),
        )

    # 5. Seed absensi bulan ini
    _seed_absensi(company)

    # 6. Update last_demo_reset
    company.last_demo_reset = timezone.now()
    company.save(update_fields=['last_demo_reset'])


def _guess_dept(jabatan_nama):
    mapping = {
        'HR': 'Human Resources',
        'Finance': 'Finance',
        'Ops': 'Operations',
        'IT': 'IT',
        'Marketing': 'Marketing',
    }
    for key, dept in mapping.items():
        if key.lower() in jabatan_nama.lower():
            return dept
    return 'General Affairs'


def _seed_absensi(company):
    """Seed absensi hadir untuk semua karyawan demo di bulan ini."""
    try:
        from apps.attendance.models import AttendanceRecord
        from apps.employees.models import Employee

        employees = Employee.objects.filter(company=company, status='Aktif')
        today = date.today()
        # Seed dari awal bulan sampai kemarin
        start = today.replace(day=1)
        delta = (today - start).days

        records = []
        for emp in employees:
            for d in range(delta):
                day = start + timedelta(days=d)
                if day.weekday() < 5:  # Senin–Jumat
                    records.append(AttendanceRecord(
                        employee   = emp,
                        tanggal    = day,
                        jam_masuk  = '08:00',
                        jam_keluar = '17:00',
                        status     = 'Hadir',
                        keterangan = 'Demo data',
                    ))
        AttendanceRecord.objects.bulk_create(records, ignore_conflicts=True)
    except Exception:
        pass  # AttendanceRecord mungkin field-nya berbeda — skip


# ── Entry point utama ──────────────────────────────────────────────────────────

def full_reset_and_seed(company):
    """Reset + seed ulang. Dipanggil dari management command."""
    reset_demo_data(company)
    seed_demo_data(company)
