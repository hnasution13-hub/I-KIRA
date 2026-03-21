"""
seed_combined.py — i-Kira
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
            deskripsi = input_prompt('  Deskripsi (opsional)')
            departments.append({'nama': nama, 'kode': kode, 'deskripsi': deskripsi})
    else:
        print()
        info('Format: NamaDepartment, kode, deskripsi (kode & deskripsi opsional)')
        info('Contoh: Human Resources, HRD, Mengelola SDM perusahaan')
        info('        Finance & Accounting, FIN')
        lines = input_bulk('Daftar department')
        departments = []
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            nama      = parts[0] if parts else ''
            kode      = parts[1] if len(parts) > 1 else ''
            deskripsi = parts[2] if len(parts) > 2 else ''
            if nama:
                departments.append({'nama': nama, 'kode': kode, 'deskripsi': deskripsi})

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
                defaults={'kode': d['kode'], 'deskripsi': d.get('deskripsi', ''), 'aktif': True}
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

# ══════════════════════════════════════════════════════════════════════════════
#  PRESET DEPARTMENT & JABATAN PER INDUSTRI
# ══════════════════════════════════════════════════════════════════════════════

DEPT_PRESET = {

    'pertambangan': {
        'label': '⛏  Pertambangan (Mining)',
        'departments': [
            ('Mining',                    'MIN',  'Operasi penambangan di pit'),
            ('Civil & Maintenance',       'CIV',  'Pemeliharaan alat berat dan infrastruktur'),
            ('Electric & Water Facility', 'EWF',  'Pengelolaan listrik dan utilitas air'),
            ('Health Safety Environment', 'HSE',  'Keselamatan kerja dan lingkungan'),
            ('Human Resources',           'HR',   'Manajemen SDM dan rekrutmen'),
            ('General Affair',            'GA',   'Urusan umum dan fasilitas kantor'),
            ('Logistic',                  'LOG',  'Pengelolaan gudang dan distribusi'),
            ('Purchasing',                'PURCH','Pengadaan barang dan jasa'),
            ('Finance & Accounting',      'FIN',  'Keuangan, akuntansi, dan pajak'),
            ('Infrastructure Technology', 'IT',   'Infrastruktur teknologi informasi'),
            ('Legal',                     'LGL',  'Urusan hukum dan kepatuhan'),
            ('Security',                  'SEC',  'Keamanan area tambang'),
        ],
        'jabatan': [
            # Mining
            ('Operator ADT',               'Staff',           'Mining'),
            ('Operator Excavator',         'Staff',           'Mining'),
            ('Operator Dozer',             'Staff',           'Mining'),
            ('Operator Grader',            'Staff',           'Mining'),
            ('Operator Loader',            'Staff',           'Mining'),
            ('Surveyor',                   'Staff',           'Mining'),
            ('Mine Dispatcher',            'Staff',           'Mining'),
            ('Drill & Blast Officer',      'Staff',           'Mining'),
            ('Mine Engineer',              'Staff',           'Mining'),
            ('Senior Mine Engineer',       'Senior Staff',    'Mining'),
            ('Mine Foreman',               'Supervisor',      'Mining'),
            ('Pit Supervisor',             'Supervisor',      'Mining'),
            ('Mining Superintendent',      'Senior Supervisor','Mining'),
            ('Mine Manager',               'Manager',         'Mining'),
            # Civil & Maintenance
            ('Mechanic',                   'Staff',           'Civil & Maintenance'),
            ('Helper Mechanic',            'Staff',           'Civil & Maintenance'),
            ('Welder',                     'Staff',           'Civil & Maintenance'),
            ('Technician',                 'Staff',           'Civil & Maintenance'),
            ('Maintenance Planner',        'Staff',           'Civil & Maintenance'),
            ('Senior Mechanic',            'Senior Staff',    'Civil & Maintenance'),
            ('Foreman Mechanic',           'Supervisor',      'Civil & Maintenance'),
            ('Workshop Supervisor',        'Supervisor',      'Civil & Maintenance'),
            ('Maintenance Superintendent', 'Senior Supervisor','Civil & Maintenance'),
            ('Maintenance Manager',        'Manager',         'Civil & Maintenance'),
            # Electric & Water Facility
            ('Electrician',                'Staff',           'Electric & Water Facility'),
            ('Genset Operator',            'Staff',           'Electric & Water Facility'),
            ('Water Pump Operator',        'Staff',           'Electric & Water Facility'),
            ('Electrical Technician',      'Staff',           'Electric & Water Facility'),
            ('Electrical Engineer',        'Staff',           'Electric & Water Facility'),
            ('Senior Electrical Engineer', 'Senior Staff',    'Electric & Water Facility'),
            ('Electrical Supervisor',      'Supervisor',      'Electric & Water Facility'),
            ('Electrical Superintendent',  'Senior Supervisor','Electric & Water Facility'),
            ('Utility Manager',            'Manager',         'Electric & Water Facility'),
            # HSE
            ('Safety Patrol',              'Staff',           'Health Safety Environment'),
            ('Firefighter',                'Staff',           'Health Safety Environment'),
            ('Safety Officer',             'Staff',           'Health Safety Environment'),
            ('Environmental Officer',      'Staff',           'Health Safety Environment'),
            ('Senior Safety Officer',      'Senior Staff',    'Health Safety Environment'),
            ('Safety Supervisor',          'Supervisor',      'Health Safety Environment'),
            ('HSE Superintendent',         'Senior Supervisor','Health Safety Environment'),
            ('HSE Manager',               'Manager',         'Health Safety Environment'),
            # HR
            ('HR Admin',                   'Staff',           'Human Resources'),
            ('Recruitment Officer',        'Staff',           'Human Resources'),
            ('Training Officer',           'Staff',           'Human Resources'),
            ('HR Generalist',              'Senior Staff',    'Human Resources'),
            ('HR Supervisor',              'Supervisor',      'Human Resources'),
            ('HR Superintendent',          'Senior Supervisor','Human Resources'),
            ('HR Manager',                'Manager',         'Human Resources'),
            # GA
            ('Office Boy',                 'Staff',           'General Affair'),
            ('Driver',                     'Staff',           'General Affair'),
            ('GA Officer',                 'Staff',           'General Affair'),
            ('Mess & Camp Officer',        'Staff',           'General Affair'),
            ('Senior GA Officer',          'Senior Staff',    'General Affair'),
            ('GA Supervisor',              'Supervisor',      'General Affair'),
            ('GA Manager',                'Manager',         'General Affair'),
            # Logistic
            ('Warehouse Helper',           'Staff',           'Logistic'),
            ('Storekeeper',                'Staff',           'Logistic'),
            ('Logistic Officer',           'Staff',           'Logistic'),
            ('Senior Logistic Officer',    'Senior Staff',    'Logistic'),
            ('Warehouse Supervisor',       'Supervisor',      'Logistic'),
            ('Logistic Manager',          'Manager',         'Logistic'),
            # Purchasing
            ('Purchasing Admin',           'Staff',           'Purchasing'),
            ('Procurement Officer',        'Staff',           'Purchasing'),
            ('Senior Procurement Officer', 'Senior Staff',    'Purchasing'),
            ('Procurement Supervisor',     'Supervisor',      'Purchasing'),
            ('Procurement Manager',       'Manager',         'Purchasing'),
            # Finance
            ('Finance Admin',              'Staff',           'Finance & Accounting'),
            ('Accountant',                 'Staff',           'Finance & Accounting'),
            ('Tax Officer',                'Staff',           'Finance & Accounting'),
            ('Senior Accountant',          'Senior Staff',    'Finance & Accounting'),
            ('Finance Supervisor',         'Supervisor',      'Finance & Accounting'),
            ('Finance Manager',           'Manager',         'Finance & Accounting'),
            # IT
            ('IT Support',                 'Staff',           'Infrastructure Technology'),
            ('Network Engineer',           'Staff',           'Infrastructure Technology'),
            ('System Administrator',       'Senior Staff',    'Infrastructure Technology'),
            ('IT Supervisor',              'Supervisor',      'Infrastructure Technology'),
            ('IT Manager',                'Manager',         'Infrastructure Technology'),
            # Legal
            ('Legal Admin',                'Staff',           'Legal'),
            ('Legal Officer',              'Staff',           'Legal'),
            ('Senior Legal Officer',       'Senior Staff',    'Legal'),
            ('Legal Supervisor',           'Supervisor',      'Legal'),
            ('Legal Manager',             'Manager',         'Legal'),
            # Security
            ('Security Guard',             'Staff',           'Security'),
            ('Security Officer',           'Staff',           'Security'),
            ('Senior Security Officer',    'Senior Staff',    'Security'),
            ('Security Supervisor',        'Supervisor',      'Security'),
            ('Security Manager',          'Manager',         'Security'),
            # Direksi
            ('Site Manager',               'Sr.Manager',          None),
            ('Operations Director',        'Manajemen',           None),
            ('Finance Director',           'Manajemen',           None),
            ('HR Director',                'Manajemen',           None),
            ('Managing Director',          'Corporate Manajemen', None),
        ],
    },

    'retail': {
        'label': '🏪  Retail',
        'departments': [
            ('Store Operations',    'OPS',  'Operasional toko dan pelayanan pelanggan'),
            ('Merchandising',       'MRCH', 'Pengelolaan produk dan display toko'),
            ('Sales & Marketing',   'SALES','Penjualan dan promosi'),
            ('Inventory & Warehouse','INV', 'Pengelolaan stok dan gudang'),
            ('Human Resources',     'HR',   'Manajemen SDM dan rekrutmen'),
            ('Finance & Accounting','FIN',  'Keuangan, akuntansi, dan pajak'),
            ('Customer Service',    'CS',   'Layanan dan kepuasan pelanggan'),
            ('IT & Digital',        'IT',   'Teknologi informasi dan e-commerce'),
            ('General Affair',      'GA',   'Urusan umum dan fasilitas'),
            ('Security',            'SEC',  'Keamanan toko'),
        ],
        'jabatan': [
            # Store Operations
            ('Kasir',                      'Staff',        'Store Operations'),
            ('Sales Associate',            'Staff',        'Store Operations'),
            ('Pramuniaga',                 'Staff',        'Store Operations'),
            ('Senior Kasir',               'Senior Staff', 'Store Operations'),
            ('Kepala Kasir',               'Supervisor',   'Store Operations'),
            ('Store Supervisor',           'Supervisor',   'Store Operations'),
            ('Assistant Store Manager',    'Manager',      'Store Operations'),
            ('Store Manager',              'Manager',      'Store Operations'),
            ('Area Manager',               'Senior Manager','Store Operations'),
            # Merchandising
            ('Merchandiser',               'Staff',        'Merchandising'),
            ('Visual Merchandiser',        'Staff',        'Merchandising'),
            ('Senior Merchandiser',        'Senior Staff', 'Merchandising'),
            ('Merchandising Supervisor',   'Supervisor',   'Merchandising'),
            ('Merchandising Manager',      'Manager',      'Merchandising'),
            # Sales & Marketing
            ('Marketing Staff',            'Staff',        'Sales & Marketing'),
            ('Social Media Specialist',    'Staff',        'Sales & Marketing'),
            ('Brand Promotor',             'Staff',        'Sales & Marketing'),
            ('Senior Marketing Staff',     'Senior Staff', 'Sales & Marketing'),
            ('Marketing Supervisor',       'Supervisor',   'Sales & Marketing'),
            ('Marketing Manager',          'Manager',      'Sales & Marketing'),
            # Inventory
            ('Warehouse Staff',            'Staff',        'Inventory & Warehouse'),
            ('Stock Checker',              'Staff',        'Inventory & Warehouse'),
            ('Inventory Control Officer',  'Senior Staff', 'Inventory & Warehouse'),
            ('Warehouse Supervisor',       'Supervisor',   'Inventory & Warehouse'),
            ('Inventory Manager',          'Manager',      'Inventory & Warehouse'),
            # HR
            ('HR Admin',                   'Staff',        'Human Resources'),
            ('Recruitment Officer',        'Staff',        'Human Resources'),
            ('Training Officer',           'Staff',        'Human Resources'),
            ('HR Supervisor',              'Supervisor',   'Human Resources'),
            ('HR Manager',                'Manager',      'Human Resources'),
            # Finance
            ('Finance Admin',              'Staff',        'Finance & Accounting'),
            ('Accountant',                 'Staff',        'Finance & Accounting'),
            ('Tax Officer',                'Staff',        'Finance & Accounting'),
            ('Finance Supervisor',         'Supervisor',   'Finance & Accounting'),
            ('Finance Manager',           'Manager',      'Finance & Accounting'),
            # Customer Service
            ('Customer Service Officer',   'Staff',        'Customer Service'),
            ('Senior CS Officer',          'Senior Staff', 'Customer Service'),
            ('CS Supervisor',              'Supervisor',   'Customer Service'),
            ('CS Manager',                'Manager',      'Customer Service'),
            # IT
            ('IT Support',                 'Staff',        'IT & Digital'),
            ('Web Developer',              'Staff',        'IT & Digital'),
            ('Digital Marketing Staff',    'Staff',        'IT & Digital'),
            ('IT Supervisor',              'Supervisor',   'IT & Digital'),
            ('IT Manager',                'Manager',      'IT & Digital'),
            # GA
            ('Office Boy',                 'Staff',        'General Affair'),
            ('Driver',                     'Staff',        'General Affair'),
            ('GA Officer',                 'Staff',        'General Affair'),
            ('GA Supervisor',              'Supervisor',   'General Affair'),
            # Security
            ('Security Guard',             'Staff',        'Security'),
            ('Security Supervisor',        'Supervisor',   'Security'),
            # Direksi
            ('Operations Director',        'Manajemen',           None),
            ('Finance Director',           'Manajemen',           None),
            ('Managing Director',          'Corporate Manajemen', None),
        ],
    },

    'manufaktur': {
        'label': '🏭  Manufaktur (Manufacturing)',
        'departments': [
            ('Production',          'PROD', 'Proses produksi dan line manufacturing'),
            ('Quality Control',     'QC',   'Pengendalian kualitas produk'),
            ('Engineering',         'ENG',  'Rekayasa dan pengembangan proses'),
            ('Maintenance',         'MAINT','Pemeliharaan mesin dan fasilitas produksi'),
            ('Warehouse & Logistic','LOG',  'Pergudangan bahan baku dan produk jadi'),
            ('Purchasing',          'PURCH','Pengadaan bahan baku dan material'),
            ('Human Resources',     'HR',   'Manajemen SDM dan rekrutmen'),
            ('Finance & Accounting','FIN',  'Keuangan, akuntansi, dan pajak'),
            ('Health Safety Environment','HSE','Keselamatan kerja dan lingkungan'),
            ('General Affair',      'GA',   'Urusan umum dan fasilitas'),
            ('IT',                  'IT',   'Infrastruktur teknologi informasi'),
            ('Sales & Marketing',   'SALES','Penjualan dan pemasaran produk'),
        ],
        'jabatan': [
            # Production
            ('Operator Produksi',          'Staff',        'Production'),
            ('Helper Produksi',            'Staff',        'Production'),
            ('Senior Operator',            'Senior Staff', 'Production'),
            ('Leader Produksi',            'Supervisor',   'Production'),
            ('Foreman Produksi',           'Supervisor',   'Production'),
            ('Production Supervisor',      'Supervisor',   'Production'),
            ('Production Superintendent',  'Senior Supervisor','Production'),
            ('Production Manager',         'Manager',      'Production'),
            # Quality Control
            ('QC Inspector',               'Staff',        'Quality Control'),
            ('QC Analyst',                 'Staff',        'Quality Control'),
            ('Senior QC Inspector',        'Senior Staff', 'Quality Control'),
            ('QC Supervisor',              'Supervisor',   'Quality Control'),
            ('QC Manager',                'Manager',      'Quality Control'),
            # Engineering
            ('Process Engineer',           'Staff',        'Engineering'),
            ('Product Engineer',           'Staff',        'Engineering'),
            ('Industrial Engineer',        'Staff',        'Engineering'),
            ('Senior Engineer',            'Senior Staff', 'Engineering'),
            ('Engineering Supervisor',     'Supervisor',   'Engineering'),
            ('Engineering Manager',        'Manager',      'Engineering'),
            # Maintenance
            ('Technician Mesin',           'Staff',        'Maintenance'),
            ('Electrician',                'Staff',        'Maintenance'),
            ('Mechanic',                   'Staff',        'Maintenance'),
            ('Senior Technician',          'Senior Staff', 'Maintenance'),
            ('Maintenance Supervisor',     'Supervisor',   'Maintenance'),
            ('Maintenance Manager',        'Manager',      'Maintenance'),
            # Warehouse
            ('Warehouse Staff',            'Staff',        'Warehouse & Logistic'),
            ('Driver Forklift',            'Staff',        'Warehouse & Logistic'),
            ('Inventory Control',          'Senior Staff', 'Warehouse & Logistic'),
            ('Warehouse Supervisor',       'Supervisor',   'Warehouse & Logistic'),
            ('Logistic Manager',          'Manager',      'Warehouse & Logistic'),
            # Purchasing
            ('Purchasing Admin',           'Staff',        'Purchasing'),
            ('Procurement Officer',        'Staff',        'Purchasing'),
            ('Senior Procurement Officer', 'Senior Staff', 'Purchasing'),
            ('Procurement Supervisor',     'Supervisor',   'Purchasing'),
            ('Procurement Manager',       'Manager',      'Purchasing'),
            # HR
            ('HR Admin',                   'Staff',        'Human Resources'),
            ('Recruitment Officer',        'Staff',        'Human Resources'),
            ('Training Officer',           'Staff',        'Human Resources'),
            ('HR Supervisor',              'Supervisor',   'Human Resources'),
            ('HR Manager',                'Manager',      'Human Resources'),
            # Finance
            ('Finance Admin',              'Staff',        'Finance & Accounting'),
            ('Accountant',                 'Staff',        'Finance & Accounting'),
            ('Tax Officer',                'Staff',        'Finance & Accounting'),
            ('Finance Supervisor',         'Supervisor',   'Finance & Accounting'),
            ('Finance Manager',           'Manager',      'Finance & Accounting'),
            # HSE
            ('Safety Officer',             'Staff',        'Health Safety Environment'),
            ('Environmental Officer',      'Staff',        'Health Safety Environment'),
            ('Senior Safety Officer',      'Senior Staff', 'Health Safety Environment'),
            ('HSE Supervisor',             'Supervisor',   'Health Safety Environment'),
            ('HSE Manager',               'Manager',      'Health Safety Environment'),
            # GA
            ('Office Boy',                 'Staff',        'General Affair'),
            ('Driver',                     'Staff',        'General Affair'),
            ('GA Officer',                 'Staff',        'General Affair'),
            ('GA Supervisor',              'Supervisor',   'General Affair'),
            # IT
            ('IT Support',                 'Staff',        'IT'),
            ('Network Engineer',           'Staff',        'IT'),
            ('IT Supervisor',              'Supervisor',   'IT'),
            ('IT Manager',                'Manager',      'IT'),
            # Sales
            ('Sales Executive',            'Staff',        'Sales & Marketing'),
            ('Marketing Staff',            'Staff',        'Sales & Marketing'),
            ('Senior Sales Executive',     'Senior Staff', 'Sales & Marketing'),
            ('Sales Supervisor',           'Supervisor',   'Sales & Marketing'),
            ('Sales Manager',             'Manager',      'Sales & Marketing'),
            # Direksi
            ('Plant Manager',              'Sr.Manager',          None),
            ('Operations Director',        'Manajemen',           None),
            ('Finance Director',           'Manajemen',           None),
            ('Managing Director',          'Corporate Manajemen', None),
        ],
    },
}


def menu_department_preset():
    header('TAMBAH DEPARTMENT & JABATAN PRESET PER INDUSTRI')

    # Pilih industri
    industri_keys  = list(DEPT_PRESET.keys())
    industri_labels = [DEPT_PRESET[k]['label'] for k in industri_keys]
    idx = pilih_menu(industri_labels, title='Pilih industri')
    key = industri_keys[idx]
    preset = DEPT_PRESET[key]

    info(f'Industri: {preset["label"]}')
    info(f'{len(preset["departments"])} department, {len(preset["jabatan"])} jabatan.')

    targets = pilih_companies('Apply ke company')
    if not targets:
        return

    # Opsi: dept saja, jabatan saja, atau keduanya
    mode_idx = pilih_menu(
        ['Department + Jabatan (lengkap)', 'Department saja', 'Jabatan saja'],
        title='Yang ingin di-insert'
    )

    print()
    if not confirm(f'Insert preset {preset["label"]} ke {len(targets)} company?'):
        warn('Dibatalkan.'); return

    for company in targets:
        dept_created = dept_skip = jab_created = jab_skip = 0

        # ── Insert department ──────────────────────────────────────────────
        if mode_idx in (0, 1):
            for nama, kode, deskripsi in preset['departments']:
                _, is_new = Department.objects.get_or_create(
                    company=company, nama=nama,
                    defaults={'kode': kode, 'deskripsi': deskripsi, 'aktif': True}
                )
                if is_new: dept_created += 1
                else:      dept_skip    += 1

        # ── Insert jabatan ─────────────────────────────────────────────────
        if mode_idx in (0, 2):
            dept_map = {d.nama: d for d in Department.objects.filter(company=company)}
            for nama, level, dept_nama in preset['jabatan']:
                dept_obj = None
                if dept_nama:
                    # cari exact dulu, fallback icontains
                    dept_obj = dept_map.get(dept_nama)
                    if not dept_obj:
                        dept_obj = next(
                            (d for n, d in dept_map.items() if dept_nama.lower() in n.lower()),
                            None
                        )
                _, is_new = Position.objects.get_or_create(
                    company=company, nama=nama,
                    defaults={'level': level, 'department': dept_obj, 'aktif': True}
                )
                if is_new: jab_created += 1
                else:      jab_skip    += 1

        print(f'\n{W}  {company.nama}:{RST}')
        if mode_idx in (0, 1):
            ok(f'Department : {dept_created} dibuat, {dept_skip} sudah ada.')
        if mode_idx in (0, 2):
            ok(f'Jabatan    : {jab_created} dibuat, {jab_skip} sudah ada.')

    print()
    ok('Selesai!')


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
    ("Site Superintendent",             "Sr.Superintendent"),
    ("Site Manager",                    "Sr.Manager"),

    # Corporate Management
    ("Operations Director",             "Manajemen"),
    ("Finance Director",                "Manajemen"),
    ("HR Director",                     "Manajemen"),
    ("Managing Director",               "Corporate Manajemen"),
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
        ('Site Manager',      'Sr.Manager'),
        ('HR Director',       'Manajemen'),
        ('Managing Director', 'Corporate Manajemen'),
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

def menu_seed_salary_benefit():
    header('SEED SALARY BENEFIT (Upah & Tunjangan)')
    from apps.payroll.models import SalaryBenefit

    targets = pilih_companies('Seed salary benefit untuk company')
    if not targets:
        return

    company_ids  = [c.pk for c in targets]
    employees    = list(Employee.objects.filter(company__in=company_ids, status='Aktif')
                        .select_related('jabatan'))
    existing_ids = set(SalaryBenefit.objects.filter(
        employee__in=[e.pk for e in employees]
    ).values_list('employee_id', flat=True))
    targets_emp  = [e for e in employees if e.pk not in existing_ids]

    info(f'{len(employees)} karyawan aktif, {len(existing_ids)} sudah punya SalaryBenefit.')
    if not targets_emp:
        warn('Semua karyawan sudah punya SalaryBenefit.')
        return
    info(f'{len(targets_emp)} karyawan akan di-seed.')

    print(f'\n{C}  Konfigurasi default:{RST}')
    jenis_idx    = pilih_menu(['bulanan', 'mingguan', 'harian'], title='Jenis Pengupahan')
    jenis_map    = ['bulanan', 'mingguan', 'harian']
    jenis        = jenis_map[jenis_idx]
    hari_idx     = pilih_menu(['5 Hari (Senin–Jumat)', '6 Hari (Senin–Sabtu)'], title='Hari Kerja')
    hari_kerja   = 5 if hari_idx == 0 else 6
    status_idx   = pilih_menu(['reguler', 'all_in'], title='Status Gaji')
    status_gaji  = 'reguler' if status_idx == 0 else 'all_in'
    pph_tangggung = confirm('PPh21 ditanggung perusahaan?')

    print(f'\n{C}  Range tunjangan (% dari gaji pokok) — isi 0,0 untuk skip:{RST}')
    def _pct_range(label, d1, d2):
        while True:
            try:
                a = int(input_prompt(f'  {label} min %', default=str(d1)))
                b = int(input_prompt(f'  {label} max %', default=str(d2)))
                if a < 0 or b < 0 or a > b: err('Range tidak valid.'); continue
                return a, b
            except ValueError: err('Angka saja.')

    pct_jabatan    = _pct_range('Tunjangan Jabatan',        5, 20)
    pct_tinggal    = _pct_range('Tunjangan Tempat Tinggal', 0, 15)
    pct_keahlian   = _pct_range('Tunjangan Keahlian',       0, 10)
    pct_komunikasi = _pct_range('Tunjangan Komunikasi',     0,  5)
    pct_kesehatan  = _pct_range('Tunjangan Kesehatan',      0,  5)
    pct_transport  = _pct_range('Tunjangan Transport',      3, 10)
    pct_makan      = _pct_range('Tunjangan Makan',          2,  8)
    pct_site       = _pct_range('Tunjangan Site',           0, 20)
    pct_kehadiran  = _pct_range('Tunjangan Kehadiran',      0,  5)

    print()
    if not confirm(f'Generate SalaryBenefit untuk {len(targets_emp)} karyawan?'):
        warn('Dibatalkan.'); return

    def _calc(gaji, pct_range):
        a, b = pct_range
        if a == 0 and b == 0: return 0
        pct = random.randint(a, b)
        return round(gaji * pct / 100 / 1000) * 1000

    bulk = []
    for emp in targets_emp:
        gaji = int(emp.gaji_pokok) if emp.gaji_pokok else 3_000_000
        bulk.append(SalaryBenefit(
            employee                   = emp,
            jenis_pengupahan           = jenis,
            hari_kerja_per_minggu      = hari_kerja,
            status_gaji                = status_gaji,
            gaji_pokok                 = gaji,
            tunjangan_jabatan          = _calc(gaji, pct_jabatan),
            tunjangan_tempat_tinggal   = _calc(gaji, pct_tinggal),
            tunjangan_keahlian         = _calc(gaji, pct_keahlian),
            tunjangan_komunikasi       = _calc(gaji, pct_komunikasi),
            tunjangan_kesehatan        = _calc(gaji, pct_kesehatan),
            tunjangan_transport        = _calc(gaji, pct_transport),
            tunjangan_makan            = _calc(gaji, pct_makan),
            tunjangan_site             = _calc(gaji, pct_site),
            tunjangan_kehadiran        = _calc(gaji, pct_kehadiran),
            pph21_ditanggung_perusahaan= pph_tangggung,
            # BPJS otomatis (0 = hitung dari gaji pokok sesuai PP 36/2021)
            bpjs_ketenagakerjaan_override = 0,
            bpjs_kesehatan_override       = 0,
            # Lembur otomatis (0 = gaji_pokok/173)
            lembur_tarif_per_jam          = 0,
            # Potongan absensi otomatis (0 = upah harian)
            potongan_absensi              = 0,
            potongan_lainnya              = 0,
        ))

    SalaryBenefit.objects.bulk_create(bulk, ignore_conflicts=True)
    ok(f'{len(bulk)} SalaryBenefit berhasil dibuat.')
    info('BPJS & lembur dihitung otomatis saat generate payroll.')


def menu_seed_candidate_profile():
    header('SEED PROFIL LENGKAP KANDIDAT')
    from apps.recruitment.models import Candidate
    from apps.recruitment.models_profile import CandidateProfile, CandidateAnak

    targets = pilih_companies('Seed profil kandidat untuk company')
    if not targets:
        return

    company_ids = [c.pk for c in targets]
    candidates  = list(Candidate.objects.filter(mprf__company__in=company_ids))
    # kandidat tanpa mprf (company tidak ter-filter) — ambil semua jika tidak ada
    if not candidates:
        candidates = list(Candidate.objects.all())

    existing_ids = set(CandidateProfile.objects.filter(
        candidate__in=[c.pk for c in candidates]
    ).values_list('candidate_id', flat=True))
    targets_cand = [c for c in candidates if c.pk not in existing_ids]

    info(f'{len(candidates)} kandidat, {len(existing_ids)} sudah punya profil.')
    if not targets_cand:
        warn('Semua kandidat sudah punya profil.')
        return
    info(f'{len(targets_cand)} kandidat akan di-seed profil.')

    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.'); return

    _BANK      = ['BCA','BRI','BNI','Mandiri','BSI','CIMB Niaga','Danamon','BTN']
    _AGAMA     = ['Islam','Islam','Islam','Kristen','Katolik','Hindu','Buddha']
    _GOLDAR    = ['A','B','AB','O','A','O','B','O']
    _ST_NIKAH  = ['Lajang','Lajang','Menikah','Menikah','Cerai']
    _PTKP_L    = ['TK/0','K/0','K/1','K/2']
    _PTKP_P    = ['TK/0','TK/0','K/0','K/1']
    _PEND      = ['SMA/SMK','SMA/SMK','D3','D4/S1','D4/S1','S2']
    _JALAN     = ['Jl. Merdeka','Jl. Sudirman','Jl. Ahmad Yani','Jl. Diponegoro',
                  'Jl. Pahlawan','Jl. Pemuda','Jl. Kartini','Jl. Veteran']
    _KELURAHAN = ['Kebayoran','Menteng','Tebet','Gambir','Senen','Lowokwaru','Blimbing']
    _KECAMATAN = ['Kebayoran Baru','Menteng','Tebet','Gambir','Senen','Lowokwaru','Blimbing']
    _HUB       = ['Istri','Suami','Ayah','Ibu','Kakak','Adik','Saudara']
    _NAMA_DAR_L = ['Budi','Ahmad','Hendra','Agus','Wahyu']
    _NAMA_DAR_P = ['Sari','Dewi','Rina','Ani','Wati']
    _ANAK_L    = ['Bima','Arjuna','Raka','Dafa','Farhan']
    _ANAK_P    = ['Naura','Kirana','Azahra','Nabila','Salsabila']

    bulk_profile = []
    bulk_anak    = []

    for cand in targets_cand:
        # Deteksi gender dari nama — heuristic sederhana
        nama_lower = cand.nama.lower().split()[0] if cand.nama else ''
        jk = 'P' if any(n in nama_lower for n in ['sari','dewi','putri','rina','ani',
             'wati','fitri','nita','yuni','mega','novia','indah','ratna','ayu',
             'bunga','dina','gita','hana','ira','julia','lina','mira','nisa']) else 'L'

        st_nikah  = random.choice(_ST_NIKAH)
        jml_anak  = random.randint(0, 3) if st_nikah == 'Menikah' else 0
        tgl_lahir = date(random.randint(1980, 2000), random.randint(1,12), random.randint(1,28))
        ptkp      = random.choice(_PTKP_L if jk == 'L' else _PTKP_P)
        kota      = random.choice(_KOTA)
        hub       = random.choice(_HUB)
        pool_dar  = _NAMA_DAR_L if random.random() < 0.5 else _NAMA_DAR_P
        nama_dar  = random.choice(pool_dar) + ' ' + random.choice(_NAMA_BELAKANG)

        p = CandidateProfile(
            candidate       = cand,
            is_submitted    = True,
            is_reviewed     = random.random() < 0.6,
            tempat_lahir    = kota,
            tanggal_lahir   = tgl_lahir,
            jenis_kelamin   = jk,
            agama           = random.choice(_AGAMA),
            pendidikan      = random.choice(_PEND),
            golongan_darah  = random.choice(_GOLDAR),
            status_nikah    = st_nikah,
            jumlah_anak     = jml_anak,
            ptkp            = ptkp,
            no_ktp          = ''.join([str(random.randint(0,9)) for _ in range(16)]),
            no_kk           = ''.join([str(random.randint(0,9)) for _ in range(16)]),
            no_npwp         = f'{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(1,9)}-{random.randint(100,999)}.{random.randint(100,999)}',
            no_bpjs_kes     = ''.join([str(random.randint(0,9)) for _ in range(13)]),
            no_bpjs_tk      = ''.join([str(random.randint(0,9)) for _ in range(11)]),
            no_rek          = ''.join([str(random.randint(0,9)) for _ in range(random.randint(10,13))]),
            nama_bank       = random.choice(_BANK),
            nama_rek        = cand.nama,
            alamat          = f'{random.choice(_JALAN)} No.{random.randint(1,99)}',
            rt              = f'{random.randint(1,20):03d}',
            rw              = f'{random.randint(1,10):03d}',
            kode_pos        = str(random.randint(10000, 99999)),
            kecamatan       = random.choice(_KECAMATAN),
            kelurahan       = random.choice(_KELURAHAN),
            nama_darurat    = nama_dar,
            hub_darurat     = hub,
            hp_darurat      = f'08{random.randint(100000000, 999999999)}',
        )
        bulk_profile.append(p)

        for urutan in range(1, jml_anak + 1):
            jk_anak = random.choice(['L','P'])
            bulk_anak.append((cand, urutan,
                random.choice(_ANAK_L if jk_anak == 'L' else _ANAK_P),
                jk_anak,
                date(random.randint(2005,2020), random.randint(1,12), random.randint(1,28))))

    CandidateProfile.objects.bulk_create(bulk_profile, ignore_conflicts=True)
    ok(f'{len(bulk_profile)} profil kandidat berhasil dibuat.')

    # Buat anak setelah profil tersimpan (butuh PK)
    if bulk_anak:
        profile_map = {p.candidate_id: p for p in
                       CandidateProfile.objects.filter(candidate__in=[c.pk for c in targets_cand])}
        anak_bulk = []
        for cand, urutan, nama, jk_anak, tgl in bulk_anak:
            prof = profile_map.get(cand.pk)
            if prof:
                anak_bulk.append(CandidateAnak(
                    profile=prof, urutan=urutan, nama=nama,
                    jenis_kelamin=jk_anak, tgl_lahir=tgl,
                    no_bpjs_kes=''.join([str(random.randint(0,9)) for _ in range(13)])
                ))
        if anak_bulk:
            CandidateAnak.objects.bulk_create(anak_bulk, ignore_conflicts=True)
            ok(f'{len(anak_bulk)} data anak kandidat berhasil dibuat.')



# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED SHIFT KERJA
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_shift():
    header('SEED SHIFT KERJA')
    from datetime import time as dtime
    from apps.shifts.models import Shift

    targets = pilih_companies('Seed shift untuk company')
    if not targets:
        return

    SHIFT_PRESET = [
        # (nama, kode, tipe, jam_masuk, jam_keluar, warna, hari_kerja)
        ('Shift Pagi',   'PAGI',  'fixed',    dtime(7, 0),  dtime(15, 0), '#2563eb', '0,1,2,3,4'),
        ('Shift Siang',  'SIANG', 'fixed',    dtime(15, 0), dtime(23, 0), '#d97706', '0,1,2,3,4'),
        ('Shift Malam',  'MALAM', 'fixed',    dtime(23, 0), dtime(7, 0),  '#7c3aed', '0,1,2,3,4'),
        ('Normal Office','NORM',  'fixed',    dtime(8, 0),  dtime(17, 0), '#059669', '0,1,2,3,4'),
        ('Shift Sabtu',  'SAB',   'fixed',    dtime(8, 0),  dtime(14, 0), '#db2777', '0,1,2,3,4,5'),
        ('Flexible WFA', 'FLEX',  'flexible', None,         None,         '#64748b', '0,1,2,3,4'),
    ]

    created = skipped = 0
    for company in targets:
        for nama, kode, tipe, masuk, keluar, warna, hari in SHIFT_PRESET:
            obj, is_new = Shift.objects.get_or_create(
                company=company, kode=kode,
                defaults={
                    'nama': nama, 'tipe': tipe,
                    'jam_masuk': masuk, 'jam_keluar': keluar,
                    'warna': warna, 'hari_kerja': hari, 'aktif': True,
                }
            )
            if is_new: created += 1
            else:      skipped += 1

    ok(f'{created} shift berhasil dibuat, {skipped} sudah ada.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED KPI TEMPLATE (Performance)
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_kpi_template():
    header('SEED KPI TEMPLATE')
    from apps.performance.models import KPITemplate

    KPI_PRESET = [
        # (nama, satuan, arah, kategori)
        ('Tingkat Kehadiran',                    '%',      'tinggi', 'SDM'),
        ('Tingkat Ketepatan Waktu Hadir',         '%',      'tinggi', 'SDM'),
        ('Jumlah Pelanggaran Disiplin',           'angka',  'rendah', 'SDM'),
        ('Penyelesaian Training Wajib',           '%',      'tinggi', 'SDM'),
        ('Skor Penilaian Kompetensi',             'angka',  'tinggi', 'SDM'),
        ('Revenue Target Achievement',            '%',      'tinggi', 'Keuangan'),
        ('Cost Efficiency Ratio',                 '%',      'rendah', 'Keuangan'),
        ('Budget Realization Accuracy',           '%',      'tinggi', 'Keuangan'),
        ('Net Profit Margin',                     '%',      'tinggi', 'Keuangan'),
        ('Accounts Receivable Days',              'hari',   'rendah', 'Keuangan'),
        ('Customer Satisfaction Score (CSAT)',    '%',      'tinggi', 'Pelanggan'),
        ('Customer Complaint Resolution Rate',    '%',      'tinggi', 'Pelanggan'),
        ('On-Time Delivery Rate',                 '%',      'tinggi', 'Pelanggan'),
        ('Net Promoter Score (NPS)',              'angka',  'tinggi', 'Pelanggan'),
        ('Defect Rate / Reject Rate',             '%',      'rendah', 'Proses'),
        ('Process Cycle Time',                    'jam',    'rendah', 'Proses'),
        ('Equipment Availability',                '%',      'tinggi', 'Proses'),
        ('Safety Incident Rate',                  'angka',  'rendah', 'Proses'),
        ('Work Order Completion Rate',            '%',      'tinggi', 'Proses'),
        ('Procurement Lead Time',                 'hari',   'rendah', 'Proses'),
        ('Turnover Rate Karyawan',                '%',      'rendah', 'SDM'),
        ('Time-to-Fill (Rekrutmen)',              'hari',   'rendah', 'SDM'),
        ('Employee Engagement Score',             '%',      'tinggi', 'SDM'),
        ('Training Hours per Employee',           'jam',    'tinggi', 'SDM'),
        ('Headcount vs Budget',                   '%',      'tinggi', 'SDM'),
        ('Payroll Accuracy Rate',                 '%',      'tinggi', 'SDM'),
        ('IT System Uptime',                      '%',      'tinggi', 'Infrastruktur'),
        ('Tiket IT Terselesaikan',                '%',      'tinggi', 'Infrastruktur'),
        ('Jumlah Proyek Selesai Tepat Waktu',     'unit',   'tinggi', 'Proses'),
        ('Jumlah Inovasi / Improvement Submitted','unit',   'tinggi', 'Inovasi'),
    ]

    targets = pilih_companies('Seed KPI template untuk company')
    if not targets:
        return

    info(f'Akan insert {len(KPI_PRESET)} KPI template.')
    if not confirm('Lanjutkan?'):
        warn('Dibatalkan.'); return

    created = skipped = 0
    for company in targets:
        for nama, satuan, arah, kategori in KPI_PRESET:
            _, is_new = KPITemplate.objects.get_or_create(
                company=company, nama=nama,
                defaults={'satuan': satuan, 'arah': arah, 'kategori': kategori, 'aktif': True}
            )
            if is_new: created += 1
            else:      skipped += 1

    ok(f'{created} KPI template berhasil dibuat, {skipped} sudah ada.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED PERIODE PENILAIAN (Performance)
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_periode_penilaian():
    header('SEED PERIODE PENILAIAN')
    from apps.performance.models import PeriodePenilaian
    from datetime import date

    targets = pilih_companies('Seed periode penilaian untuk company')
    if not targets:
        return

    tahun_sekarang = date.today().year
    PERIODE_PRESET = [
        # (nama, tipe, mulai, selesai, status)
        (f'Tahunan {tahun_sekarang}',        'Tahunan',    date(tahun_sekarang, 1, 1),  date(tahun_sekarang, 12, 31), 'aktif'),
        (f'Tahunan {tahun_sekarang-1}',      'Tahunan',    date(tahun_sekarang-1, 1, 1),date(tahun_sekarang-1, 12, 31),'tutup'),
        (f'Q1 {tahun_sekarang}',             'Triwulan',   date(tahun_sekarang, 1, 1),  date(tahun_sekarang, 3, 31),  'tutup'),
        (f'Q2 {tahun_sekarang}',             'Triwulan',   date(tahun_sekarang, 4, 1),  date(tahun_sekarang, 6, 30),  'tutup'),
        (f'Q3 {tahun_sekarang}',             'Triwulan',   date(tahun_sekarang, 7, 1),  date(tahun_sekarang, 9, 30),  'aktif'),
        (f'Q4 {tahun_sekarang}',             'Triwulan',   date(tahun_sekarang, 10, 1), date(tahun_sekarang, 12, 31), 'draft'),
        (f'Semester 1 {tahun_sekarang}',     'Semesteran', date(tahun_sekarang, 1, 1),  date(tahun_sekarang, 6, 30),  'tutup'),
        (f'Semester 2 {tahun_sekarang}',     'Semesteran', date(tahun_sekarang, 7, 1),  date(tahun_sekarang, 12, 31), 'aktif'),
    ]

    created = skipped = 0
    for company in targets:
        for nama, tipe, mulai, selesai, status in PERIODE_PRESET:
            _, is_new = PeriodePenilaian.objects.get_or_create(
                company=company, nama=nama,
                defaults={'tipe': tipe, 'tanggal_mulai': mulai,
                          'tanggal_selesai': selesai, 'status': status}
            )
            if is_new: created += 1
            else:      skipped += 1

    ok(f'{created} periode penilaian berhasil dibuat, {skipped} sudah ada.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED SOAL PSIKOTES (SoalBank)
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_soal_psikotes():
    header('SEED SOAL PSIKOTES (SoalBank)')
    from apps.psychotest.models import SoalBank

    existing = SoalBank.objects.count()
    if existing > 0:
        warn(f'SoalBank sudah ada {existing} soal.')
        if not confirm('Tambah soal preset di atas yang sudah ada?'):
            warn('Dibatalkan.'); return

    SOAL_LOGIKA = [
        ('Jika A > B dan B > C, maka...', 'A > C', 'A < C', 'A = C', 'Tidak bisa ditentukan', 'A', 'mudah'),
        ('Semua kucing adalah hewan. Pus adalah kucing. Maka Pus adalah...', 'Hewan', 'Bukan hewan', 'Mungkin hewan', 'Tidak diketahui', 'A', 'mudah'),
        ('5, 10, 20, 40, ?', '60', '70', '80', '100', 'C', 'mudah'),
        ('Jika hari ini Senin, 3 hari lagi adalah...', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'B', 'mudah'),
        ('Angka ganjil dari: 2, 4, 7, 8, 10 adalah...', '2', '4', '7', '8', 'C', 'mudah'),
        ('1, 4, 9, 16, 25, ?', '30', '36', '40', '49', 'B', 'mudah'),
        ('Jika merah = 1, biru = 2, hijau = 3, maka 1+3 = ?', 'Merah+Biru', 'Merah+Hijau', 'Biru+Hijau', 'Biru+Biru', 'B', 'sedang'),
        ('3, 6, 12, 24, ?', '36', '42', '48', '60', 'C', 'mudah'),
    ]
    SOAL_VERBAL = [
        ('Antonim dari RAJIN adalah...', 'Pintar', 'Malas', 'Cerdas', 'Aktif', 'B', 'mudah'),
        ('Sinonim dari BIJAK adalah...', 'Bodoh', 'Arif', 'Kaya', 'Tua', 'B', 'mudah'),
        ('DOKTER : RUMAH SAKIT = GURU : ?', 'Kantor', 'Pabrik', 'Sekolah', 'Toko', 'C', 'mudah'),
        ('Kata yang tepat untuk melengkapi: "Dia ... keras untuk meraih impiannya."', 'bermain', 'bekerja', 'berlari', 'bernyanyi', 'B', 'mudah'),
        ('Antonim dari OPTIMIS adalah...', 'Realistis', 'Idealis', 'Pesimis', 'Pragmatis', 'C', 'mudah'),
        ('Manakah ejaan yang benar?', 'Praktek', 'Praktik', 'Praktic', 'Practik', 'B', 'mudah'),
        ('Sinonim KOMPETEN adalah...', 'Lemah', 'Mampu', 'Gagal', 'Baru', 'B', 'mudah'),
        ('BUKU : PERPUSTAKAAN = UANG : ?', 'Bank', 'Toko', 'Sekolah', 'Rumah', 'A', 'mudah'),
    ]
    SOAL_NUMERIK = [
        ('Berapakah 15% dari 200?', '25', '30', '35', '40', 'B', 'mudah'),
        ('Jika harga barang Rp80.000 didiskon 25%, harga akhir adalah...', 'Rp55.000', 'Rp60.000', 'Rp65.000', 'Rp70.000', 'B', 'mudah'),
        ('Rata-rata dari 4, 8, 12, 16 adalah...', '8', '10', '12', '14', 'B', 'mudah'),
        ('Jika 3x = 21, maka x = ?', '5', '6', '7', '8', 'C', 'mudah'),
        ('Sebuah mobil menempuh 120 km dalam 2 jam. Kecepatannya adalah...', '40 km/jam', '50 km/jam', '60 km/jam', '70 km/jam', 'C', 'mudah'),
        ('Berapakah 2^10?', '512', '1024', '2048', '256', 'B', 'sedang'),
        ('25 + 17 × 2 - 10 = ?', '49', '74', '59', '64', 'C', 'sedang'),
        ('Jika A = 5 dan B = 3, berapa A² - B²?', '16', '25', '34', '10', 'A', 'sedang'),
    ]

    bulk = []
    for soal_list, kategori in [(SOAL_LOGIKA,'logika'),(SOAL_VERBAL,'verbal'),(SOAL_NUMERIK,'numerik')]:
        for pertanyaan, a, b, c, d, jwb, tingkat in soal_list:
            if not SoalBank.objects.filter(pertanyaan=pertanyaan).exists():
                bulk.append(SoalBank(
                    kategori=kategori, tipe='pilihan_ganda',
                    pertanyaan=pertanyaan, opsi_a=a, opsi_b=b, opsi_c=c, opsi_d=d,
                    jawaban_benar=jwb,
                ))

    if bulk:
        SoalBank.objects.bulk_create(bulk, ignore_conflicts=True)
        ok(f'{len(bulk)} soal psikotes berhasil dibuat.')
    else:
        warn('Semua soal sudah ada.')

    info('Soal DISC & Kraepelin: generate otomatis via utils/psychotest_seed.py')
    info('Soal Advanced (OCEAN/Raven): jalankan: python manage.py seed_advanced_soal')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED KOMPETENSI OD
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_kompetensi_od():
    header('SEED KOMPETENSI OD (Organizational Development)')
    from apps.od.models import CompetencyCategory, Competency

    KOMPETENSI_PRESET = {
        'Behavioral': [
            ('BEH-01', 'Komunikasi', 'Kemampuan menyampaikan informasi secara jelas dan efektif',
             'Hanya menyampaikan informasi dasar',
             'Menyampaikan informasi dengan jelas kepada rekan kerja',
             'Berkomunikasi efektif di berbagai situasi dan audiens',
             'Menjadi komunikator kunci dalam tim dan lintas divisi',
             'Memimpin komunikasi strategis organisasi'),
            ('BEH-02', 'Kerjasama Tim', 'Kemampuan bekerja efektif dalam tim',
             'Berpartisipasi jika diminta',
             'Aktif berkontribusi dalam tim',
             'Memfasilitasi kolaborasi antar anggota tim',
             'Membangun sinergi tim lintas departemen',
             'Memimpin budaya kolaborasi organisasi'),
            ('BEH-03', 'Inisiatif', 'Kemampuan bertindak proaktif tanpa diarahkan',
             'Bertindak jika ada instruksi jelas',
             'Menyelesaikan tugas lebih dari yang diminta',
             'Mengidentifikasi dan menyelesaikan masalah sebelum terjadi',
             'Menginisiasi improvement proses secara konsisten',
             'Memimpin transformasi budaya inovasi'),
            ('BEH-04', 'Disiplin & Integritas', 'Komitmen terhadap aturan dan kejujuran',
             'Memenuhi kewajiban minimum',
             'Konsisten mengikuti aturan dan prosedur',
             'Menjadi role model disiplin di lingkungan kerja',
             'Membangun budaya integritas di tim',
             'Menjaga integritas organisasi di seluruh lini'),
            ('BEH-05', 'Adaptabilitas', 'Kemampuan menyesuaikan diri dengan perubahan',
             'Menerima perubahan jika dipaksa',
             'Beradaptasi dengan perubahan setelah waktu penyesuaian',
             'Beradaptasi cepat dan membantu orang lain beradaptasi',
             'Memimpin perubahan dan mengelola resistensi',
             'Mendesain organisasi yang agile dan adaptif'),
        ],
        'Technical': [
            ('TECH-01', 'Keahlian Teknis Bidang', 'Penguasaan kompetensi teknis sesuai bidang kerja',
             'Pengetahuan teknis dasar',
             'Mampu melaksanakan tugas teknis standar',
             'Mampu menyelesaikan masalah teknis kompleks',
             'Menjadi referensi teknis di departemen',
             'Ahli teknis (subject matter expert) level organisasi'),
            ('TECH-02', 'Penggunaan Teknologi & Sistem', 'Kemampuan memanfaatkan tools dan sistem digital',
             'Menggunakan aplikasi dasar (email, Ms. Office)',
             'Menggunakan sistem ERP/HRIS dasar',
             'Memanfaatkan teknologi untuk meningkatkan produktivitas',
             'Mengintegrasikan sistem dan mengotomasi proses',
             'Merancang solusi teknologi organisasi'),
            ('TECH-03', 'Analisis Data & Pelaporan', 'Kemampuan menganalisis data dan membuat laporan',
             'Membuat laporan sederhana dari data yang tersedia',
             'Menganalisis data dan membuat insight dasar',
             'Membuat analisis mendalam dan rekomendasi berbasis data',
             'Merancang sistem pelaporan dan dashboard',
             'Memimpin strategi data-driven decision making'),
        ],
        'Leadership': [
            ('LDR-01', 'Pengambilan Keputusan', 'Kemampuan membuat keputusan tepat dan tepat waktu',
             'Membuat keputusan rutin dengan panduan',
             'Membuat keputusan operasional secara mandiri',
             'Membuat keputusan taktis dengan mempertimbangkan risiko',
             'Membuat keputusan strategis departemen',
             'Membuat keputusan strategis organisasi'),
            ('LDR-02', 'Pengembangan Bawahan', 'Kemampuan mengembangkan kompetensi anggota tim',
             'Memberikan feedback jika diminta',
             'Aktif memberikan coaching dan feedback',
             'Merancang program pengembangan individu',
             'Membangun talent pipeline departemen',
             'Memimpin talent management organisasi'),
            ('LDR-03', 'Perencanaan & Organisasi', 'Kemampuan merencanakan dan mengorganisir sumber daya',
             'Merencanakan pekerjaan harian',
             'Merencanakan dan mengorganisir pekerjaan tim',
             'Merancang rencana kerja departemen',
             'Merancang strategi dan roadmap jangka menengah',
             'Merancang strategi jangka panjang organisasi'),
        ],
    }

    targets = pilih_companies('Seed kompetensi untuk company')
    if not targets:
        return

    total_cat = total_comp = 0
    for company in targets:
        warna_map = {
            'Behavioral':  '#2563eb',
            'Technical':   '#059669',
            'Leadership':  '#dc2626',
        }
        for urutan, (cat_nama, komps) in enumerate(KOMPETENSI_PRESET.items()):
            cat, is_new = CompetencyCategory.objects.get_or_create(
                company=company, nama=cat_nama,
                defaults={'warna': warna_map.get(cat_nama, '#64748b'), 'urutan': urutan, 'aktif': True}
            )
            if is_new: total_cat += 1

            for kode, nama, deskripsi, l1, l2, l3, l4, l5 in komps:
                _, is_new = Competency.objects.get_or_create(
                    company=company, kode=kode,
                    defaults={
                        'kategori': cat, 'nama': nama, 'deskripsi': deskripsi,
                        'level_1_desc': l1, 'level_2_desc': l2, 'level_3_desc': l3,
                        'level_4_desc': l4, 'level_5_desc': l5, 'aktif': True,
                    }
                )
                if is_new: total_comp += 1

    ok(f'{total_cat} kategori + {total_comp} kompetensi berhasil dibuat.')
    info('Lanjutkan: OD → Position Competency untuk assign ke jabatan')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED JOB SITE & POINT OF HIRE
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_jobsite():
    header('SEED JOB SITE & POINT OF HIRE')
    from apps.employees.models import JobSite, PointOfHire

    targets = pilih_companies('Seed job site untuk company')
    if not targets:
        return

    JOBSITE_PRESET = [
        ('Head Office', 'HO', 'Jakarta Selatan, DKI Jakarta'),
        ('Site A', 'SITE-A', 'Kalimantan Timur'),
        ('Site B', 'SITE-B', 'Kalimantan Selatan'),
        ('Workshop', 'WS', 'Balikpapan, Kalimantan Timur'),
        ('Camp Area', 'CAMP', 'Kutai Kartanegara, Kalimantan Timur'),
    ]
    POH_PRESET = [
        'Jakarta', 'Surabaya', 'Balikpapan', 'Samarinda', 'Banjarmasin',
        'Makassar', 'Medan', 'Semarang', 'Bandung', 'Palembang',
    ]

    created_js = created_poh = skipped_js = skipped_poh = 0
    for company in targets:
        for nama, kode, lokasi in JOBSITE_PRESET:
            _, is_new = JobSite.objects.get_or_create(
                company=company, kode=kode,
                defaults={'nama': nama, 'lokasi': lokasi, 'aktif': True}
            )
            if is_new: created_js += 1
            else:      skipped_js += 1

    for nama_poh in POH_PRESET:
        _, is_new = PointOfHire.objects.get_or_create(nama=nama_poh)
        if is_new: created_poh += 1
        else:      skipped_poh += 1

    ok(f'{created_js} job site, {created_poh} point of hire berhasil dibuat.')
    if skipped_js or skipped_poh:
        warn(f'{skipped_js} job site + {skipped_poh} POH sudah ada (skip).')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED OFFERING TEMPLATE (Recruitment)
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_offering_template():
    header('SEED OFFERING TEMPLATE (Recruitment)')
    from apps.recruitment.models import OfferingTemplate, CompanySetting

    if OfferingTemplate.objects.exists():
        warn(f'Sudah ada {OfferingTemplate.objects.count()} template.')
        if not confirm('Tetap buat template default baru?'):
            warn('Dibatalkan.'); return

    OfferingTemplate.objects.get_or_create(
        nama='Standard PKWT Mining',
        defaults={
            'is_default': True,
            'deskripsi': 'Template standar untuk karyawan PKWT di site pertambangan',
            'working_day_text': 'Roster Working Day, every day working including National Holiday/Red Calendar day, able to take Rest one day after two weeks work at Site, 07.30 – 16.00 (base on field working time)',
            'employment_status_text': 'First Contract (PKWT I) : 6 (Six) months, If your evaluation is good/excellent, company will be consider to extend your working agreement to (PKWT II)',
            'meal_allowance_text': 'Provided by Company (breakfast, lunch, & dinner)',
            'residence_allowance_text': 'Provided by Company (mess/dormitory)',
            'roster_leave_text': '10 : 2 (working 10 weeks)',
            'annual_leave_text': '12 months work continually, 12 working days Leave',
            'overtime_text': 'Job Position Assignment Responsibility',
            'bpjs_kes_text': 'Health Care (Employee dues obligation by regulation)',
            'bpjs_tk_text': 'JHT,JKK,JK,JP (JHT&JP; Employee dues obligation by regulation)',
            'bpjs_potongan_text': 'Deducted 2% JHT, 1% JP, 1% Kes From Salary for BPJS TK & Kes.',
            'pph21_text': 'Income Tax is covered by Company',
            'footer_text': 'The mentioned statement above as our agreement previous, so please sign the letter and submit the letter back to us as your acceptance to the term & condition in the agreement as soon as possible.\n\nThanks you for your attention and cooperation.',
        }
    )
    OfferingTemplate.objects.get_or_create(
        nama='Standard PKWTT Office',
        defaults={
            'is_default': False,
            'deskripsi': 'Template standar untuk karyawan tetap (PKWTT) di kantor',
            'working_day_text': 'Monday to Friday, 08.00 – 17.00 WIB (1 hour break)',
            'employment_status_text': 'Permanent Employee (PKWTT) effective from joining date',
            'meal_allowance_text': 'Meal allowance included in salary package',
            'residence_allowance_text': 'Not provided',
            'roster_leave_text': 'Monday – Friday (5 working days)',
            'annual_leave_text': 'After 12 months of continuous employment, 12 working days per year',
            'overtime_text': 'Based on Government Regulation No. 36/2021',
            'bpjs_kes_text': 'BPJS Kesehatan — Employee contribution 1%, Company 4%',
            'bpjs_tk_text': 'JHT 3.7% (company) + 2% (employee); JKK, JK by company; JP 2% (company) + 1% (employee)',
            'bpjs_potongan_text': 'Deducted from salary as per BPJS regulation',
            'pph21_text': 'Income Tax (PPh 21) deducted from salary as per applicable tax regulation',
            'footer_text': 'We look forward to your positive response. Please sign and return this letter as your acceptance.\n\nThank you.',
        }
    )

    # Seed CompanySetting jika belum ada
    CompanySetting.objects.get_or_create(pk=1, defaults={
        'nama_perusahaan': 'PT. Nama Perusahaan',
        'hrd_manager': 'HRD Manager',
        'format_nomor_ol': 'OL/{YYYY}{MM}/{SEQ:04d}',
    })

    ok('2 offering template + company setting berhasil dibuat.')


# ══════════════════════════════════════════════════════════════════════════════
#  MENU — SEED SITE ALLOWANCE RULE (Payroll)
# ══════════════════════════════════════════════════════════════════════════════

def menu_seed_site_allowance():
    header('SEED SITE ALLOWANCE RULE')
    from apps.payroll.models import SiteAllowanceRule
    from apps.employees.models import JobSite

    targets = pilih_companies('Seed site allowance untuk company')
    if not targets:
        return

    created = skipped = 0
    for company in targets:
        sites = JobSite.objects.filter(company=company, aktif=True)
        if not sites.exists():
            warn(f'{company.nama}: belum ada job site. Jalankan seed job site dulu.')
            continue

        for site in sites:
            # Tunjangan site flat per site
            tunjangan_flat = 2_000_000 if 'HO' in site.kode else 5_000_000
            _, is_new = SiteAllowanceRule.objects.get_or_create(
                company=company, job_site=site, jabatan=None,
                nama_komponen='Tunjangan Site',
                defaults={'nilai': tunjangan_flat, 'jenis': 'flat', 'aktif': True}
            )
            if is_new: created += 1
            else:      skipped += 1

    ok(f'{created} site allowance rule berhasil dibuat, {skipped} sudah ada.')


def menu_seed_lengkap():
    header('SEED LENGKAP — ALL IN ONE')
    info('Jalankan semua seed secara berurutan untuk test menyeluruh.')
    info('Urutan: Company → Dept → Jabatan Preset → Sync → Dummy Karyawan → Absensi → Salary → Kontrak → Kandidat → Profil Kandidat → Asset')
    print()
    if not confirm('Lanjutkan seed lengkap? (akan masuk ke setiap menu secara berurutan)'):
        warn('Dibatalkan.'); return

    steps = [
        ('Company',               menu_tambah_company),
        ('Department',            menu_tambah_department),
        ('Jabatan Preset',        menu_jabatan_preset),
        ('Sync Dept→Jabatan',     menu_sync_department_jabatan),
        ('Job Site & POH',        menu_seed_jobsite),
        ('Shift Kerja',           menu_seed_shift),
        ('Karyawan Dummy',        menu_generate_dummy_karyawan),
        ('Absensi',               menu_generate_absensi),
        ('Salary Benefit',        menu_seed_salary_benefit),
        ('Site Allowance Rule',   menu_seed_site_allowance),
        ('Kontrak',               menu_seed_kontrak),
        ('KPI Template',          menu_seed_kpi_template),
        ('Periode Penilaian',     menu_seed_periode_penilaian),
        ('Kompetensi OD',         menu_seed_kompetensi_od),
        ('Soal Psikotes',         menu_seed_soal_psikotes),
        ('Offering Template',     menu_seed_offering_template),
        ('Kandidat',              menu_seed_kandidat),
        ('Profil Kandidat',       menu_seed_candidate_profile),
        ('Asset',                 menu_seed_asset),
    ]
    for label, fn in steps:
        print(f'\n{B}══ STEP: {label} ══{RST}')
        try:
            fn()
        except Exception as e:
            err(f'Step "{label}" error: {e}')
            if not confirm('Lanjut ke step berikutnya?'):
                break
    ok('Seed lengkap selesai!')


def main_menu():
    while True:
        header('i-Kira — Seed Data')

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
            'Tambah Department (manual)',
            'Tambah Department & Jabatan Preset (Industri)',
            'Tambah Jabatan (manual)',
            'Tambah Jabatan Preset (114 jabatan industri)',
            'Sync Department ke Jabatan',
            'Generate Karyawan Dummy',
            'Generate Absensi',
            'Seed Salary Benefit (Upah & Tunjangan)',
            'Seed Kandidat Rekrutmen',
            'Seed Profil Lengkap Kandidat',
            'Seed Kontrak Karyawan',
            'Seed Asset Management',
            '─── Add-On & Master Data ───',
            'Seed Shift Kerja',
            'Seed KPI Template (Performance)',
            'Seed Periode Penilaian (Performance)',
            'Seed Soal Psikotes (SoalBank)',
            'Seed Kompetensi OD',
            'Seed Job Site & Point of Hire',
            'Seed Offering Template (Recruitment)',
            'Seed Site Allowance Rule (Payroll)',
            '─── ─────────────────────── ───',
            'Lihat semua data',
            'SEED LENGKAP (All-in-One)',
            'Keluar',
        ], title='Menu')

        if   menu == 0:  menu_tambah_company()
        elif menu == 1:  menu_tambah_department()
        elif menu == 2:  menu_department_preset()
        elif menu == 3:  menu_tambah_jabatan()
        elif menu == 4:  menu_jabatan_preset()
        elif menu == 5:  menu_sync_department_jabatan()
        elif menu == 6:  menu_generate_dummy_karyawan()
        elif menu == 7:  menu_generate_absensi()
        elif menu == 8:  menu_seed_salary_benefit()
        elif menu == 9:  menu_seed_kandidat()
        elif menu == 10: menu_seed_candidate_profile()
        elif menu == 11: menu_seed_kontrak()
        elif menu == 12: menu_seed_asset()
        elif menu == 13: pass  # separator
        elif menu == 14: menu_seed_shift()
        elif menu == 16: menu_seed_kpi_template()
        elif menu == 17: menu_seed_periode_penilaian()
        elif menu == 18: menu_seed_soal_psikotes()
        elif menu == 19: menu_seed_kompetensi_od()
        elif menu == 20: menu_seed_jobsite()
        elif menu == 21: menu_seed_offering_template()
        elif menu == 23: menu_seed_site_allowance()
        elif menu == 24: pass  # separator
        elif menu == 25: menu_lihat_data()
        elif menu == 26: menu_seed_lengkap()
        elif menu == 27:
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
    parser = argparse.ArgumentParser(description='i-Kira — Seed Data')
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
    parser.add_argument('--dept-preset',  action='store_true', help='Preset department & jabatan per industri')
    parser.add_argument('--salary',     action='store_true', help='Seed salary benefit karyawan')
    parser.add_argument('--profil-kandidat', action='store_true', help='Seed profil lengkap kandidat')
    parser.add_argument('--seed-all',        action='store_true', help='Seed lengkap all-in-one')
    parser.add_argument('--shift',            action='store_true', help='Seed shift kerja')
    parser.add_argument('--kpi-template',     action='store_true', help='Seed KPI template performance')
    parser.add_argument('--periode-penilaian',action='store_true', help='Seed periode penilaian')
    parser.add_argument('--soal-psikotes',    action='store_true', help='Seed soal bank psikotes')
    parser.add_argument('--kompetensi',       action='store_true', help='Seed kompetensi OD')
    parser.add_argument('--jobsite',          action='store_true', help='Seed job site & point of hire')
    parser.add_argument('--offering-template',action='store_true', help='Seed offering template rekrutmen')
    parser.add_argument('--site-allowance',   action='store_true', help='Seed site allowance rule payroll')
    args = parser.parse_args()

    try:
        if   args.company:    menu_tambah_company()
        elif args.department: menu_tambah_department()
        elif getattr(args, 'dept_preset', False): menu_department_preset()
        elif args.jabatan:    menu_tambah_jabatan()
        elif args.preset:     menu_jabatan_preset()
        elif getattr(args, 'sync_dept', False): menu_sync_department_jabatan()
        elif args.dummy:      menu_generate_dummy_karyawan()
        elif args.absensi:    menu_generate_absensi()
        elif args.salary:     menu_seed_salary_benefit()
        elif args.kandidat:   menu_seed_kandidat()
        elif getattr(args, 'profil_kandidat', False): menu_seed_candidate_profile()
        elif args.kontrak:    menu_seed_kontrak()
        elif args.asset:      menu_seed_asset()
        elif args.shift:      menu_seed_shift()
        elif getattr(args, 'kpi_template', False):    menu_seed_kpi_template()
        elif getattr(args, 'periode_penilaian', False): menu_seed_periode_penilaian()
        elif getattr(args, 'soal_psikotes', False):   menu_seed_soal_psikotes()
        elif args.kompetensi: menu_seed_kompetensi_od()
        elif args.jobsite:    menu_seed_jobsite()
        elif getattr(args, 'offering_template', False): menu_seed_offering_template()
        elif getattr(args, 'site_allowance', False):  menu_seed_site_allowance()
        elif getattr(args, 'seed_all', False): menu_seed_lengkap()
        elif args.list:       menu_lihat_data()
        else:                 main_menu()
    except KeyboardInterrupt:
        print(f'\n\n{Y}  Dibatalkan.{RST}\n')