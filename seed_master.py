"""
seed_combined.py — HRIS SmartDesk
Script interaktif gabungan untuk seed data master + generate absensi.

Menu:
  1. Tambah Company / Tenant
  2. Tambah Department
  3. Tambah Jabatan
  4. Generate Absensi  ← pilih company & rentang tanggal
  5. Lihat semua data
  6. Keluar

Cara pakai:
  python seed_combined.py

Atau langsung ke menu tertentu:
  python seed_combined.py --company
  python seed_combined.py --department
  python seed_combined.py --jabatan
  python seed_combined.py --absensi
  python seed_combined.py --list
"""

import os
import sys
import django
import re

# Fix encoding Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Setup Django ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_project.settings')
django.setup()

from apps.core.models import Company, Department, Position
from apps.employees.models import Employee
from apps.attendance.models import Attendance, Leave
from apps.core.models import User
from apps.assets.models import Asset, Category as AssetCategory, Depreciation
from apps.locations.models import Location
from apps.vendors.models import Vendor

import random
import calendar
from datetime import date, time, timedelta
from decimal import Decimal

# ── Warna terminal ────────────────────────────────────────────────────────────
R   = '\033[91m'
G   = '\033[92m'
Y   = '\033[93m'
B   = '\033[94m'
C   = '\033[96m'
W   = '\033[97m'
DIM = '\033[2m'
RST = '\033[0m'

def clr(text, color):
    return f'{color}{text}{RST}'

def header(title):
    print(f'\n{B}{"="*58}{RST}')
    print(f'{W}  {title}{RST}')
    print(f'{B}{"="*58}{RST}')

def info(msg):  print(f'{C}  [i] {msg}{RST}')
def ok(msg):    print(f'{G}  [OK] {msg}{RST}')
def warn(msg):  print(f'{Y}  [!] {msg}{RST}')
def err(msg):   print(f'{R}  [X] {msg}{RST}')
def dim(msg):   print(f'{DIM}  {msg}{RST}')


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UMUM
# ══════════════════════════════════════════════════════════════════════════════

def input_prompt(label, default=None):
    hint = f' [{default}]' if default else ''
    val  = input(f'{Y}  > {label}{hint}: {RST}').strip()
    return val or default or ''


def confirm(msg):
    val = input(f'{Y}  > {msg} (y/n): {RST}').strip().lower()
    return val in ('y', 'yes', 'ya')


def pilih_menu(options, title='Pilih'):
    print(f'\n{C}  {title}:{RST}')
    for i, opt in enumerate(options, 1):
        print(f'{DIM}    {i}.{RST} {opt}')
    while True:
        val = input(f'{Y}  > Pilihan (1-{len(options)}): {RST}').strip()
        if val.isdigit() and 1 <= int(val) <= len(options):
            return int(val) - 1
        err(f'Masukkan angka 1 sampai {len(options)}')


def pilih_companies(label='Target company'):
    companies = list(Company.objects.order_by('nama'))
    if not companies:
        err('Belum ada company di database. Tambah company dulu.')
        return []

    print(f'\n{C}  {label}:{RST}')
    print(f'{DIM}    0. Semua company ({len(companies)} company){RST}')
    for i, c in enumerate(companies, 1):
        status_color = G if c.status == 'aktif' else Y
        print(f'{DIM}    {i}.{RST} {c.nama} {clr(f"[{c.status}]", status_color)}')

    raw = input(f'{Y}  > Pilih nomor (0=semua, pisah koma untuk beberapa, contoh: 1,3): {RST}').strip()

    if raw == '0' or raw == '':
        return companies

    selected = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(companies):
                if companies[idx] not in selected:
                    selected.append(companies[idx])
    return selected


def input_bulk(label):
    print(f'\n{C}  {label}{RST}')
    print(f'{DIM}  Ketik satu per baris, atau paste sekaligus (pisah koma/baris).{RST}')
    print(f'{DIM}  Ketik SELESAI atau tekan Enter kosong 2x untuk lanjut.{RST}\n')

    lines       = []
    empty_count = 0

    while True:
        val = input(f'{Y}  > {RST}').strip()
        if val.upper() == 'SELESAI' or val == '':
            empty_count += 1
            if empty_count >= 2 or val.upper() == 'SELESAI':
                break
        else:
            empty_count = 0
            lines.append(val)

    return [l for l in lines if l]


def input_tanggal(label, default=None):
    """
    Input tanggal format DD-MM-YYYY.
    Jika kosong dan ada default, pakai default.
    """
    default_str = default.strftime('%d-%m-%Y') if default else None
    while True:
        raw = input_prompt(label + ' (DD-MM-YYYY)', default=default_str)
        if not raw:
            err('Tanggal tidak boleh kosong.')
            continue
        try:
            parts = raw.strip().split('-')
            if len(parts) != 3:
                raise ValueError
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
        except (ValueError, IndexError):
            err(f'Format salah: "{raw}". Gunakan DD-MM-YYYY, contoh: 01-01-2025')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 1 — TAMBAH COMPANY
# ══════════════════════════════════════════════════════════════════════════════

def menu_tambah_company():
    header('TAMBAH COMPANY / TENANT')

    existing = Company.objects.order_by('nama')
    if existing.exists():
        info(f'Company yang sudah ada ({existing.count()}):')
        for c in existing:
            dim(f'  • {c.nama} [{c.slug}] — {c.status}')

    print()
    mode = pilih_menu(
        ['Tambah satu company', 'Tambah beberapa sekaligus (bulk)'],
        title='Mode input'
    )

    if mode == 0:
        _input_satu_company()
    else:
        _input_bulk_company()


def _input_satu_company():
    print()
    nama = input_prompt('Nama perusahaan')
    if not nama:
        err('Nama tidak boleh kosong.')
        return

    singkatan  = input_prompt('Singkatan (opsional)')
    slug_default = re.sub(r'[^a-z0-9-]', '',
                          nama.lower().replace(' ', '-').replace('.', '').replace(',', ''))[:80]
    slug     = input_prompt('Slug (URL identifier)', default=slug_default)
    status   = pilih_menu(['aktif', 'trial', 'suspend', 'nonaktif'], title='Status')
    status_val = ['aktif', 'trial', 'suspend', 'nonaktif'][status]
    npwp     = input_prompt('NPWP (opsional)')
    alamat   = input_prompt('Alamat (opsional)')
    no_telp  = input_prompt('No. Telepon (opsional)')
    email    = input_prompt('Email (opsional)')

    if Company.objects.filter(slug=slug).exists():
        err(f'Slug "{slug}" sudah digunakan.')
        slug = input_prompt('Slug baru')

    try:
        c = Company.objects.create(
            nama=nama, singkatan=singkatan, slug=slug,
            status=status_val, npwp=npwp, alamat=alamat,
            no_telp=no_telp, email=email,
        )
        ok(f'Company "{c.nama}" berhasil dibuat (ID: {c.pk}, slug: {c.slug})')
    except Exception as e:
        err(f'Gagal: {e}')


def _input_bulk_company():
    print()
    info('Format: NamaPerusahaan, singkatan, slug (singkatan & slug opsional)')
    info('Contoh: PT Maju Jaya, MJ, pt-maju-jaya')
    info('        PT Sejahtera, SEJ')
    print()

    lines = input_bulk('Daftar company')
    if not lines:
        warn('Tidak ada data diinput.')
        return

    created = skipped = 0
    for line in lines:
        parts = [p.strip() for p in line.split(',')]
        nama  = parts[0] if len(parts) > 0 else ''
        singk = parts[1] if len(parts) > 1 else ''
        slug  = parts[2] if len(parts) > 2 else ''
        if not nama:
            continue
        if not slug:
            slug = re.sub(r'[^a-z0-9-]',
                          '', nama.lower().replace(' ', '-').replace('.', ''))[:80]
        base_slug = slug
        counter   = 1
        while Company.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        try:
            Company.objects.create(nama=nama, singkatan=singk, slug=slug, status='aktif')
            ok(f'"{nama}" > slug: {slug}')
            created += 1
        except Exception as e:
            err(f'"{nama}" gagal: {e}')
            skipped += 1

    print()
    info(f'Total: {created} berhasil, {skipped} gagal.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 2 — TAMBAH DEPARTMENT
# ══════════════════════════════════════════════════════════════════════════════

def menu_tambah_department():
    header('TAMBAH DEPARTMENT')

    targets = pilih_companies('Apply department ke company')
    if not targets:
        return

    info(f'Target: {", ".join(c.nama for c in targets)}')

    mode = pilih_menu(
        ['Input satu per satu', 'Bulk (list sekaligus)'],
        title='Mode input'
    )

    if mode == 0:
        departments = []
        print()
        info('Ketik nama department, Enter kosong untuk selesai.')
        while True:
            nama = input_prompt('Nama department (Enter=selesai)')
            if not nama:
                break
            kode = input_prompt('  Kode (opsional, contoh: HRD, FIN)')
            departments.append({'nama': nama, 'kode': kode})
    else:
        print()
        info('Format: NamaDepartment, kode (kode opsional)')
        info('Contoh: Human Resources, HRD')
        info('        Finance & Accounting, FIN')
        lines = input_bulk('Daftar department')
        departments = []
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            nama  = parts[0] if parts else ''
            kode  = parts[1] if len(parts) > 1 else ''
            if nama:
                departments.append({'nama': nama, 'kode': kode})

    if not departments:
        warn('Tidak ada department diinput.')
        return

    print()
    info(f'Akan tambah {len(departments)} department ke {len(targets)} company:')
    for d in departments:
        kode_str = f' ({d["kode"]})' if d['kode'] else ''
        dim(f'  • {d["nama"]}{kode_str}')

    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    created = skipped = 0
    for company in targets:
        for d in departments:
            obj, is_new = Department.objects.get_or_create(
                company=company,
                nama=d['nama'],
                defaults={'kode': d['kode'], 'aktif': True}
            )
            if is_new:
                created += 1
            else:
                skipped += 1

    print()
    ok(f'{created} department berhasil ditambah, {skipped} sudah ada (skip).')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 3 — TAMBAH JABATAN
# ══════════════════════════════════════════════════════════════════════════════

LEVEL_CHOICES = [
    'Staff', 'Senior Staff', 'Supervisor',
    'Senior Supervisor', 'Manager', 'Senior Manager', 'Director'
]


def menu_tambah_jabatan():
    header('TAMBAH JABATAN / POSISI')

    targets = pilih_companies('Apply jabatan ke company')
    if not targets:
        return

    info(f'Target: {", ".join(c.nama for c in targets)}')

    sample_company = targets[0]
    depts = Department.objects.filter(company=sample_company, aktif=True).order_by('nama')
    if depts.exists():
        info(f'Department tersedia di {sample_company.nama}:')
        for i, d in enumerate(depts, 1):
            dim(f'  {i}. {d.nama}')

    mode = pilih_menu(
        ['Input satu per satu', 'Bulk (list sekaligus)'],
        title='Mode input'
    )

    if mode == 0:
        jabatans = []
        print()
        info('Ketik nama jabatan, Enter kosong untuk selesai.')
        while True:
            nama = input_prompt('Nama jabatan (Enter=selesai)')
            if not nama:
                break
            level_idx = pilih_menu(LEVEL_CHOICES, title='Level')
            level     = LEVEL_CHOICES[level_idx]
            dept_nama = input_prompt('  Department (opsional, nama department)')
            jabatans.append({'nama': nama, 'level': level, 'dept': dept_nama})
    else:
        print()
        info('Format: NamaJabatan, level, department (level & dept opsional)')
        info('Level: Staff, Senior Staff, Supervisor, Manager, Senior Manager, General Manager, Director')
        info('Contoh: Staff HRD, Staff, Human Resources')
        info('        Manager Keuangan, Manager, Finance')
        lines = input_bulk('Daftar jabatan')
        jabatans = []
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            nama  = parts[0] if parts else ''
            level = parts[1] if len(parts) > 1 else 'Staff'
            dept  = parts[2] if len(parts) > 2 else ''
            if level not in LEVEL_CHOICES:
                level = 'Staff'
            if nama:
                jabatans.append({'nama': nama, 'level': level, 'dept': dept})

    if not jabatans:
        warn('Tidak ada jabatan diinput.')
        return

    print()
    info(f'Akan tambah {len(jabatans)} jabatan ke {len(targets)} company:')
    for j in jabatans:
        dept_str = f' > {j["dept"]}' if j['dept'] else ''
        dim(f'  • {j["nama"]} [{j["level"]}]{dept_str}')

    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    created = skipped = 0
    for company in targets:
        for j in jabatans:
            dept_obj = None
            if j['dept']:
                dept_obj = Department.objects.filter(
                    company=company, nama__icontains=j['dept']
                ).first()

            obj, is_new = Position.objects.get_or_create(
                company=company,
                nama=j['nama'],
                defaults={
                    'level':      j['level'],
                    'department': dept_obj,
                    'aktif':      True,
                }
            )
            if is_new:
                created += 1
            else:
                skipped += 1

    print()
    ok(f'{created} jabatan berhasil ditambah, {skipped} sudah ada (skip).')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 4 — GENERATE ABSENSI
# ══════════════════════════════════════════════════════════════════════════════

# Libur Nasional Indonesia 2024-2026 (bisa ditambah)
LIBUR_NASIONAL = {
    # 2024
    date(2024, 1,  1):  'Tahun Baru',
    date(2024, 2,  8):  'Tahun Baru Imlek',
    date(2024, 3, 11):  'Isra Miraj',
    date(2024, 3, 22):  'Nyepi',
    date(2024, 3, 29):  'Jumat Agung',
    date(2024, 4, 10):  'Idul Fitri',
    date(2024, 4, 11):  'Idul Fitri',
    date(2024, 5,  1):  'Hari Buruh',
    date(2024, 5,  9):  'Kenaikan Isa Almasih',
    date(2024, 5, 23):  'Waisak',
    date(2024, 6,  1):  'Hari Pancasila',
    date(2024, 6, 17):  'Idul Adha',
    date(2024, 7,  7):  'Tahun Baru Islam',
    date(2024, 8, 17):  'HUT RI',
    date(2024, 9, 16):  'Maulid Nabi',
    date(2024, 12, 25): 'Natal',
    date(2024, 12, 26): 'Cuti Bersama Natal',
    # 2025
    date(2025, 1,  1):  'Tahun Baru',
    date(2025, 1, 27):  'Isra Miraj',
    date(2025, 1, 28):  'Cuti Bersama Isra Miraj',
    date(2025, 1, 29):  'Tahun Baru Imlek',
    date(2025, 3,  4):  'Nyepi',
    date(2025, 3, 31):  'Idul Fitri',
    date(2025, 4,  1):  'Idul Fitri',
    date(2025, 4,  2):  'Cuti Bersama Idul Fitri',
    date(2025, 4,  3):  'Cuti Bersama Idul Fitri',
    date(2025, 4,  4):  'Cuti Bersama Idul Fitri',
    date(2025, 4, 18):  'Jumat Agung',
    date(2025, 5,  1):  'Hari Buruh',
    date(2025, 5, 12):  'Waisak',
    date(2025, 5, 29):  'Kenaikan Isa Almasih',
    date(2025, 6,  1):  'Hari Pancasila',
    date(2025, 6,  6):  'Idul Adha',
    date(2025, 6, 27):  'Tahun Baru Islam',
    date(2025, 8, 17):  'HUT RI',
    date(2025, 9,  5):  'Maulid Nabi',
    date(2025, 12, 25): 'Natal',
    date(2025, 12, 26): 'Cuti Bersama Natal',
    # 2026
    date(2026, 1,  1):  'Tahun Baru',
    date(2026, 2, 17):  'Tahun Baru Imlek',
    date(2026, 3, 20):  'Nyepi',
    date(2026, 4,  3):  'Jumat Agung',
    date(2026, 5,  1):  'Hari Buruh',
    date(2026, 6,  1):  'Hari Pancasila',
    date(2026, 8, 17):  'HUT RI',
    date(2026, 12, 25): 'Natal',
}

# Persona absensi
PERSONA = {
    'nakal': {
        'label':             '🔴 Nakal',
        'p_hadir':           0.68,
        'p_izin':            0.07,
        'p_sakit':           0.08,
        'p_alpha':           0.17,
        'late_prob':         0.45,
        'late_menit':        (20, 120),
        'lembur_prob':       0.05,
        'cuti_prob':         0.70,
        'cuti_hari':         (1, 3),
        'pulang_cepat_prob': 0.15,
    },
    'normal': {
        'label':             '🟡 Normal',
        'p_hadir':           0.86,
        'p_izin':            0.05,
        'p_sakit':           0.05,
        'p_alpha':           0.04,
        'late_prob':         0.15,
        'late_menit':        (5, 45),
        'lembur_prob':       0.20,
        'cuti_prob':         0.45,
        'cuti_hari':         (1, 2),
        'pulang_cepat_prob': 0.05,
    },
    'rajin': {
        'label':             '🟢 Rajin',
        'p_hadir':           0.96,
        'p_izin':            0.02,
        'p_sakit':           0.02,
        'p_alpha':           0.00,
        'late_prob':         0.04,
        'late_menit':        (1, 15),
        'lembur_prob':       0.40,
        'cuti_prob':         0.30,
        'cuti_hari':         (1, 2),
        'pulang_cepat_prob': 0.01,
    },
}


def _is_workday(d):
    return d.weekday() < 5 and d not in LIBUR_NASIONAL


def _get_workdays_in_month(year, month, start_date, end_date):
    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])
    days  = []
    d = max(first, start_date)
    while d <= min(last, end_date):
        if _is_workday(d):
            days.append(d)
        d += timedelta(1)
    return days


def menu_generate_absensi():
    header('GENERATE ABSENSI')

    # ── Pilih company ────────────────────────────────────────────────────────
    targets = pilih_companies('Generate absensi untuk company')
    if not targets:
        return

    info(f'Target company: {", ".join(c.nama for c in targets)}')

    # ── Pilih rentang tanggal ────────────────────────────────────────────────
    print(f'\n{C}  Rentang tanggal absensi:{RST}')
    start_date = input_tanggal('Tanggal mulai', default=date(2025, 1, 1))
    end_date   = input_tanggal('Tanggal selesai', default=date.today())

    if start_date > end_date:
        err('Tanggal mulai tidak boleh lebih besar dari tanggal selesai.')
        return

    total_hari = (end_date - start_date).days + 1
    info(f'Rentang: {start_date.strftime("%d-%m-%Y")} s/d {end_date.strftime("%d-%m-%Y")} ({total_hari} hari)')

    # ── Cek data existing ────────────────────────────────────────────────────
    company_ids  = [c.pk for c in targets]
    emp_existing = Employee.objects.filter(company__in=company_ids, status='Aktif')
    emp_ids      = list(emp_existing.values_list('pk', flat=True))

    n_existing = Attendance.objects.filter(
        employee__in=emp_ids,
        tanggal__gte=start_date,
        tanggal__lte=end_date
    ).count()

    if n_existing > 0:
        warn(f'Ditemukan {n_existing:,} record absensi existing di rentang ini.')
        aksi = pilih_menu(
            [
                f'Hapus {n_existing:,} record lama lalu generate ulang',
                'Batalkan — jangan lakukan apa-apa',
            ],
            title='Apa yang ingin dilakukan?'
        )
        if aksi == 1:
            warn('Generate dibatalkan.')
            return
        # Hapus data lama
        n_del = Attendance.objects.filter(
            employee__in=emp_ids,
            tanggal__gte=start_date,
            tanggal__lte=end_date
        ).delete()[0]
        n_lv_del = Leave.objects.filter(
            employee__in=emp_ids,
            tanggal_mulai__gte=start_date,
            tanggal_mulai__lte=end_date
        ).delete()[0]
        ok(f'Hapus {n_del:,} absensi + {n_lv_del} leave lama.')

    # ── Ambil karyawan aktif dari company terpilih ───────────────────────────
    employees = list(
        Employee.objects.filter(company__in=company_ids, status='Aktif')
        .select_related('company', 'department', 'jabatan')
    )

    if not employees:
        err('Tidak ada karyawan aktif di company yang dipilih.')
        return

    info(f'{len(employees)} karyawan aktif ditemukan.')

    # ── Input distribusi persona ─────────────────────────────────────────────
    print(f'\n{C}  Distribusi persona karyawan:{RST}')
    info('Total harus 100. Contoh: Nakal=20, Normal=40, Rajin=40')
    while True:
        try:
            pct_nakal  = int(input_prompt('% Nakal  (sering alpha, sering telat)', default='20') or 20)
            pct_normal = int(input_prompt('% Normal (kehadiran rata-rata)',         default='40') or 40)
            pct_rajin  = int(input_prompt('% Rajin  (hampir selalu hadir, lembur)', default='40') or 40)
        except ValueError:
            err('Masukkan angka bulat.')
            continue
        if pct_nakal + pct_normal + pct_rajin != 100:
            err(f'Total = {pct_nakal + pct_normal + pct_rajin}, harus tepat 100. Coba lagi.')
            continue
        if any(v < 0 for v in [pct_nakal, pct_normal, pct_rajin]):
            err('Persentase tidak boleh negatif.')
            continue
        break

    thresh_nakal  = pct_nakal  / 100
    thresh_normal = thresh_nakal + pct_normal / 100

    # ── Konfirmasi akhir ─────────────────────────────────────────────────────
    print()
    info('Ringkasan generate:')
    dim(f'  Company  : {", ".join(c.nama for c in targets)}')
    dim(f'  Periode  : {start_date.strftime("%d-%m-%Y")} — {end_date.strftime("%d-%m-%Y")} ({total_hari} hari)')
    dim(f'  Karyawan : {len(employees)} orang')
    dim(f'  Persona  : 🔴 Nakal {pct_nakal}% | 🟡 Normal {pct_normal}% | 🟢 Rajin {pct_rajin}%')
    print()

    if not confirm('Lanjutkan generate absensi?'):
        warn('Dibatalkan.')
        return

    # ── Assign persona ───────────────────────────────────────────────────────
    random.seed(42)
    random.shuffle(employees)
    persona_map = {}
    counts = {'nakal': 0, 'normal': 0, 'rajin': 0}
    for emp in employees:
        r = random.random()
        if r < thresh_nakal:
            p = 'nakal'
        elif r < thresh_normal:
            p = 'normal'
        else:
            p = 'rajin'
        persona_map[emp.pk] = p
        counts[p] += 1

    info(f'Persona — Nakal:{counts["nakal"]}  Normal:{counts["normal"]}  Rajin:{counts["rajin"]}')

    # ── Sinkronisasi akun portal ──────────────────────────────────────────────
    print(f'\n{C}  [1] Sinkronisasi akun portal...{RST}')
    created_user = 0
    for emp in employees:
        uname = emp.nik.strip()
        if not User.objects.filter(username=uname).exists():
            try:
                u = User(username=uname, nik=uname, role='employee',
                         is_active=True, is_staff=False,
                         department=emp.department, jabatan=emp.jabatan)
                u.set_password('demo1234')
                u.save()
                emp.user = u
                emp.save(update_fields=['user'])
                created_user += 1
            except Exception:
                pass
    ok(f'{created_user} akun baru dibuat (yang sudah ada dilewati).')

    # ── Iterasi bulan ────────────────────────────────────────────────────────
    print(f'\n{C}  [2] Generate absensi...{RST}')
    months = []
    y, m = start_date.year, start_date.month
    while date(y, m, 1) <= end_date:
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1; y += 1

    att_bulk = []
    lv_bulk  = []
    persona_stats = {
        k: {'hadir': 0, 'alpha': 0, 'telat': 0, 'lembur_jam': 0.0, 'cuti': 0}
        for k in PERSONA
    }

    for emp in employees:
        pname = persona_map[emp.pk]
        p     = PERSONA[pname]
        ps    = persona_stats[pname]

        cuti_days = set()

        # Generate cuti per bulan
        for year, month in months:
            wdays = _get_workdays_in_month(year, month, start_date, end_date)
            if not wdays:
                continue
            available = [d for d in wdays if d not in cuti_days]
            if not available:
                continue

            if random.random() < p['cuti_prob'] / len(months) * 12:
                n_hari     = random.randint(*p['cuti_hari'])
                start_cuti = random.choice(available)
                cuti_range = []
                d = start_cuti
                while len(cuti_range) < n_hari and d <= end_date:
                    if _is_workday(d) and d not in cuti_days:
                        cuti_range.append(d)
                    d += timedelta(1)

                if cuti_range:
                    for cd in cuti_range:
                        cuti_days.add(cd)
                    ps['cuti'] += len(cuti_range)
                    lv_bulk.append(Leave(
                        employee=emp,
                        tipe_cuti=random.choice(
                            ['Cuti Tahunan', 'Cuti Tahunan', 'Cuti Penting']
                            if pname == 'nakal' else
                            ['Cuti Tahunan', 'Cuti Tahunan', 'Cuti Melahirkan']
                            if pname == 'rajin' else
                            ['Cuti Tahunan', 'Cuti Penting', 'Izin Khusus']
                        ),
                        tanggal_mulai=cuti_range[0],
                        tanggal_selesai=cuti_range[-1],
                        jumlah_hari=len(cuti_range),
                        alasan='Keperluan pribadi' if pname == 'nakal' else 'Cuti terencana',
                        status='Approved',
                    ))

        # Generate absensi harian
        cur = start_date
        while cur <= end_date:
            # Weekend
            if cur.weekday() >= 5:
                att_bulk.append(Attendance(
                    employee=emp, tanggal=cur,
                    status='Libur', keterangan='Akhir Pekan'))
                cur += timedelta(1)
                continue

            # Libur nasional
            if cur in LIBUR_NASIONAL:
                att_bulk.append(Attendance(
                    employee=emp, tanggal=cur,
                    status='Libur', keterangan=LIBUR_NASIONAL[cur]))
                cur += timedelta(1)
                continue

            # Cuti
            if cur in cuti_days:
                att_bulk.append(Attendance(
                    employee=emp, tanggal=cur,
                    status='Cuti', keterangan='Cuti'))
                cur += timedelta(1)
                continue

            # Hari kerja — roll dice
            r        = random.random()
            cumul    = 0

            cumul += p['p_alpha']
            if r < cumul:
                att_bulk.append(Attendance(employee=emp, tanggal=cur, status='Tidak Hadir'))
                ps['alpha'] += 1
                cur += timedelta(1)
                continue

            cumul += p['p_sakit']
            if r < cumul:
                att_bulk.append(Attendance(
                    employee=emp, tanggal=cur,
                    status='Sakit', keterangan='Sakit'))
                cur += timedelta(1)
                continue

            cumul += p['p_izin']
            if r < cumul:
                att_bulk.append(Attendance(
                    employee=emp, tanggal=cur,
                    status='Izin', keterangan='Izin pribadi'))
                cur += timedelta(1)
                continue

            # HADIR
            is_late = random.random() < p['late_prob']
            if is_late:
                mnt_late = random.randint(*p['late_menit'])
                masuk    = 8 * 60 + mnt_late
                ps['telat'] += 1
            else:
                masuk = 8 * 60 + random.randint(-15, 5)
            masuk = max(masuk, 7 * 60 + 30)

            r2 = random.random()
            if r2 < p['pulang_cepat_prob']:
                keluar = random.randint(14 * 60, 16 * 60 + 30)
                ket    = 'Izin pulang cepat'
            elif r2 < p['pulang_cepat_prob'] + p['lembur_prob']:
                keluar = 17 * 60 + random.randint(60, 240)
                ket    = 'Lembur'
            else:
                keluar = 17 * 60 + random.randint(0, 30)
                ket    = ''
            keluar = min(keluar, 23 * 60)

            ci         = time(masuk  // 60, masuk  % 60)
            co         = time(keluar // 60, keluar % 60)
            mnt_telat  = max(0, masuk - 8 * 60)
            lbr_jam    = round(max(0.0, (keluar - masuk - 60) / 60 - 8.0), 1)

            att_bulk.append(Attendance(
                employee=emp, tanggal=cur,
                check_in=ci, check_out=co,
                status='Hadir',
                keterlambatan=mnt_telat,
                lembur_jam=Decimal(str(lbr_jam)),
                keterangan=ket,
            ))
            ps['hadir'] += 1
            ps['lembur_jam'] += lbr_jam

            cur += timedelta(1)

    # ── Simpan ke DB ──────────────────────────────────────────────────────────
    print(f'  Menyimpan {len(att_bulk):,} record absensi + {len(lv_bulk)} leave...')
    Attendance.objects.bulk_create(att_bulk, batch_size=2000, ignore_conflicts=True)
    Leave.objects.bulk_create(lv_bulk, ignore_conflicts=True)

    # ── Ringkasan ─────────────────────────────────────────────────────────────
    print(f'\n{B}{"─"*58}{RST}')
    print(f'  {W}{"Persona":<12} {"Karyawan":>9} {"Hadir":>8} {"Alpha":>7} {"Telat":>7} {"Lembur":>10} {"Cuti":>6}{RST}')
    print(f'{B}{"─"*58}{RST}')
    for pname, ps in persona_stats.items():
        print(f'  {PERSONA[pname]["label"]:<12} {counts[pname]:>9} '
              f'{ps["hadir"]:>8,} {ps["alpha"]:>7,} {ps["telat"]:>7,} '
              f'{ps["lembur_jam"]:>9.1f}j {ps["cuti"]:>6}')
    print(f'{B}{"─"*58}{RST}')

    stat_all = {
        s: sum(1 for a in att_bulk if a.status == s)
        for s in ['Hadir', 'Sakit', 'Izin', 'Cuti', 'Tidak Hadir', 'Libur']
    }
    total_lembur = sum(ps['lembur_jam'] for ps in persona_stats.values())

    print()
    ok(f'Generate selesai!')
    info(f'Periode   : {start_date.strftime("%d-%m-%Y")} s/d {end_date.strftime("%d-%m-%Y")}')
    info(f'Karyawan  : {len(employees)} orang')
    info(f'Total rec : {len(att_bulk):,}')
    info(f'Hadir:{stat_all["Hadir"]:,}  Sakit:{stat_all["Sakit"]}  '
         f'Izin:{stat_all["Izin"]}  Cuti:{stat_all["Cuti"]}  '
         f'Alpha:{stat_all["Tidak Hadir"]}  Libur:{stat_all["Libur"]:,}')
    info(f'Total jam lembur: {total_lembur:,.1f} jam')
    print()
    dim('  Login portal : http://localhost:8000/karyawan/')
    dim('  Username = NIK karyawan | Password = demo1234')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 5 — GENERATE KARYAWAN DUMMY
# ══════════════════════════════════════════════════════════════════════════════

# Pool nama dummy Indonesia
_NAMA_DEPAN_L = [
    'Ahmad', 'Muhammad', 'Rizky', 'Fajar', 'Dimas', 'Andi', 'Budi', 'Hendra',
    'Dani', 'Agus', 'Wahyu', 'Bayu', 'Yoga', 'Arif', 'Gilang', 'Iwan',
    'Joko', 'Kevin', 'Lutfi', 'Nanda', 'Rafi', 'Satria', 'Toni', 'Vino',
    'Aditya', 'Bagus', 'Candra', 'Dedy', 'Feri', 'Gunawan', 'Hadi', 'Imam',
    'Yusuf', 'Farhan', 'Hafiz', 'Ilham', 'Jafar', 'Karim', 'Luthfi', 'Mirza',
    'Nabil', 'Omar', 'Pandu', 'Qori', 'Reza', 'Syahrul', 'Taufik', 'Umar',
    'Wildan', 'Zaki', 'Alfarizi', 'Bramantyo', 'Daffa', 'Evan', 'Fauzan',
    'Ghifari', 'Hafidz', 'Irfan', 'Khoirul', 'Lukman', 'Marwan', 'Muhamad',
    'Eko', 'Riko', 'Doni', 'Oscar', 'Ucok', 'Widi', 'Yudi', 'Satrio',
]
_NAMA_DEPAN_P = [
    'Sari', 'Dewi', 'Putri', 'Rina', 'Ani', 'Wati', 'Fitri', 'Nita',
    'Yuni', 'Lestari', 'Mega', 'Novia', 'Indah', 'Ratna', 'Sinta', 'Tari',
    'Ulfa', 'Vera', 'Winda', 'Xena', 'Yola', 'Zahra', 'Ayu', 'Bunga',
    'Cantika', 'Dina', 'Erika', 'Fanny', 'Gita', 'Hana', 'Ira', 'Julia',
    'Kiki', 'Lina', 'Mira', 'Nisa', 'Okta', 'Prita', 'Qanita', 'Reni',
    'Sela', 'Tika', 'Umi', 'Vira', 'Widya', 'Yasmin', 'Zara', 'Amelia',
    'Bella', 'Citra', 'Devi', 'Elsa', 'Fira', 'Ghina', 'Hasna', 'Intan',
    'Khansa', 'Laila', 'Mawar', 'Nabila', 'Olivia', 'Paramita',
]
_NAMA_TENGAH = [
    'Nur', 'Sri', 'Dwi', 'Tri', 'Eka', 'Budi', 'Hadi', 'Wahyu',
    'Rizki', 'Cahya', 'Putra', 'Putri', 'Adi', 'Arya', 'Bagas',
    '', '', '', '', '', '', '', '',  # lebih banyak tanpa nama tengah
]
_NAMA_BELAKANG = [
    'Santoso', 'Wijaya', 'Kusuma', 'Pratama', 'Saputra', 'Hidayat',
    'Nugroho', 'Rahmad', 'Setiawan', 'Susanto', 'Wahyudi', 'Purnomo',
    'Hartono', 'Gunawan', 'Kurniawan', 'Hakim', 'Firmansyah', 'Darma',
    'Iskandar', 'Jaya', 'Laksono', 'Mulyono', 'Nurdiana', 'Oktavian',
    'Permadi', 'Qodri', 'Ramadan', 'Syahputra', 'Taufik', 'Utomo',
    'Adiputra', 'Budiman', 'Cahyono', 'Dirgantara', 'Effendi', 'Firdaus',
    'Gultom', 'Hasibuan', 'Irawan', 'Junaidi', 'Kartika', 'Manurung',
    'Nasution', 'Panjaitan', 'Sitompul', 'Simbolon', 'Siregar', 'Pane',
    'Harahap', 'Lubis', 'Daulay', 'Pulungan', 'Batubara', 'Sinaga',
    'Wibowo', 'Zulkarnain', 'Ramadhan', 'Sanjaya', 'Nurhadi', 'Surya',
]
_KOTA = [
    'Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang', 'Makassar',
    'Palembang', 'Yogyakarta', 'Malang', 'Bogor', 'Depok', 'Tangerang',
    'Bekasi', 'Denpasar', 'Pekanbaru', 'Batam', 'Balikpapan', 'Banjarmasin',
]
_AGAMA   = ['Islam', 'Islam', 'Islam', 'Kristen', 'Katolik', 'Hindu', 'Buddha']
_PEND    = ['SMA/SMK', 'SMA/SMK', 'D3', 'D4/S1', 'D4/S1', 'S2']
_ST_KAR  = [
    'PKWT', 'PKWT', 'PKWT', 'PKWT', 'PKWT', 'PKWT',  # 60% PKWT
    'PKWTT', 'PKWTT', 'PKWTT',                          # 30% PKWTT
    'PHL',                                               # 10% PHL
]
_PTKP_L  = ['TK/0', 'K/0', 'K/1', 'K/2']
_PTKP_P  = ['TK/0', 'TK/0', 'K/0', 'K/1']

# Gaji range default per level jabatan (Rp)
_GAJI_LEVEL = {
    'Crew':                 (2_500_000,  4_000_000),
    'Jr.Staff':             (3_000_000,  5_000_000),
    'Staff':                (4_000_000,  7_000_000),
    'Sr.Staff':             (6_000_000, 10_000_000),
    'Jr.Supervisor':        (8_000_000, 12_000_000),
    'Supervisor':           (10_000_000, 15_000_000),
    'Sr.Supervisor':        (13_000_000, 20_000_000),
    'Jr.Superintendent':    (15_000_000, 22_000_000),
    'Superintendent':       (18_000_000, 28_000_000),
    'Sr.Superintendent':    (22_000_000, 35_000_000),
    'Jr.Manager':           (25_000_000, 35_000_000),
    'Manager':              (30_000_000, 45_000_000),
    'Sr.Manager':           (40_000_000, 60_000_000),
    'Manajemen':            (55_000_000, 80_000_000),
    'Corporate Manajemen':  (75_000_000, 120_000_000),
}


def _gen_nama(jk):
    pool    = _NAMA_DEPAN_L if jk == 'L' else _NAMA_DEPAN_P
    depan   = random.choice(pool)
    tengah  = random.choice(_NAMA_TENGAH)
    belakang = random.choice(_NAMA_BELAKANG)
    if tengah:
        return f'{depan} {tengah} {belakang}'
    return f'{depan} {belakang}'


def _gen_nik_dummy(company, existing_niks):
    """Generate NIK unik format DMY-XXXX per company."""
    for _ in range(9999):
        num = random.randint(1, 9999)
        nik = f'DMY-{num:04d}'
        if nik not in existing_niks and not Employee.objects.filter(company=company, nik=nik).exists():
            existing_niks.add(nik)
            return nik
    raise ValueError('Tidak bisa generate NIK unik, pool habis.')


def _input_gaji_range(label_level, default_min, default_max):
    """Input range gaji min-max dari user, return (min, max)."""
    while True:
        try:
            raw_min = input_prompt(f'  Gaji min {label_level} (Rp)', default=str(default_min))
            raw_max = input_prompt(f'  Gaji max {label_level} (Rp)', default=str(default_max))
            g_min = int(str(raw_min).replace('.', '').replace(',', '').replace('_', ''))
            g_max = int(str(raw_max).replace('.', '').replace(',', '').replace('_', ''))
            if g_min <= 0 or g_max <= 0:
                err('Gaji harus lebih dari 0.')
                continue
            if g_min > g_max:
                err('Gaji min tidak boleh lebih besar dari gaji max.')
                continue
            return g_min, g_max
        except ValueError:
            err('Masukkan angka saja (boleh pakai titik/koma sebagai pemisah ribuan).')


def menu_generate_dummy_karyawan():
    header('GENERATE KARYAWAN DUMMY')

    # ── Pool data tambahan ────────────────────────────────────────────────────
    _BANK = ['BCA', 'BRI', 'BNI', 'Mandiri', 'BSI', 'CIMB Niaga', 'Danamon', 'BTN']
    _JALAN = ['Jl. Merdeka', 'Jl. Sudirman', 'Jl. Gatot Subroto', 'Jl. Ahmad Yani',
              'Jl. Diponegoro', 'Jl. Pahlawan', 'Jl. Pemuda', 'Jl. Imam Bonjol',
              'Jl. Kartini', 'Jl. Veteran', 'Jl. Cendrawasih', 'Jl. Mawar']
    _KELURAHAN = ['Kebayoran', 'Menteng', 'Tebet', 'Cempaka Putih', 'Gambir',
                  'Senen', 'Koja', 'Penjaringan', 'Cilincing', 'Tanjung Priok',
                  'Lowokwaru', 'Blimbing', 'Klojen', 'Sukun', 'Kedungkandang']
    _KECAMATAN = ['Kebayoran Baru', 'Menteng', 'Tebet', 'Cempaka Putih', 'Gambir',
                  'Senen', 'Koja', 'Penjaringan', 'Cilincing', 'Tanjung Priok',
                  'Lowokwaru', 'Blimbing', 'Klojen', 'Sukun', 'Kedungkandang']
    _GOLDAR    = ['A', 'B', 'AB', 'O', 'A', 'O', 'B', 'O']  # O lebih umum
    _HUB_DARURAT = ['Istri', 'Suami', 'Ayah', 'Ibu', 'Kakak', 'Adik', 'Saudara']
    _NAMA_DARURAT_L = ['Budi', 'Ahmad', 'Hendra', 'Agus', 'Wahyu', 'Dani', 'Eko', 'Rudi']
    _NAMA_DARURAT_P = ['Sari', 'Dewi', 'Rina', 'Ani', 'Wati', 'Fitri', 'Nita', 'Yuni']
    _NAMA_ANAK_L = ['Bima', 'Arjuna', 'Raka', 'Dafa', 'Farhan', 'Rafi', 'Zaki', 'Naufal']
    _NAMA_ANAK_P = ['Naura', 'Kirana', 'Azahra', 'Nabila', 'Salsabila', 'Hana', 'Intan', 'Syifa']

    # ── Pilih company ─────────────────────────────────────────────────────────
    targets = pilih_companies('Generate dummy karyawan untuk company')
    if not targets:
        return

    # ── Cek department & jabatan tersedia ─────────────────────────────────────
    for company in targets:
        n_dept = Department.objects.filter(company=company, aktif=True).count()
        n_pos  = Position.objects.filter(company=company, aktif=True).count()
        if n_dept == 0 or n_pos == 0:
            err(f'Company "{company.nama}" belum punya department/jabatan. Tambah dulu.')
            return

    # ── Jumlah dummy per company ──────────────────────────────────────────────
    print(f'\n{C}  Jumlah karyawan dummy:{RST}')
    while True:
        try:
            n_dummy = int(input_prompt('Jumlah dummy per company', default='10'))
            if n_dummy <= 0:
                err('Harus lebih dari 0.')
                continue
            break
        except ValueError:
            err('Masukkan angka bulat.')

    # ── Rasio gender ──────────────────────────────────────────────────────────
    print(f'\n{C}  Rasio gender:{RST}')
    while True:
        try:
            pct_l = int(input_prompt('% Laki-laki', default='60'))
            if not (0 <= pct_l <= 100):
                err('Masukkan 0–100.')
                continue
            info(f'Laki-laki {pct_l}% | Perempuan {100-pct_l}%')
            break
        except ValueError:
            err('Masukkan angka bulat.')

    # ── Range gaji — pakai default langsung ──────────────────────────────────
    gaji_range = {level: (dmin, dmax) for level, (dmin, dmax) in _GAJI_LEVEL.items()}

    # ── Tanggal join range ────────────────────────────────────────────────────
    print(f'\n{C}  Rentang tanggal bergabung:{RST}')
    join_min = input_tanggal('Join date paling awal', default=date(2020, 1, 1))
    join_max = input_tanggal('Join date paling akhir', default=date.today())
    if join_min > join_max:
        err('Join date min tidak boleh lebih besar dari max.')
        return

    # ── Konfirmasi ────────────────────────────────────────────────────────────
    print()
    info('Ringkasan generate karyawan dummy:')
    dim(f'  Company  : {", ".join(c.nama for c in targets)}')
    dim(f'  Jumlah   : {n_dummy} per company ({n_dummy * len(targets)} total)')
    dim(f'  Gender   : L {pct_l}% | P {100-pct_l}%')
    dim(f'  Join date: {join_min.strftime("%d-%m-%Y")} — {join_max.strftime("%d-%m-%Y")}')
    dim(f'  Logika   : Dept → Jabatan (jabatan sesuai dept)')
    print()
    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    # ── Generate ──────────────────────────────────────────────────────────────
    total_created = 0
    join_delta    = (join_max - join_min).days

    for company in targets:
        # Build mapping dept → list jabatan di dept itu
        depts = list(Department.objects.filter(company=company, aktif=True))

        dept_jabatan_map = {}
        for dept in depts:
            jabatans = list(Position.objects.filter(
                company=company, aktif=True, department=dept
            ))
            if jabatans:
                dept_jabatan_map[dept] = jabatans

        # Dept yang tidak punya jabatan → pakai jabatan tanpa dept sebagai fallback
        pos_no_dept = list(Position.objects.filter(
            company=company, aktif=True, department__isnull=True
        ))

        # Kalau tidak ada mapping sama sekali, fallback semua jabatan
        all_positions = list(Position.objects.filter(company=company, aktif=True))

        existing_niks = set()
        emp_bulk = []

        for _ in range(n_dummy):
            jk   = 'L' if random.random() < pct_l / 100 else 'P'
            nama = _gen_nama(jk)
            nik  = _gen_nik_dummy(company, existing_niks)

            # ── Pilih dept dulu, lalu jabatan dari dept itu ──
            if dept_jabatan_map:
                dept = random.choice(list(dept_jabatan_map.keys()))
                pos  = random.choice(dept_jabatan_map[dept])
            elif pos_no_dept:
                dept = random.choice(depts)
                pos  = random.choice(pos_no_dept)
            else:
                dept = random.choice(depts)
                pos  = random.choice(all_positions)

            level    = pos.level if pos.level in _GAJI_LEVEL else 'Staff'
            g_min, g_max = gaji_range[level]
            gaji_pokok   = random.randint(g_min // 1000, g_max // 1000) * 1000

            join_date = join_min + timedelta(days=random.randint(0, join_delta))
            tgl_lahir = date(random.randint(1975, 2000), random.randint(1, 12), random.randint(1, 28))
            st_nikah  = random.choice(['Lajang', 'Menikah', 'Menikah', 'Lajang'])
            jml_anak  = random.randint(0, 3) if st_nikah == 'Menikah' else 0
            jk_full   = 'Laki-laki' if jk == 'L' else 'Perempuan'
            ptkp      = random.choice(_PTKP_L if jk == 'L' else _PTKP_P)
            kota      = random.choice(_KOTA)

            # ── Data identitas & bank ──
            no_ktp  = ''.join([str(random.randint(0,9)) for _ in range(16)])
            no_npwp = f'{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(1,9)}-{random.randint(100,999)}.{random.randint(100,999)}'
            no_bpjs_kes = ''.join([str(random.randint(0,9)) for _ in range(13)])
            no_bpjs_tk  = ''.join([str(random.randint(0,9)) for _ in range(11)])
            nama_bank   = random.choice(_BANK)
            no_rek      = ''.join([str(random.randint(0,9)) for _ in range(random.randint(10,13))])
            no_hp       = f'08{random.randint(100000000, 999999999)}'
            email       = f'{nama.lower().replace(" ",".")[:20]}@gmail.com'
            alamat      = f'{random.choice(_JALAN)} No.{random.randint(1,99)}'
            rt          = f'{random.randint(1,20):03d}'
            rw          = f'{random.randint(1,10):03d}'
            kelurahan   = random.choice(_KELURAHAN)
            kecamatan   = random.choice(_KECAMATAN)
            kode_pos    = str(random.randint(10000, 99999))

            # ── Golongan darah & No KK ──
            goldar  = random.choice(_GOLDAR)
            no_kk   = ''.join([str(random.randint(0,9)) for _ in range(16)])

            # ── Kontak darurat ──
            hub_dar  = random.choice(_HUB_DARURAT)
            pool_dar = _NAMA_DARURAT_L if random.random() < 0.5 else _NAMA_DARURAT_P
            nama_dar = random.choice(pool_dar) + ' ' + random.choice(_NAMA_BELAKANG)
            hp_dar   = f'08{random.randint(100000000, 999999999)}'

            # ── Status karyawan sesuai level ──
            if pos.level == 'Crew':
                st_kar = random.choice(['PHL', 'PKWT'])
            else:
                st_kar = random.choice(_ST_KAR)

            emp_obj = Employee(
                company         = company,
                nik             = nik,
                nama            = nama,
                department      = dept,
                jabatan         = pos,
                status_karyawan = st_kar,
                join_date       = join_date,
                status          = 'Aktif',
                jenis_kelamin   = jk,
                agama           = random.choice(_AGAMA),
                pendidikan      = random.choice(_PEND),
                golongan_darah  = goldar,
                status_nikah    = st_nikah,
                jumlah_anak     = jml_anak,
                ptkp            = ptkp,
                tempat_lahir    = kota,
                tanggal_lahir   = tgl_lahir,
                gaji_pokok      = gaji_pokok,
                no_ktp          = no_ktp,
                no_kk           = no_kk,
                no_npwp         = no_npwp,
                no_bpjs_kes     = no_bpjs_kes,
                no_bpjs_tk      = no_bpjs_tk,
                nama_bank       = nama_bank,
                no_rek          = no_rek,
                nama_rek        = nama,
                no_hp           = no_hp,
                email           = email,
                alamat          = alamat,
                rt              = rt,
                rw              = rw,
                kelurahan       = kelurahan,
                kecamatan       = kecamatan,
                kode_pos        = kode_pos,
                nama_darurat    = nama_dar,
                hub_darurat     = hub_dar,
                hp_darurat      = hp_dar,
            )
            emp_bulk.append(emp_obj)

        try:
            created = Employee.objects.bulk_create(emp_bulk, ignore_conflicts=True)
            n = len(created)
            ok(f'{company.nama}: {n} karyawan dummy berhasil dibuat.')
            total_created += n

            # ── Generate data anak untuk karyawan menikah ──────────────────
            from apps.employees.models import AnakKaryawan
            anak_bulk = []
            for emp in Employee.objects.filter(company=company, status_nikah='Menikah', jumlah_anak__gt=0).order_by('-id')[:n]:
                for urutan in range(1, emp.jumlah_anak + 1):
                    jk_anak = random.choice(['L', 'P'])
                    pool_anak = _NAMA_ANAK_L if jk_anak == 'L' else _NAMA_ANAK_P
                    tgl_anak  = date(random.randint(2005, 2020), random.randint(1,12), random.randint(1,28))
                    anak_bulk.append(AnakKaryawan(
                        employee      = emp,
                        urutan        = urutan,
                        nama          = random.choice(pool_anak),
                        tgl_lahir     = tgl_anak,
                        jenis_kelamin = jk_anak,
                        no_bpjs_kes   = ''.join([str(random.randint(0,9)) for _ in range(13)]),
                    ))
            if anak_bulk:
                AnakKaryawan.objects.bulk_create(anak_bulk, ignore_conflicts=True)
                info(f'{company.nama}: {len(anak_bulk)} data anak berhasil dibuat.')

        except Exception as e:
            err(f'{company.nama} gagal: {e}')

    print()
    ok(f'Total {total_created} karyawan dummy berhasil dibuat.')
    info('Logika: Dept dipilih dulu → jabatan dari dept tersebut')
    dim('Jalankan Generate Absensi untuk generate data kehadiran.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 6 — LIHAT SEMUA DATA
# ══════════════════════════════════════════════════════════════════════════════

def menu_lihat_data():
    header('DATA MASTER SAAT INI')

    companies = Company.objects.order_by('nama')
    if not companies.exists():
        warn('Belum ada company.')
        return

    for c in companies:
        status_color = G if c.status == 'aktif' else Y
        print(f'\n{W}  [CO] {c.nama}{RST} {clr(f"[{c.status}]", status_color)} {DIM}(slug: {c.slug}){RST}')

        addons = []
        if getattr(c, 'addon_assets', False):              addons.append('Assets')
        if getattr(c, 'addon_recruitment', False):         addons.append('Rekrutmen')
        if getattr(c, 'addon_psychotest', False):          addons.append('Psikotes')
        if getattr(c, 'addon_advanced_psychotest', False): addons.append('OCEAN')
        if getattr(c, 'addon_od', False):                  addons.append('OD')
        if addons:
            dim(f'     Add-On aktif: {", ".join(addons)}')
        else:
            dim(f'     Add-On: semua nonaktif')

        depts = Department.objects.filter(company=c, aktif=True).order_by('nama')
        if depts.exists():
            dim(f'     Department ({depts.count()}):')
            for d in depts:
                kode_str = f' ({d.kode})' if d.kode else ''
                dim(f'       • {d.nama}{kode_str}')
        else:
            dim(f'     Department: belum ada')

        positions = Position.objects.filter(company=c, aktif=True).order_by('nama')
        if positions.exists():
            dim(f'     Jabatan ({positions.count()}):')
            for pos in positions:
                dept_str = f' > {pos.department.nama}' if pos.department else ''
                dim(f'       • {pos.nama} [{pos.level}]{dept_str}')
        else:
            dim(f'     Jabatan: belum ada')

        # Info absensi
        emp_ids = Employee.objects.filter(company=c, status='Aktif').values_list('pk', flat=True)
        n_abs = Attendance.objects.filter(employee__in=emp_ids).count()
        if n_abs:
            dim(f'     Absensi : {n_abs:,} record')
        else:
            dim(f'     Absensi : belum ada')

    print()
    info(f'Total: {companies.count()} company, '
         f'{Department.objects.count()} department, '
         f'{Position.objects.count()} jabatan.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU JABATAN PRESET — 114 Jabatan Industri
# ══════════════════════════════════════════════════════════════════════════════

JABATAN_PRESET = [
    # Mining | MPE-MIN
    ("Operator ADT",                    "Staff"),
    ("Operator Excavator",              "Staff"),
    ("Operator Dozer",                  "Staff"),
    ("Operator Grader",                 "Staff"),
    ("Operator Loader",                 "Staff"),
    ("Surveyor",                        "Staff"),
    ("Mine Dispatcher",                 "Staff"),
    ("Drill & Blast Officer",           "Staff"),
    ("Mine Engineer",                   "Staff"),
    ("Senior Mine Engineer",            "Senior Staff"),
    ("Mine Foreman",                    "Supervisor"),
    ("Pit Supervisor",                  "Supervisor"),
    ("Mining Superintendent",           "Senior Supervisor"),
    ("Mine Manager",                    "Manager"),

    # Civil & Maintenance | CIV-MAINT
    ("Mechanic",                        "Staff"),
    ("Helper Mechanic",                 "Staff"),
    ("Welder",                          "Staff"),
    ("Technician",                      "Staff"),
    ("Maintenance Planner",             "Staff"),
    ("Senior Mechanic",                 "Senior Staff"),
    ("Foreman Mechanic",                "Supervisor"),
    ("Workshop Supervisor",             "Supervisor"),
    ("Maintenance Superintendent",      "Senior Supervisor"),
    ("Maintenance Manager",             "Manager"),

    # Electric & Utility | EWF
    ("Electrician",                     "Staff"),
    ("Genset Operator",                 "Staff"),
    ("Water Pump Operator",             "Staff"),
    ("Electrical Technician",           "Staff"),
    ("Electrical Engineer",             "Staff"),
    ("Senior Electrical Engineer",      "Senior Staff"),
    ("Electrical Supervisor",           "Supervisor"),
    ("Electrical Superintendent",       "Senior Supervisor"),
    ("Utility Manager",                 "Manager"),

    # Health Safety Environment | HSE
    ("Safety Patrol",                   "Staff"),
    ("Firefighter",                     "Staff"),
    ("Safety Officer",                  "Staff"),
    ("Environmental Officer",           "Staff"),
    ("Senior Safety Officer",           "Senior Staff"),
    ("Safety Supervisor",               "Supervisor"),
    ("HSE Superintendent",              "Senior Supervisor"),
    ("HSE Manager",                     "Manager"),

    # Human Resources | HR
    ("HR Admin",                        "Staff"),
    ("Recruitment Officer",             "Staff"),
    ("Training Officer",                "Staff"),
    ("HR Generalist",                   "Senior Staff"),
    ("HR Supervisor",                   "Supervisor"),
    ("HR Superintendent",               "Senior Supervisor"),
    ("HR Manager",                      "Manager"),

    # General Affair | GA
    ("Office Boy",                      "Staff"),
    ("Office Girl",                     "Staff"),
    ("Driver",                          "Staff"),
    ("Gardener",                        "Staff"),
    ("GA Officer",                      "Staff"),
    ("Mess & Camp Officer",             "Staff"),
    ("Senior GA Officer",               "Senior Staff"),
    ("GA Supervisor",                   "Supervisor"),
    ("GA Superintendent",               "Senior Supervisor"),
    ("GA Manager",                      "Manager"),

    # Logistic & Warehouse | LOG
    ("Warehouse Helper",                "Staff"),
    ("Storekeeper",                     "Staff"),
    ("Logistic Officer",                "Staff"),
    ("Senior Logistic Officer",         "Senior Staff"),
    ("Warehouse Supervisor",            "Supervisor"),
    ("Logistic Superintendent",         "Senior Supervisor"),
    ("Logistic Manager",                "Manager"),

    # Purchasing | PURCH
    ("Purchasing Admin",                "Staff"),
    ("Procurement Officer",             "Staff"),
    ("Senior Procurement Officer",      "Senior Staff"),
    ("Procurement Supervisor",          "Supervisor"),
    ("Procurement Superintendent",      "Senior Supervisor"),
    ("Procurement Manager",             "Manager"),

    # Finance & Accounting | FAT
    ("Finance Admin",                   "Staff"),
    ("Accountant",                      "Staff"),
    ("Tax Officer",                     "Staff"),
    ("Senior Accountant",               "Senior Staff"),
    ("Finance Supervisor",              "Supervisor"),
    ("Finance Superintendent",          "Senior Supervisor"),
    ("Finance Manager",                 "Manager"),

    # Infrastructure Technology | IT
    ("IT Support",                      "Staff"),
    ("Network Engineer",                "Staff"),
    ("System Administrator",            "Senior Staff"),
    ("IT Supervisor",                   "Supervisor"),
    ("IT Superintendent",               "Senior Supervisor"),
    ("IT Manager",                      "Manager"),

    # Legal | LGL
    ("Legal Admin",                     "Staff"),
    ("Legal Officer",                   "Staff"),
    ("Senior Legal Officer",            "Senior Staff"),
    ("Legal Supervisor",                "Supervisor"),
    ("Legal Manager",                   "Manager"),

    # Security | SG
    ("Security Guard",                  "Staff"),
    ("Security Officer",                "Staff"),
    ("Senior Security Officer",         "Senior Staff"),
    ("Security Supervisor",             "Supervisor"),
    ("Security Manager",                "Manager"),

    # Site Management
    ("Site Superintendent",             "Senior Manager"),
    ("Site Manager",                    "Senior Manager"),

    # Corporate Management
    ("Operations Director",             "Director"),
    ("Finance Director",                "Director"),
    ("HR Director",                     "Director"),
    ("Managing Director",               "Director"),
]


def menu_jabatan_preset():
    header('TAMBAH JABATAN PRESET — 114 Jabatan Industri')

    targets = pilih_companies('Apply jabatan ke company')
    if not targets:
        return

    info(f'Target: {", ".join(c.nama for c in targets)}')
    info(f'Akan insert {len(JABATAN_PRESET)} jabatan preset.')

    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    created = skipped = 0
    for company in targets:
        for nama, level in JABATAN_PRESET:
            obj, is_new = Position.objects.get_or_create(
                company=company,
                nama=nama,
                defaults={'level': level, 'aktif': True}
            )
            if is_new:
                created += 1
            else:
                skipped += 1

    print()
    ok(f'{created} jabatan berhasil ditambah, {skipped} sudah ada (skip).')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU SEED KANDIDAT
# ══════════════════════════════════════════════════════════════════════════════

_SUMBER_REKRUTMEN = [
    'LinkedIn', 'LinkedIn', 'JobStreet', 'JobStreet', 'Indeed',
    'Referral', 'Referral', 'Walk-in', 'Instagram', 'Website',
]
_STATUS_KANDIDAT = [
    'Screening', 'Screening', 'Screening',
    'Psikotes', 'Psikotes',
    'Interview HR', 'Interview HR',
    'Interview User',
    'Medical Check',
    'Offering',
    'Hired', 'Hired',
    'Rejected', 'Rejected', 'Rejected',
    'Withdrawn',
]
_PENDIDIKAN_K = ['SMA/SMK', 'D3', 'D4/S1', 'D4/S1', 'S1', 'S2']


def menu_sync_department_jabatan():
    header('FIX DEPARTMENT KE JABATAN')
    info('Update department jabatan berdasarkan struktur organisasi perusahaan.')

    # Mapping jabatan → department (berdasarkan struktur org resmi)
    JABATAN_DEPT_MAP = {
        # Mining
        'Operator ADT':                 'Mining',
        'Operator Excavator':           'Mining',
        'Operator Dozer':               'Mining',
        'Operator Grader':              'Mining',
        'Operator Loader':              'Mining',
        'Surveyor':                     'Mining',
        'Mine Dispatcher':              'Mining',
        'Drill & Blast Officer':        'Mining',
        'Mine Engineer':                'Mining',
        'Senior Mine Engineer':         'Mining',
        'Mine Foreman':                 'Mining',
        'Pit Supervisor':               'Mining',
        'Mining Superintendent':        'Mining',
        'Mine Manager':                 'Mining',

        # Civil & Maintenance
        'Mechanic':                     'Civil & Maintenance',
        'Helper Mechanic':              'Civil & Maintenance',
        'Welder':                       'Civil & Maintenance',
        'Technician':                   'Civil & Maintenance',
        'Maintenance Planner':          'Civil & Maintenance',
        'Senior Mechanic':              'Civil & Maintenance',
        'Foreman Mechanic':             'Civil & Maintenance',
        'Workshop Supervisor':          'Civil & Maintenance',
        'Maintenance Superintendent':   'Civil & Maintenance',
        'Maintenance Manager':          'Civil & Maintenance',

        # Electric & Water Facility
        'Electrician':                  'Electric & Water Facility',
        'Genset Operator':              'Electric & Water Facility',
        'Water Pump Operator':          'Electric & Water Facility',
        'Electrical Technician':        'Electric & Water Facility',
        'Electrical Engineer':          'Electric & Water Facility',
        'Senior Electrical Engineer':   'Electric & Water Facility',
        'Electrical Supervisor':        'Electric & Water Facility',
        'Electrical Superintendent':    'Electric & Water Facility',
        'Utility Manager':              'Electric & Water Facility',

        # Health Safety Environment
        'Safety Patrol':                'Health Safety Environment',
        'Firefighter':                  'Health Safety Environment',
        'Safety Officer':               'Health Safety Environment',
        'Environmental Officer':        'Health Safety Environment',
        'Senior Safety Officer':        'Health Safety Environment',
        'Safety Supervisor':            'Health Safety Environment',
        'HSE Superintendent':           'Health Safety Environment',
        'HSE Manager':                  'Health Safety Environment',

        # Human Resources
        'HR Admin':                     'Human Resources',
        'Recruitment Officer':          'Human Resources',
        'Training Officer':             'Human Resources',
        'HR Generalist':                'Human Resources',
        'HR Supervisor':                'Human Resources',
        'HR Superintendent':            'Human Resources',
        'HR Manager':                   'Human Resources',

        # General Affair
        'Office Boy':                   'General Affair',
        'Office Girl':                  'General Affair',
        'Driver':                       'General Affair',
        'Gardener':                     'General Affair',
        'GA Officer':                   'General Affair',
        'Mess & Camp Officer':          'General Affair',
        'Senior GA Officer':            'General Affair',
        'GA Supervisor':                'General Affair',
        'GA Superintendent':            'General Affair',
        'GA Manager':                   'General Affair',

        # Logistic
        'Warehouse Helper':             'Logistic',
        'Storekeeper':                  'Logistic',
        'Logistic Officer':             'Logistic',
        'Senior Logistic Officer':      'Logistic',
        'Warehouse Supervisor':         'Logistic',
        'Logistic Superintendent':      'Logistic',
        'Logistic Manager':             'Logistic',

        # Purchasing
        'Purchasing Admin':             'Purchasing',
        'Procurement Officer':          'Purchasing',
        'Senior Procurement Officer':   'Purchasing',
        'Procurement Supervisor':       'Purchasing',
        'Procurement Superintendent':   'Purchasing',
        'Procurement Manager':          'Purchasing',

        # Finance & Accounting
        'Finance Admin':                'Finance & Accounting',
        'Accountant':                   'Finance & Accounting',
        'Tax Officer':                  'Finance & Accounting',
        'Senior Accountant':            'Finance & Accounting',
        'Finance Supervisor':           'Finance & Accounting',
        'Finance Superintendent':       'Finance & Accounting',
        'Finance Manager':              'Finance & Accounting',

        # Infrastructure Technology
        'IT Support':                   'Infrastructure Technology',
        'Network Engineer':             'Infrastructure Technology',
        'System Administrator':         'Infrastructure Technology',
        'IT Supervisor':                'Infrastructure Technology',
        'IT Superintendent':            'Infrastructure Technology',
        'IT Manager':                   'Infrastructure Technology',

        # Legal
        'Legal Admin':                  'Legal',
        'Legal Officer':                'Legal',
        'Senior Legal Officer':         'Legal',
        'Legal Supervisor':             'Legal',
        'Legal Manager':                'Legal',

        # Security
        'Security Guard':               'Security',
        'Security Officer':             'Security',
        'Senior Security Officer':      'Security',
        'Security Supervisor':          'Security',
        'Security Manager':             'Security',
    }

    targets = pilih_companies('Fix jabatan untuk company')
    if not targets:
        return

    updated = skipped = not_found = 0
    for company in targets:
        depts = {d.nama: d for d in Department.objects.filter(company=company)}

        for jabatan_nama, dept_keyword in JABATAN_DEPT_MAP.items():
            dept_match = None
            for dept_nama, dept_obj in depts.items():
                if dept_keyword.lower() in dept_nama.lower():
                    dept_match = dept_obj
                    break

            if not dept_match:
                not_found += 1
                continue

            n = Position.objects.filter(
                company=company,
                nama__iexact=jabatan_nama
            ).update(department=dept_match)

            if n > 0:
                updated += n
            else:
                skipped += 1

    print()
    ok(f'Selesai! {updated} jabatan berhasil di-fix department-nya.')
    if skipped:
        warn(f'{skipped} jabatan tidak ditemukan di database (mungkin nama berbeda).')
    if not_found:
        warn(f'{not_found} dept tidak ditemukan di company.')


def menu_seed_kandidat():
    header('SEED KANDIDAT REKRUTMEN')

    targets = pilih_companies('Seed kandidat untuk company')
    if not targets:
        return

    while True:
        try:
            jumlah = int(input_prompt('Jumlah kandidat per company', default='30'))
            if jumlah <= 0:
                err('Harus lebih dari 0.')
                continue
            break
        except ValueError:
            err('Masukkan angka.')

    info(f'Akan generate {jumlah} kandidat per company ({jumlah * len(targets)} total)')
    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    from apps.recruitment.models import Candidate, ManpowerRequest
    from datetime import date, timedelta

    _SUMBER = ['LinkedIn', 'LinkedIn', 'JobStreet', 'JobStreet', 'Indeed',
               'Referral', 'Referral', 'Walk-in', 'Instagram', 'Website']
    _STATUS = ['Screening', 'Screening', 'Screening', 'Psikotes', 'Psikotes',
               'Interview HR', 'Interview HR', 'Interview User', 'Medical Check',
               'Offering', 'Hired', 'Hired', 'Rejected', 'Rejected', 'Rejected', 'Withdrawn']
    _PEND   = ['SMA/SMK', 'D3', 'D4/S1', 'D4/S1', 'S1', 'S2']

    total = 0
    for company in targets:
        positions = list(Position.objects.filter(company=company, aktif=True).values_list('nama', flat=True))
        if not positions:
            positions = ['Staff Umum', 'Operator', 'Supervisor', 'Admin', 'Manager']

        mprf = ManpowerRequest.objects.filter(company=company).first()

        bulk = []
        for _ in range(jumlah):
            jk  = random.choice(['L', 'L', 'P'])
            nama = _gen_nama(jk)
            jabatan = random.choice(positions)
            exp = random.randint(0, 15)
            gaji_min = 3_000_000 + (exp * 500_000)
            gaji_max = gaji_min + 3_000_000
            ekspektasi = random.randint(gaji_min // 1000, gaji_max // 1000) * 1000
            ats_score = random.randint(40, 95)
            if ats_score >= 80:   ats_grade = 'A'
            elif ats_score >= 65: ats_grade = 'B'
            elif ats_score >= 50: ats_grade = 'C'
            else:                 ats_grade = 'D'

            bulk.append(Candidate(
                mprf             = mprf,
                nama             = nama,
                email            = f'{nama.lower().replace(" ", ".")[:20]}@gmail.com',
                no_hp            = f'08{random.randint(100000000, 999999999)}',
                jabatan_dilamar  = jabatan,
                sumber           = random.choice(_SUMBER),
                status           = random.choice(_STATUS),
                pendidikan       = random.choice(_PEND),
                pengalaman_tahun = exp,
                ekspektasi_gaji  = ekspektasi,
                ats_score        = ats_score,
                ats_grade        = ats_grade,
                ats_rekomendasi  = 'Lanjut' if ats_score >= 65 else 'Pertimbangkan',
            ))

        created = Candidate.objects.bulk_create(bulk, ignore_conflicts=True)
        n = len(created)
        total += n
        ok(f'{company.nama}: {n} kandidat berhasil dibuat.')

    print()
    ok(f'Total {total} kandidat berhasil dibuat!')


def menu_seed_kontrak():
    header('SEED KONTRAK KARYAWAN')

    _PENANDATANGAN = [
        ('HR Manager',        'Manager'),
        ('Site Manager',      'Manager'),
        ('HR Director',       'Director'),
        ('Managing Director', 'Director'),
    ]

    targets = pilih_companies('Seed kontrak untuk company')
    if not targets:
        return

    info('Kontrak akan dibuat untuk karyawan aktif yang belum punya kontrak.')

    # Pilih tipe kontrak & rasio
    print(f'\n{C}  Rasio tipe kontrak:{RST}')
    info('Total harus 100. Default: PKWT=60, PKWTT=30, PHL=10')
    while True:
        try:
            pct_pkwt  = int(input_prompt('% PKWT  (Waktu Tertentu)', default='60') or 60)
            pct_pkwtt = int(input_prompt('% PKWTT (Waktu Tidak Tertentu)', default='30') or 30)
            pct_phl   = 100 - pct_pkwt - pct_pkwtt
            if pct_pkwt + pct_pkwtt > 100 or pct_phl < 0:
                err('Total melebihi 100. Coba lagi.')
                continue
            info(f'Rasio: PKWT={pct_pkwt}% | PKWTT={pct_pkwtt}% | PHL={pct_phl}%')
            break
        except ValueError:
            err('Masukkan angka.')

    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.')
        return

    from apps.contracts.models import Contract
    from apps.employees.models import Employee
    from datetime import date, timedelta

    # Build tipe pool sesuai rasio
    tipe_pool = (
        ['PKWT'] * pct_pkwt +
        ['PKWTT'] * pct_pkwtt +
        ['Perjanjian Harian Lepas'] * pct_phl
    )

    total = 0
    for company in targets:
        employees = Employee.objects.filter(company=company, status='Aktif')
        existing  = set(Contract.objects.filter(company=company).values_list('employee_id', flat=True))
        targets_emp = [e for e in employees if e.pk not in existing]

        if not targets_emp:
            warn(f'{company.nama}: semua karyawan sudah punya kontrak.')
            continue

        penandatangan = random.choice(_PENANDATANGAN)
        bulk = []

        for emp in targets_emp:
            tipe = random.choice(tipe_pool)
            mulai = emp.join_date if emp.join_date else date(2023, 1, 1)

            if tipe == 'PKWT':
                durasi = random.choice([6, 12, 12, 24])
                selesai = mulai + timedelta(days=30 * durasi)
                # Tentukan status berdasarkan tanggal
                if selesai < date.today():
                    status = random.choice(['Expired', 'Renewed'])
                else:
                    status = 'Aktif'
            elif tipe == 'Perjanjian Harian Lepas':
                durasi = random.choice([3, 6])
                selesai = mulai + timedelta(days=30 * durasi)
                status = 'Aktif' if selesai >= date.today() else 'Expired'
            else:
                selesai = None  # PKWTT tidak ada tanggal selesai
                status = 'Aktif'

            bulk.append(Contract(
                company              = company,
                employee             = emp,
                tipe_kontrak         = tipe,
                tanggal_mulai        = mulai,
                tanggal_selesai      = selesai,
                jabatan              = emp.jabatan.nama if emp.jabatan else '',
                departemen           = emp.department.nama if emp.department else '',
                gaji_pokok           = emp.gaji_pokok or 0,
                status_gaji          = random.choice(['reguler', 'reguler', 'all_in']),
                nama_penandatangan   = penandatangan[0],
                jabatan_penandatangan= penandatangan[1],
                status               = status,
            ))

        # Simpan satu per satu karena ada auto-generate nomor kontrak
        created = 0
        for contract in bulk:
            try:
                contract.save()
                created += 1
            except Exception as e:
                pass

        total += created
        ok(f'{company.nama}: {created} kontrak berhasil dibuat.')

    print()
    ok(f'Total {total} kontrak berhasil dibuat!')
    info('PKWT = ada tanggal selesai | PKWTT = permanen | PHL = harian lepas')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU UTAMA
# ══════════════════════════════════════════════════════════════════════════════

def main_menu():
    while True:
        header('HRIS SmartDesk — Seed Data')

        n_company = Company.objects.count()
        n_dept    = Department.objects.count()
        n_pos     = Position.objects.count()
        n_emp     = Employee.objects.filter(status='Aktif').count()
        n_abs     = Attendance.objects.count()
        dim(f'  DB: {n_company} company | {n_dept} dept | {n_pos} jabatan | '
            f'{n_emp} karyawan aktif | {n_abs:,} absensi')

        print()
        menu = pilih_menu([
            'Tambah Company / Tenant',
            'Tambah Department',
            'Tambah Jabatan (manual)',
            'Tambah Jabatan Preset (114 jabatan industri)',
            'Sync Department ke Jabatan',
            'Generate Karyawan Dummy',
            'Generate Absensi',
            'Seed Kandidat Rekrutmen',
            'Seed Kontrak Karyawan',
            'Seed Asset Management',
            'Lihat semua data',
            'Keluar',
        ], title='Menu')

        if   menu == 0: menu_tambah_company()
        elif menu == 1: menu_tambah_department()
        elif menu == 2: menu_tambah_jabatan()
        elif menu == 3: menu_jabatan_preset()
        elif menu == 4: menu_sync_department_jabatan()
        elif menu == 5: menu_generate_dummy_karyawan()
        elif menu == 6: menu_generate_absensi()
        elif menu == 7: menu_seed_kandidat()
        elif menu == 8: menu_seed_kontrak()
        elif menu == 9: menu_seed_asset()
        elif menu == 10: menu_lihat_data()
        elif menu == 11:
            print(f'\n{G}  Selesai. Sampai jumpa!{RST}\n')
            break

        input(f'\n{DIM}  Tekan Enter untuk kembali ke menu...{RST}')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU 7 — SEED ASSET MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Pool data dummy ───────────────────────────────────────────────────────────

_MERK_MOBIL   = ['Toyota', 'Honda', 'Mitsubishi', 'Daihatsu', 'Suzuki', 'Isuzu', 'Hino', 'Nissan']
_MODEL_MOBIL  = ['Avanza', 'Innova', 'Rush', 'Fortuner', 'Pajero', 'Elf', 'Ranger', 'L300', 'Xpander', 'BRV']
_MERK_MOTOR   = ['Honda', 'Yamaha', 'Suzuki', 'Kawasaki']
_MODEL_MOTOR  = ['Vario 125', 'Beat', 'Mio', 'NMAX', 'Scoopy', 'Aerox', 'CBR', 'Ninja']

_MERK_LAPTOP  = ['Lenovo', 'HP', 'Dell', 'Asus', 'Acer', 'Apple']
_MODEL_LAPTOP = ['ThinkPad E14', 'Pavilion 14', 'Latitude 5420', 'VivoBook 14', 'Aspire 5', 'MacBook Air']
_MERK_PRINTER = ['Canon', 'Epson', 'HP', 'Brother', 'Fuji Xerox']
_MODEL_PRINTER= ['LBP6030', 'L3150', 'LaserJet Pro', 'DCP-L2540DW', 'DocuPrint M285']
_MERK_FURN    = ['Uno', 'Olympic', 'Chitose', 'Brother', 'Erka', 'Ligna']
_TIPE_FURN    = ['Meja Kerja', 'Kursi Kerja', 'Lemari Arsip', 'Sofa Tamu', 'Meja Rapat', 'Rak Buku', 'Partisi Ruangan']

_MERK_SERVER  = ['Dell', 'HP', 'Lenovo', 'IBM', 'Huawei']
_MODEL_SERVER = ['PowerEdge R740', 'ProLiant DL380', 'ThinkSystem SR650', 'System x3650', 'FusionServer G5500']
_MERK_SWITCH  = ['Cisco', 'Mikrotik', 'TP-Link', 'Netgear', 'Juniper']
_MODEL_SWITCH = ['Catalyst 2960', 'CRS326', 'TL-SG1024', 'GS316', 'EX2300-24P']
_MERK_AP      = ['Ubiquiti', 'Cisco', 'TP-Link', 'Ruckus', 'Mikrotik']
_MODEL_AP     = ['UniFi AP AC Pro', 'Aironet 2802', 'EAP245', 'R510', 'cAP ac']

_TIPE_MESIN   = ['Mesin Fotokopi', 'Mesin Jahit', 'Mesin Bubut', 'Mesin Las', 'Mesin Bor', 'Forklift', 'Kompresor', 'Generator']
_MERK_MESIN   = ['Ricoh', 'Brother', 'Makita', 'Bosch', 'Krisbow', 'Toyota Industries', 'Atlas Copco']

_MERK_AC      = ['Daikin', 'Panasonic', 'LG', 'Sharp', 'Mitsubishi Electric', 'Samsung', 'Gree']
_TIPE_AC      = ['AC Split 1PK', 'AC Split 1.5PK', 'AC Split 2PK', 'AC Cassette 2PK', 'AC Standing 5PK']
_MERK_ELEK    = ['Samsung', 'LG', 'Sony', 'Panasonic', 'Philips', 'Sharp']
_TIPE_ELEK    = ['TV LED 43"', 'TV LED 55"', 'Proyektor', 'UPS 1KVA', 'Dispenser', 'Kulkas 2 Pintu', 'Mesin Absensi']

_NAMA_GEDUNG  = ['Gedung {l}', 'Tower {l}', 'Kantor {l}', 'Warehouse {l}']
_LANTAI       = ['Lantai {n}', 'Basement {n}']
_RUANGAN      = [
    'Ruang HRD', 'Ruang Finance', 'Ruang IT', 'Ruang Marketing', 'Ruang Direktur',
    'Ruang Meeting A', 'Ruang Meeting B', 'Ruang Server', 'Gudang Umum', 'Lobby',
    'Ruang Operasional', 'Ruang Logistik', 'Ruang Legal', 'Pantry', 'Musholla',
]

_VENDOR_NAMA  = [
    'PT Sumber Teknologi', 'CV Maju Bersama', 'PT Artha Prima', 'UD Jaya Mandiri',
    'PT Global Solusi', 'CV Karya Utama', 'PT Delta Sejahtera', 'CV Bintang Abadi',
    'PT Nusantara Teknik', 'CV Prima Sentosa', 'PT Indo Megatech', 'UD Surya Abadi',
]
_VENDOR_CP    = [
    'Budi Santoso', 'Andi Wijaya', 'Sari Dewi', 'Hendra Kusuma',
    'Rina Pratama', 'Doni Saputra', 'Mega Lestari', 'Rizky Hidayat',
]

# Konfigurasi tipe aset: (nama_menu, kode_prefix, kategori_parent, kategori_child, harga_min, harga_max, useful_life, residual_pct)
_TIPE_ASET = {
    'mobil':   ('Kendaraan Roda 4',   'KND-R4',  'Kendaraan',        'Kendaraan Roda 4',    150_000_000, 600_000_000, 8,  10),
    'motor':   ('Kendaraan Roda 2',   'KND-R2',  'Kendaraan',        'Kendaraan Roda 2',     15_000_000,  40_000_000, 5,  10),
    'gedung':  ('Gedung',             'PROP-GD', 'Properti',         'Gedung & Bangunan',   500_000_000, 5_000_000_000, 20, 5),
    'tanah':   ('Tanah',              'PROP-TN', 'Properti',         'Tanah',               200_000_000, 3_000_000_000, 0,  0),
    'laptop':  ('Laptop & Komputer',  'IT-LPT',  'Peralatan Kantor', 'Komputer & Laptop',     8_000_000,  30_000_000, 4,  5),
    'printer': ('Printer & Scanner',  'IT-PRN',  'Peralatan Kantor', 'Printer & Scanner',     2_000_000,  15_000_000, 4,  5),
    'furnitur':('Furniture Kantor',   'FRN',     'Peralatan Kantor', 'Furniture',             1_000_000,  20_000_000, 8,  5),
    'server':  ('Server',             'IT-SVR',  'Infrastruktur IT', 'Server & Storage',     20_000_000, 200_000_000, 5,  5),
    'switch':  ('Switch & Networking','IT-NET',  'Infrastruktur IT', 'Jaringan',              3_000_000,  50_000_000, 5,  5),
    'ap':      ('Access Point',       'IT-AP',   'Infrastruktur IT', 'Jaringan',              1_500_000,  10_000_000, 5,  5),
    'mesin':   ('Mesin & Peralatan',  'MSN',     'Mesin',            'Mesin & Peralatan',    10_000_000, 500_000_000, 10, 10),
    'ac':      ('AC & Pendingin',     'HVAC',    'AC & Elektronik',  'AC & Pendingin',        3_000_000,  25_000_000, 5,  5),
    'elektronik':('Elektronik Umum',  'ELEK',    'AC & Elektronik',  'Elektronik',            1_000_000,  30_000_000, 5,  5),
}


# ── Helper generator per tipe ─────────────────────────────────────────────────

def _rand_serial():
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def _rand_tanggal_beli(tahun_awal=2018, tahun_akhir=2025):
    y = random.randint(tahun_awal, tahun_akhir)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return date(y, m, d)


def _gen_asset_name_detail(tipe):
    """Return (asset_name, brand) per tipe."""
    if tipe == 'mobil':
        merk = random.choice(_MERK_MOBIL)
        return f'{merk} {random.choice(_MODEL_MOBIL)}', merk
    if tipe == 'motor':
        merk = random.choice(_MERK_MOTOR)
        return f'{merk} {random.choice(_MODEL_MOTOR)}', merk
    if tipe == 'gedung':
        huruf = random.choice('ABCDE')
        return random.choice(_NAMA_GEDUNG).format(l=huruf), '-'
    if tipe == 'tanah':
        kota = random.choice(_KOTA)
        return f'Tanah {kota} Blok {random.choice("ABCDEF")}-{random.randint(1,20)}', '-'
    if tipe == 'laptop':
        merk = random.choice(_MERK_LAPTOP)
        return f'{merk} {random.choice(_MODEL_LAPTOP)}', merk
    if tipe == 'printer':
        merk = random.choice(_MERK_PRINTER)
        return f'{merk} {random.choice(_MODEL_PRINTER)}', merk
    if tipe == 'furnitur':
        merk = random.choice(_MERK_FURN)
        return f'{random.choice(_TIPE_FURN)} {merk}', merk
    if tipe == 'server':
        merk = random.choice(_MERK_SERVER)
        return f'{merk} {random.choice(_MODEL_SERVER)}', merk
    if tipe in ('switch', 'ap'):
        merk = random.choice(_MERK_SWITCH if tipe == 'switch' else _MERK_AP)
        model = random.choice(_MODEL_SWITCH if tipe == 'switch' else _MODEL_AP)
        return f'{merk} {model}', merk
    if tipe == 'mesin':
        merk = random.choice(_MERK_MESIN)
        return f'{random.choice(_TIPE_MESIN)} {merk}', merk
    if tipe == 'ac':
        merk = random.choice(_MERK_AC)
        return f'{random.choice(_TIPE_AC)} {merk}', merk
    if tipe == 'elektronik':
        merk = random.choice(_MERK_ELEK)
        return f'{random.choice(_TIPE_ELEK)} {merk}', merk
    return f'Aset {tipe.title()} #{random.randint(100,999)}', '-'


def _get_or_create_kategori(company, parent_name, child_name, asset_type='Tangible'):
    """Get or create hierarki kategori parent → child."""
    # Generate kode unik berbasis nama
    def _kode(name, prefix=''):
        base = prefix + name[:4].upper().replace(' ', '')
        kode = base
        i = 1
        while AssetCategory.objects.filter(code=kode).exists():
            kode = f'{base}{i}'
            i += 1
        return kode

    parent, _ = AssetCategory.objects.get_or_create(
        company=company, name=parent_name,
        defaults={'code': _kode(parent_name), 'asset_type': asset_type, 'parent': None}
    )
    child, _ = AssetCategory.objects.get_or_create(
        company=company, name=child_name, parent=parent,
        defaults={'code': _kode(child_name, parent.code[:2]), 'asset_type': asset_type}
    )
    return child


def _get_or_create_lokasi_pool(n_gedung, n_lantai, n_ruangan):
    """Generate pool lokasi hierarki: Gedung → Lantai → Ruangan."""
    lokasi_pool = []
    huruf_list = list('ABCDEFGHIJ')

    for gi in range(n_gedung):
        huruf = huruf_list[gi % len(huruf_list)]
        gd_code = f'GD-{huruf}'
        gd_name = f'Gedung {huruf}'
        gedung, _ = Location.objects.get_or_create(
            code=gd_code,
            defaults={'name': gd_name, 'type': 'Gedung'}
        )

        for li in range(1, n_lantai + 1):
            lt_code = f'{gd_code}-L{li}'
            lt_name = f'Lantai {li}'
            lantai, _ = Location.objects.get_or_create(
                code=lt_code,
                defaults={'name': lt_name, 'type': 'Lantai', 'parent': gedung}
            )

            ruangan_names = random.sample(_RUANGAN, min(n_ruangan, len(_RUANGAN)))
            for rn in ruangan_names:
                # kode unik
                rn_short = rn.replace('Ruang ', 'R-').replace(' ', '')[:8]
                rn_code = f'{lt_code}-{rn_short}'
                # pastikan unik
                suffix = ''
                base_code = rn_code[:18]
                counter = 1
                while Location.objects.filter(code=rn_code).exists():
                    rn_code = f'{base_code}-{counter}'
                    counter += 1
                ruangan, _ = Location.objects.get_or_create(
                    code=rn_code,
                    defaults={'name': rn, 'type': 'Ruangan', 'parent': lantai}
                )
                lokasi_pool.append(ruangan)

    if not lokasi_pool:
        # fallback: pakai lantai
        lokasi_pool = list(Location.objects.filter(type='Lantai'))
    return lokasi_pool


def _get_or_create_vendor_pool(n_vendor):
    """Generate pool vendor dummy."""
    vendors = []
    pool = list(_VENDOR_NAMA)
    random.shuffle(pool)
    for i in range(min(n_vendor, len(pool))):
        nama = pool[i]
        # kode unik
        base_code = 'VND-' + str(i + 1).zfill(3)
        code = base_code
        j = 1
        while Vendor.objects.filter(code=code).exists():
            code = f'VND-{i+1:03d}-{j}'
            j += 1
        v, _ = Vendor.objects.get_or_create(
            code=code,
            defaults={
                'name': nama,
                'contact_person': random.choice(_VENDOR_CP),
                'phone': f'08{random.randint(100000000, 999999999)}',
                'email': f'info@{nama.lower().replace(" ","").replace(".", "")[:12]}.co.id',
                'status': 'Aktif',
            }
        )
        vendors.append(v)
    if not vendors:
        vendors = list(Vendor.objects.filter(status='Aktif')[:5])
    return vendors


def _gen_asset_code(tipe_cfg, company, existing_codes):
    """Generate kode aset unik per company."""
    prefix = tipe_cfg[1]  # e.g. 'KND-R4'
    # Ambil nomor urut terakhir di DB
    last = Asset.objects.filter(
        company=company, asset_code__startswith=prefix
    ).order_by('-asset_code').first()
    start = 1
    if last:
        try:
            start = int(last.asset_code.split('-')[-1]) + 1
        except Exception:
            start = Asset.objects.filter(company=company, asset_code__startswith=prefix).count() + 1

    for n in range(start, start + 9999):
        code = f'{prefix}-{n:04d}'
        if code not in existing_codes and not Asset.objects.filter(asset_code=code).exists():
            existing_codes.add(code)
            return code
    raise ValueError(f'Tidak bisa generate kode aset unik untuk prefix {prefix}')


def _generate_depreciation_bulk(asset):
    """Generate Depreciation records untuk satu asset (garis lurus)."""
    if asset.useful_life <= 0:
        return []
    purchase_price = float(asset.purchase_price)
    residual_value = float(asset.residual_value)
    monthly_dep = (purchase_price - residual_value) / (asset.useful_life * 12)
    total_months = asset.useful_life * 12
    year = asset.purchase_date.year
    month = asset.purchase_date.month
    accumulated = 0.0
    book_value = purchase_price
    entries = []
    for _ in range(total_months):
        accumulated += monthly_dep
        book_value  -= monthly_dep
        if book_value < 0:
            book_value = 0.0
        entries.append(Depreciation(
            asset=asset,
            year=year, month=month,
            monthly_depreciation=round(monthly_dep, 2),
            accumulated_depreciation=round(accumulated, 2),
            book_value=round(book_value, 2),
        ))
        month += 1
        if month > 12:
            month = 1; year += 1
    return entries


# ── Menu utama seed asset ─────────────────────────────────────────────────────

def menu_seed_asset():
    header('SEED ASSET MANAGEMENT')
    info('Seed data aset dummy per tipe — untuk testing QA & tampilan UX.')

    # 1. Pilih company
    targets = pilih_companies('Seed aset untuk company')
    if not targets:
        return

    # 2. Input jumlah per tipe aset
    print(f'\n{C}  Jumlah aset per tipe (Enter = 0 / skip):{RST}')
    info('Kosongkan / isi 0 untuk skip tipe tersebut.')
    print()

    jumlah = {}
    tipe_menu = [
        ('mobil',      '🚗  Kendaraan Roda 4 (Mobil)'),
        ('motor',      '🏍  Kendaraan Roda 2 (Motor)'),
        ('gedung',     '🏢  Gedung & Bangunan'),
        ('tanah',      '🌍  Tanah'),
        ('laptop',     '💻  Laptop & Komputer'),
        ('printer',    '🖨  Printer & Scanner'),
        ('furnitur',   '🪑  Furniture Kantor'),
        ('server',     '🖥  Server'),
        ('switch',     '🔌  Switch & Networking'),
        ('ap',         '📡  Access Point (WiFi)'),
        ('mesin',      '⚙️  Mesin & Peralatan Produksi'),
        ('ac',         '❄️  AC & Pendingin'),
        ('elektronik', '📺  Elektronik Umum'),
    ]

    for key, label in tipe_menu:
        while True:
            try:
                raw = input_prompt(f'{label}', default='0')
                n = int(raw or 0)
                if n < 0:
                    err('Tidak boleh negatif.')
                    continue
                jumlah[key] = n
                break
            except ValueError:
                err('Masukkan angka bulat.')

    total_aset = sum(jumlah.values())
    if total_aset == 0:
        warn('Semua tipe 0 — tidak ada yang di-generate.')
        return

    # 3. Input jumlah lokasi & vendor
    print(f'\n{C}  Setup Lokasi:{RST}')
    while True:
        try:
            n_gedung  = int(input_prompt('Jumlah gedung/area', default='2'))
            n_lantai  = int(input_prompt('Jumlah lantai per gedung', default='3'))
            n_ruangan = int(input_prompt('Jumlah ruangan per lantai', default='5'))
            if any(v < 0 for v in [n_gedung, n_lantai, n_ruangan]):
                err('Tidak boleh negatif.')
                continue
            break
        except ValueError:
            err('Masukkan angka bulat.')

    print(f'\n{C}  Setup Vendor:{RST}')
    while True:
        try:
            n_vendor = int(input_prompt('Jumlah vendor dummy', default='5'))
            if n_vendor < 0:
                err('Tidak boleh negatif.')
                continue
            break
        except ValueError:
            err('Masukkan angka bulat.')

    # 4. Opsi generate depresiasi
    print()
    gen_dep = confirm('Generate jadwal depresiasi untuk semua aset? (bisa lambat jika banyak)')

    # 5. Konfirmasi
    print()
    info('Ringkasan generate aset:')
    dim(f'  Company  : {", ".join(c.nama for c in targets)}')
    dim(f'  Total    : {total_aset} aset per company ({total_aset * len(targets)} total)')
    for key, label in tipe_menu:
        if jumlah[key] > 0:
            dim(f'  {label:<35}: {jumlah[key]}')
    dim(f'  Lokasi   : {n_gedung} gedung × {n_lantai} lantai × {n_ruangan} ruangan')
    dim(f'  Vendor   : {n_vendor} vendor')
    dim(f'  Depresiasi: {"Ya" if gen_dep else "Tidak"}')
    print()

    if not confirm('Lanjutkan generate?'):
        warn('Dibatalkan.')
        return

    # 6. Generate lokasi & vendor (shared, tidak per-company)
    print(f'\n{C}  [1/3] Generate lokasi...{RST}')
    if n_gedung > 0:
        lokasi_pool = _get_or_create_lokasi_pool(n_gedung, n_lantai, n_ruangan)
        ok(f'{len(lokasi_pool)} ruangan/area siap.')
    else:
        lokasi_pool = list(Location.objects.all()[:10])
        if not lokasi_pool:
            warn('Tidak ada lokasi — aset akan tanpa lokasi.')

    print(f'{C}  [2/3] Generate vendor...{RST}')
    if n_vendor > 0:
        vendor_pool = _get_or_create_vendor_pool(n_vendor)
        ok(f'{len(vendor_pool)} vendor siap.')
    else:
        vendor_pool = list(Vendor.objects.filter(status='Aktif')[:5])
        if not vendor_pool:
            warn('Tidak ada vendor — aset akan tanpa vendor.')

    # 7. Generate aset per company
    print(f'{C}  [3/3] Generate aset...{RST}')
    total_created   = 0
    total_dep_rows  = 0
    kondisi_choices = ['Baik', 'Baik', 'Baik', 'Rusak Ringan', 'Dalam Perbaikan']
    status_choices  = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'MAINTENANCE', 'RETIRED']

    for company in targets:
        emp_pool = list(Employee.objects.filter(company=company, status='Aktif')[:30])
        existing_codes = set()
        asset_bulk = []
        dep_parent_list = []  # list tipe asset untuk generate dep setelah bulk create

        for tipe_key, n in jumlah.items():
            if n == 0:
                continue
            cfg = _TIPE_ASET[tipe_key]
            # _, prefix, parent_cat, child_cat, harga_min, harga_max, useful_life, residual_pct
            harga_min   = cfg[4]
            harga_max   = cfg[5]
            useful_life = cfg[6]
            residual_pct= cfg[7]

            kategori = _get_or_create_kategori(company, cfg[2], cfg[3])

            for _ in range(n):
                nama, brand = _gen_asset_name_detail(tipe_key)
                kode = _gen_asset_code(cfg, company, existing_codes)
                tgl_beli = _rand_tanggal_beli()
                harga = random.randint(harga_min // 1000, harga_max // 1000) * 1000
                residual = int(harga * residual_pct / 100)

                asset_bulk.append(Asset(
                    company        = company,
                    asset_code     = kode,
                    asset_name     = nama,
                    category       = kategori,
                    purchase_date  = tgl_beli,
                    purchase_price = harga,
                    useful_life    = useful_life,
                    residual_value = residual,
                    serial_number  = _rand_serial() if tipe_key not in ('gedung', 'tanah') else '',
                    brand          = brand,
                    vendor         = random.choice(vendor_pool) if vendor_pool else None,
                    location       = random.choice(lokasi_pool)  if lokasi_pool else None,
                    responsible    = random.choice(emp_pool)     if emp_pool    else None,
                    status         = 'ACTIVE' if tipe_key in ('gedung', 'tanah') else random.choice(status_choices),
                    condition      = 'Baik'   if tipe_key in ('gedung', 'tanah') else random.choice(kondisi_choices),
                    warranty_date  = (tgl_beli + timedelta(days=random.choice([365, 730, 1095])))
                                     if tipe_key not in ('gedung', 'tanah') else None,
                ))

        # Bulk create aset
        created = Asset.objects.bulk_create(asset_bulk, ignore_conflicts=True)
        total_created += len(created)
        ok(f'{company.nama}: {len(created)} aset berhasil dibuat.')

        # Generate depresiasi jika diminta
        if gen_dep and created:
            dep_bulk = []
            # After bulk_create with ignore_conflicts=True, some databases (e.g. SQLite)
            # may return objects without PKs. Filter those out before generating depreciation.
            valid_assets = [a for a in created if a.pk is not None]
            for asset in valid_assets:
                dep_bulk.extend(_generate_depreciation_bulk(asset))
            if dep_bulk:
                Depreciation.objects.bulk_create(dep_bulk, ignore_conflicts=True, batch_size=2000)
                total_dep_rows += len(dep_bulk)
                ok(f'{company.nama}: {len(dep_bulk):,} baris depresiasi.')

    # 8. Ringkasan
    print(f'\n{B}{"─"*58}{RST}')
    print(f'  {W}Ringkasan Seed Aset{RST}')
    print(f'{B}{"─"*58}{RST}')
    ok(f'Total aset  : {total_created:,}')
    if gen_dep:
        ok(f'Depresiasi  : {total_dep_rows:,} baris')
    print()
    info('Cek hasil di: /asset/ — Daftar Aset')
    info('Cek laporan : /asset-reports/ — Dashboard Aset')
    if lokasi_pool:
        info(f'Lokasi      : /locations/ — {n_gedung} gedung, {n_lantai * n_gedung} lantai, {len(lokasi_pool)} ruangan')
    if vendor_pool:
        info(f'Vendor      : /vendors/ — {len(vendor_pool)} vendor')


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='HRIS SmartDesk — Seed Data')
    parser.add_argument('--company',    action='store_true', help='Langsung ke menu tambah company')
    parser.add_argument('--department', action='store_true', help='Langsung ke menu tambah department')
    parser.add_argument('--jabatan',    action='store_true', help='Langsung ke menu tambah jabatan manual')
    parser.add_argument('--preset',     action='store_true', help='Langsung ke menu jabatan preset 114 jabatan')
    parser.add_argument('--dummy',      action='store_true', help='Langsung ke menu generate karyawan dummy')
    parser.add_argument('--absensi',    action='store_true', help='Langsung ke menu generate absensi')
    parser.add_argument('--sync-dept',  action='store_true', help='Sync department ke jabatan dari data karyawan')
    parser.add_argument('--kandidat',   action='store_true', help='Langsung ke menu seed kandidat rekrutmen')
    parser.add_argument('--kontrak',    action='store_true', help='Langsung ke menu seed kontrak karyawan')
    parser.add_argument('--asset',      action='store_true', help='Langsung ke menu seed asset management')
    parser.add_argument('--list',       action='store_true', help='Langsung ke lihat data')
    args = parser.parse_args()

    try:
        if   args.company:    menu_tambah_company()
        elif args.department: menu_tambah_department()
        elif args.jabatan:    menu_tambah_jabatan()
        elif args.preset:     menu_jabatan_preset()
        elif getattr(args, 'sync_dept', False): menu_sync_department_jabatan()
        elif args.dummy:      menu_generate_dummy_karyawan()
        elif args.absensi:    menu_generate_absensi()
        elif args.kandidat:   menu_seed_kandidat()
        elif args.kontrak:    menu_seed_kontrak()
        elif args.asset:      menu_seed_asset()
        elif args.list:       menu_lihat_data()
        else:                 main_menu()
    except KeyboardInterrupt:
        print(f'\n\n{Y}  Dibatalkan.{RST}\n')